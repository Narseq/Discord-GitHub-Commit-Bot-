"""Bot Discord: sprawdzanie GitHuba i wysyłanie powiadomień."""

import asyncio
from datetime import datetime

import aiohttp
import discord

from .config import GITHUB_TOKEN, TOKEN, log
from .messages import msg
from .storage import db, get_setting
from .web import start_web


class Githubek(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.http_session = None
        self.poll_task = None
        self.poll_lock = asyncio.Lock()
        self.web_runner = None

    async def setup_hook(self):
        self.http_session = aiohttp.ClientSession()
        self.poll_task = asyncio.create_task(self.poll_loop())
        await self.start_web()

    async def close(self):
        if self.poll_task:
            self.poll_task.cancel()
        if self.web_runner:
            await self.web_runner.cleanup()
        if self.http_session:
            await self.http_session.close()
        await super().close()

    async def on_ready(self):
        log.info("Zalogowano jako %s", self.user)

    # -------------------------------------------------------------- polling

    async def poll_loop(self):
        await self.wait_until_ready()
        while True:
            try:
                await self.check_all()
            except Exception:
                log.exception("Błąd w pętli sprawdzania")
            try:
                minutes = max(1, int(get_setting("interval")))
            except ValueError:
                minutes = 15
            await asyncio.sleep(minutes * 60)

    async def check_all(self):
        async with self.poll_lock:
            for row in db.execute("SELECT * FROM repos WHERE enabled=1").fetchall():
                await self.check_repo(row["id"])
                await asyncio.sleep(1)

    async def gh_get(self, path, params, etag):
        headers = {"Accept": "application/vnd.github+json", "User-Agent": "githubek-bot"}
        if GITHUB_TOKEN:
            headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
        if etag:
            headers["If-None-Match"] = etag
        async with self.http_session.get(
            f"https://api.github.com{path}", params=params, headers=headers, timeout=aiohttp.ClientTimeout(total=20)
        ) as resp:
            if resp.status == 304:
                return 304, None, etag
            if resp.status == 404 and path.endswith("/releases/latest"):
                return 404, None, ""
            if resp.status >= 400:
                body = (await resp.text())[:200]
                raise RuntimeError(f"GitHub {resp.status}: {body}")
            return resp.status, await resp.json(), resp.headers.get("ETag", "")

    async def check_repo(self, repo_id):
        row = db.execute("SELECT * FROM repos WHERE id=?", (repo_id,)).fetchone()
        if not row:
            return
        error = ""
        try:
            if row["watch_commits"]:
                await self.check_commits(row)
            if row["watch_releases"]:
                await self.check_releases(row)
        except Exception as exc:
            log.warning("%s: %s", row["repo"], exc)
            error = str(exc)[:300]
        db.execute(
            "UPDATE repos SET last_check=?, last_error=? WHERE id=?",
            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), error, repo_id),
        )
        db.commit()

    async def check_commits(self, row):
        params = {"per_page": 10}
        if row["branch"]:
            params["sha"] = row["branch"]
        status, commits, etag = await self.gh_get(f"/repos/{row['repo']}/commits", params, row["etag_commits"])
        if status == 304 or not commits:
            return
        newest = commits[0]["sha"]
        if row["last_sha"] and row["last_sha"] != newest:
            new = []
            for commit in commits:
                if commit["sha"] == row["last_sha"]:
                    break
                new.append(commit)
            await self.notify_commits(row, new)
        db.execute(
            "UPDATE repos SET last_sha=?, etag_commits=? WHERE id=?", (newest, etag, row["id"])
        )
        db.commit()

    async def check_releases(self, row):
        status, release, etag = await self.gh_get(
            f"/repos/{row['repo']}/releases/latest", None, row["etag_releases"]
        )
        if status == 304:
            return
        release_id = str(release["id"]) if release else ""
        if release and row["last_release"] and row["last_release"] != release_id:
            await self.notify_release(row, release)
        db.execute(
            "UPDATE repos SET last_release=?, etag_releases=? WHERE id=?",
            (release_id or row["last_release"], etag, row["id"]),
        )
        db.commit()

    # -------------------------------------------------------- notifications

    def targets(self, row):
        channel_id = row["channel_id"] or get_setting("channel_id")
        users = [u for u in (row["users"] + "," + get_setting("users")).split(",") if u]
        roles = [r for r in (row["roles"] + "," + get_setting("roles")).split(",") if r]
        users, roles = list(dict.fromkeys(users)), list(dict.fromkeys(roles))
        mentions = " ".join([f"<@&{r}>" for r in roles] + [f"<@{u}>" for u in users])
        return channel_id, mentions

    async def send(self, row, embed, kind, summary):
        channel_id, mentions = self.targets(row)
        if not channel_id:
            raise RuntimeError("Nie ustawiono kanału (ani globalnego, ani dla repo)")
        channel = self.get_channel(int(channel_id)) or await self.fetch_channel(int(channel_id))
        await channel.send(
            content=mentions or None,
            embed=embed,
            allowed_mentions=discord.AllowedMentions(users=True, roles=True, everyone=False),
        )
        db.execute(
            "INSERT INTO events(ts, repo, kind, title) VALUES(?, ?, ?, ?)",
            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), row["repo"], kind, summary),
        )
        db.commit()

    async def notify_commits(self, row, commits):
        lines = []
        for commit in commits[:8]:
            message = commit["commit"]["message"].split("\n")[0][:90]
            author = (commit.get("author") or {}).get("login") or commit["commit"]["author"]["name"]
            lines.append(f"[`{commit['sha'][:7]}`]({commit['html_url']}) {message} — **{author}**")
        if len(commits) > 8:
            lines.append(msg("more", n=len(commits) - 8))
        count = len(commits)
        branch = f" ({row['branch']})" if row["branch"] else ""
        embed = discord.Embed(
            title=f"{row['repo']}{branch}: {count} {msg('commit_one' if count == 1 else 'commit_many')}",
            url=f"https://github.com/{row['repo']}/commits/{row['branch']}".rstrip("/"),
            description="\n".join(lines),
            color=0x2EA043,
            timestamp=datetime.now().astimezone(),
        )
        # w historii panelu zapisujemy zawsze polski opis (panel sam go tłumaczy)
        await self.send(row, embed, "commit", f"{count} {'nowy commit' if count == 1 else 'nowe commity'}")

    async def notify_release(self, row, release):
        name = release.get("name") or release["tag_name"]
        embed = discord.Embed(
            title=f"{row['repo']}: {msg('release', tag=release['tag_name'])}",
            url=release["html_url"],
            description=(release.get("body") or "")[:1000] or None,
            color=0x1F6FEB,
            timestamp=datetime.now().astimezone(),
        )
        embed.add_field(name=msg("release_field"), value=name, inline=True)
        if release.get("prerelease"):
            embed.add_field(name=msg("type_field"), value=msg("prerelease"), inline=True)
        await self.send(row, embed, "release", f"nowa wersja {release['tag_name']}")

    async def send_test(self, row):
        embed = discord.Embed(
            title=msg("test_title", repo=row["repo"]),
            description=msg("test_desc"),
            color=0x8957E5,
        )
        await self.send(row, embed, "test", "Wiadomość testowa")

    # ------------------------------------------------------------ web panel

    async def start_web(self):
        self.web_runner = await start_web(self)


def main():
    if not TOKEN:
        raise SystemExit("Ustaw DISCORD_TOKEN w pliku .env")
    Githubek().run(TOKEN, log_handler=None)
