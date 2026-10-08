"""Akcje panelu (POST): logowanie, ustawienia, repozytoria, konta."""

import asyncio
import sqlite3
import time

import pymysql
from aiohttp import web

from ..accounts import (
    LOGIN_FAILS,
    hash_password,
    login_locked,
    q,
    session_cookie,
    verify_password,
)
from ..config import SESSION_DAYS, USERNAME_RE
from ..storage import db, parse_ids, parse_repo, set_setting
from .ui import redirect


async def login_post(request):
    ip = request.remote or "?"
    if login_locked(ip):
        raise web.HTTPFound("/login?e=2")
    data = await request.post()
    user = await q("SELECT * FROM panel_users WHERE username=%s", (data.get("username", "").strip(),), mode="one")
    if user and verify_password(data.get("password", ""), user["password_hash"]):
        resp = web.HTTPFound("/")
        resp.set_cookie(
            "session", session_cookie(user), httponly=True, samesite="Strict", max_age=SESSION_DAYS * 86400
        )
        raise resp
    LOGIN_FAILS.setdefault(ip, []).append(time.time())
    await asyncio.sleep(1)
    raise web.HTTPFound("/login?e=1")


async def logout(request):
    resp = web.HTTPFound("/login")
    resp.del_cookie("session")
    raise resp


async def save_settings(request):
    data = await request.post()
    interval = data.get("interval", "15").strip()
    set_setting("interval", interval if interval.isdigit() and int(interval) >= 1 else "15")
    set_setting("channel_id", parse_ids(data.get("channel_id"))[:20])
    set_setting("users", parse_ids(data.get("users")))
    set_setting("roles", parse_ids(data.get("roles")))
    set_setting("message_lang", "en" if data.get("message_lang") == "en" else "pl")
    redirect("Zapisano ustawienia", "/settings")


async def repo_add(request):
    data = await request.post()
    repo = parse_repo(data.get("repo"))
    if not repo:
        redirect("Nieprawidłowy link/nazwa repo", "/repos")
    try:
        db.execute("INSERT INTO repos(repo) VALUES(?)", (repo,))
        db.commit()
    except sqlite3.IntegrityError:
        redirect("To repo już jest dodane", "/repos")
    row = db.execute("SELECT id FROM repos WHERE repo=?", (repo,)).fetchone()
    await request.app["bot"].check_repo(row["id"])  # ustawia punkt odniesienia
    redirect(f"Dodano {repo} — ustaw teraz powiadomienia", f"/repos/{row['id']}")


async def repo_update(request):
    rid = int(request.match_info["id"])
    data = await request.post()
    db.execute(
        """UPDATE repos SET branch=?, channel_id=?, users=?, roles=?, watch_commits=?, watch_releases=?,
           enabled=?, last_sha='', last_release='', etag_commits='', etag_releases='' WHERE id=?""",
        (
            data.get("branch", "").strip(),
            parse_ids(data.get("channel_id"))[:20],
            parse_ids(data.get("users")),
            parse_ids(data.get("roles")),
            int("watch_commits" in data),
            int("watch_releases" in data),
            int("enabled" in data),
            rid,
        ),
    )
    db.commit()
    await request.app["bot"].check_repo(rid)  # nowy punkt odniesienia
    redirect("Zapisano zmiany", f"/repos/{rid}")


async def repo_delete(request):
    db.execute("DELETE FROM repos WHERE id=?", (int(request.match_info["id"]),))
    db.commit()
    redirect("Usunięto repozytorium", "/repos")


async def repo_check(request):
    rid = int(request.match_info["id"])
    bot = request.app["bot"]
    async with bot.poll_lock:
        await bot.check_repo(rid)
    redirect("Sprawdzono", f"/repos/{rid}")


async def repo_test(request):
    rid = int(request.match_info["id"])
    row = db.execute("SELECT * FROM repos WHERE id=?", (rid,)).fetchone()
    try:
        await request.app["bot"].send_test(row)
    except Exception as exc:
        redirect(f"Błąd wysyłania: {exc}", f"/repos/{rid}")
    redirect("Wysłano wiadomość testową", f"/repos/{rid}")


async def check_all_now(request):
    await request.app["bot"].check_all()
    redirect("Sprawdzono wszystkie repozytoria", "/")


async def user_add(request):
    data = await request.post()
    username, password = data.get("username", "").strip(), data.get("password", "")
    if not USERNAME_RE.match(username):
        redirect("Login: 3-32 znaków (litery, cyfry, _ . -)", "/accounts")
    if len(password) < 8:
        redirect("Hasło musi mieć min. 8 znaków", "/accounts")
    try:
        await q("INSERT INTO panel_users(username, password_hash) VALUES(%s, %s)", (username, hash_password(password)), mode=None)
    except pymysql.err.IntegrityError:
        redirect("Taki login już istnieje", "/accounts")
    redirect(f"Dodano konto {username}", "/accounts")


async def user_delete(request):
    uid = int(request.match_info["id"])
    if uid == request["user"]["id"]:
        redirect("Nie możesz usunąć własnego konta", "/accounts")
    await q("DELETE FROM panel_users WHERE id=%s", (uid,), mode=None)
    redirect("Usunięto konto", "/accounts")


async def password_change(request):
    data = await request.post()
    if not verify_password(data.get("current", ""), request["user"]["password_hash"]):
        redirect("Obecne hasło jest nieprawidłowe", "/accounts")
    if len(data.get("new", "")) < 8:
        redirect("Nowe hasło musi mieć min. 8 znaków", "/accounts")
    await q(
        "UPDATE panel_users SET password_hash=%s WHERE id=%s",
        (hash_password(data["new"]), request["user"]["id"]),
        mode=None,
    )
    raise web.HTTPFound("/login")  # zmiana hasła unieważnia sesje


async def set_lang(request):
    nxt = request.query.get("next", "/")
    if not nxt.startswith("/") or nxt.startswith("//") or "\\" in nxt:
        nxt = "/"
    resp = web.HTTPFound(nxt)
    if request.match_info["code"] in ("pl", "en"):
        resp.set_cookie("lang", request.match_info["code"], max_age=365 * 86400, samesite="Lax")
    raise resp
