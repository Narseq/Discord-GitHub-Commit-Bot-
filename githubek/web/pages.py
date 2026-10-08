"""Strony panelu (GET)."""

from ..accounts import q
from ..config import GITHUB_TOKEN
from ..storage import db, get_setting
from .ui import (
    channel_name,
    channel_select,
    checked,
    chips,
    esc,
    hue_of,
    icon,
    labels_for,
    layout,
    page,
    post_button,
    redirect,
    repo_state,
    roles_datalist,
    soft_break,
    time_label,
)


async def index(request):
    rows = db.execute("SELECT * FROM repos").fetchall()
    active = sum(1 for r in rows if r["enabled"])
    errors = sum(1 for r in rows if r["last_error"])
    sent = db.execute(
        "SELECT COUNT(*) c FROM events WHERE kind!='test' AND ts >= datetime('now','localtime','-1 day')"
    ).fetchone()["c"]
    events = db.execute("SELECT * FROM events ORDER BY id DESC LIMIT 10").fetchall()
    warn = ""
    if not get_setting("channel_id"):
        warn = (
            f'<div class="banner">{icon("settings")}<div>Nie ustawiono domyślnego kanału — powiadomienia nie '
            f'będą wysyłane. <a href="/settings">Ustaw kanał</a></div></div>'
        )
    feed = "".join(
        f'<div class="ev"><div class="ic {esc(e["kind"])}">{icon(e["kind"])}</div>'
        f'<div class="tx">{esc(e["title"])}<small>{esc(e["repo"])}</small></div><time>{esc(time_label(e["ts"]))}</time></div>'
        for e in events
    ) or '<div class="empty">Jeszcze nic nie wysłano. Dodaj repozytorium i poczekaj na pierwszy commit.</div>'
    body = f"""{warn}
<div class="tiles">
  <div class="tile"><div class="n">{len(rows)}</div><div class="t">Repozytoria</div></div>
  <div class="tile"><div class="n">{active}</div><div class="t">Aktywne</div></div>
  <div class="tile"><div class="n">{sent}</div><div class="t">Powiadomień (24h)</div></div>
  <div class="tile {'bad' if errors else ''}"><div class="n">{errors}</div><div class="t">Z błędem</div></div>
</div>
<div class="card"><h3>Ostatnia aktywność</h3><div class="desc">Wysłane powiadomienia · sprawdzanie co {esc(get_setting('interval'))} min</div>{feed}</div>"""
    return layout(
        request, "/", "Przegląd", "Co się dzieje z Twoimi repozytoriami.", body,
        actions=post_button("/check-all", "Sprawdź teraz", "sec", "refresh"), wide=True,
    )


async def repos_page(request):
    bot = request.app["bot"]
    rows = db.execute("SELECT * FROM repos ORDER BY repo").fetchall()
    cards = ""
    for r in rows:
        chan = channel_name(bot, r["channel_id"]) or ("własny kanał" if r["channel_id"] else "kanał globalny")
        pings = len([x for x in (r["users"] + "," + r["roles"]).split(",") if x])
        owner, _, name = r["repo"].partition("/")
        tags = ""
        if r["watch_commits"]:
            tags += f'<span class="tag">{icon("commit")}commity</span>'
        if r["watch_releases"]:
            tags += f'<span class="tag">{icon("release")}wersje</span>'
        if r["branch"]:
            tags += f'<span class="tag">{icon("repos")}{esc(r["branch"])}</span>'
        cards += f"""<a class="repocard {'off' if not r['enabled'] else ''}" href="/repos/{r['id']}" style="--h:{hue_of(owner)}">
  <div class="rc-head">
    <span class="rc-av">{esc(owner[:1].upper())}</span>
    <div class="rc-id"><small>{esc(owner)}</small><b>{soft_break(name)}</b></div>
    {repo_state(r)}
  </div>
  <div class="rc-tags">{tags}</div>
  <div class="rc-foot"><span>{esc(chan)}</span><span>dodatkowe pingi: {pings}</span><span>Sprawdzono: {esc(time_label(r['last_check'])) or '—'}</span></div></a>"""
    cards = f'<div class="repos">{cards}</div>' if cards else '<div class="card empty">Brak repozytoriów — dodaj pierwsze powyżej.</div>'
    body = f"""
<form class="card" method="post" action="/repos/add">
  <h3>Dodaj repozytorium</h3><div class="desc">Wklej link do GitHuba albo wpisz owner/nazwa. Bot zapamięta obecny stan i da znać o kolejnych zmianach.</div>
  <div class="inline"><input type="text" name="repo" placeholder="https://github.com/owner/repo" required><button class="btn">{icon('plus')}Dodaj</button></div>
</form>
{cards}"""
    return layout(request, "/repos", "Repozytoria", "Kliknij repozytorium, aby zmienić jego ustawienia.", body, wide=True)


async def repo_page(request):
    bot = request.app["bot"]
    rid = int(request.match_info["id"])
    row = db.execute("SELECT * FROM repos WHERE id=?", (rid,)).fetchone()
    if not row:
        redirect("Nie znaleziono repozytorium", "/repos")
    labels = await labels_for(bot, row["users"], row["roles"])
    error = f'<div class="err">Ostatni błąd: {esc(row["last_error"])}</div>' if row["last_error"] else ""
    body = f"""{error}{roles_datalist(bot)}
<form method="post" action="/repos/{rid}/update">
  <div class="card">
    <h3>Co śledzić</h3><div class="desc">Wybierz, o czym bot ma Cię informować.</div>
    <label class="tg"><div><b>Commity</b><span>Nowe commity na wybranym branchu</span></div><input type="checkbox" name="watch_commits" {checked(row['watch_commits'])}></label>
    <label class="tg"><div><b>Wersje (releases)</b><span>Nowe wydania na GitHubie</span></div><input type="checkbox" name="watch_releases" {checked(row['watch_releases'])}></label>
    <label class="tg"><div><b>Repozytorium włączone</b><span>Wyłącz, aby wstrzymać sprawdzanie</span></div><input type="checkbox" name="enabled" {checked(row['enabled'])}></label>
    <div style="margin-top:14px"><label class="l">Branch</label><input type="text" name="branch" value="{esc(row['branch'])}" placeholder="puste = domyślny branch repozytorium"></div>
  </div>
  <div class="card">
    <h3>Gdzie i kogo powiadomić</h3><div class="desc">Pingi z tej strony dodają się do globalnych z zakładki Ustawienia.</div>
    <div class="grid">
      <div class="full"><label class="l">Kanał</label>{channel_select(bot, 'channel_id', row['channel_id'], '— kanał domyślny z ustawień —')}</div>
      <div class="full"><label class="l">Użytkownicy do pingu</label>{chips('users', row['users'], labels, 'u', 'wklej ID użytkownika i Enter')}
        <div class="hint">ID: w Discordzie włącz Tryb programisty, PPM na użytkowniku → Kopiuj ID.</div></div>
      <div class="full"><label class="l">Role do pingu</label>{chips('roles', row['roles'], labels, 'r', 'wybierz rolę lub wklej ID i Enter', 'rolelist')}</div>
    </div>
  </div>
  <div class="row"><button class="btn">Zapisz zmiany</button><a class="btn sec" href="/repos">Anuluj</a></div>
  <div class="hint">Zapis ustawia nowy punkt odniesienia — stare zmiany nie zostaną wysłane.</div>
</form>
<div class="card" style="margin-top:26px">
  <h3>Akcje</h3><div class="desc">Ostatnie sprawdzenie: {esc(row['last_check']) or '—'} · ostatni commit: {esc(row['last_sha'][:7]) or '—'}</div>
  <div class="row">{post_button(f'/repos/{rid}/check', 'Sprawdź teraz', 'sec', 'refresh')}{post_button(f'/repos/{rid}/test', 'Wyślij wiadomość testową', 'sec', 'test')}
  <span class="sp"></span>{post_button(f'/repos/{rid}/delete', 'Usuń repozytorium', 'del', '', 'Usunąć repozytorium?')}</div>
</div>"""
    return layout(
        request, "/repos", esc(row["repo"]), f"Ustawienia powiadomień {repo_state(row)}", body,
        actions=f'<a class="btn sec" href="https://github.com/{esc(row["repo"])}" target="_blank">Otwórz na GitHubie ↗</a>',
        crumb='<a class="crumb" href="/repos">← Repozytoria</a><br>',
    )


async def settings_page(request):
    bot = request.app["bot"]
    labels = await labels_for(bot, get_setting("users"), get_setting("roles"))
    token = "podany — limit 5000 zapytań/h" if GITHUB_TOKEN else "brak — limit 60 zapytań/h (dodaj GITHUB_TOKEN w .env)"
    pills = "".join(
        f'<button type="button" class="pill" onclick="this.form.interval.value={m}">{m} min</button>' for m in (5, 10, 15, 20, 30, 60)
    )
    body = f"""{roles_datalist(bot)}
<form method="post" action="/settings">
  <div class="card">
    <h3>Kanał i częstotliwość</h3><div class="desc">Gdzie bot wysyła wiadomości i jak często sprawdza GitHuba.</div>
    <div class="grid">
      <div><label class="l">Domyślny kanał</label>{channel_select(bot, 'channel_id', get_setting('channel_id'), '— wybierz kanał —')}
        <div class="hint">Każde repo może mieć własny kanał w swoich ustawieniach.</div></div>
      <div><label class="l">Sprawdzaj co (minuty)</label><input type="number" min="1" name="interval" value="{esc(get_setting('interval'))}">
        <div class="row" style="margin-top:8px;gap:6px">{pills}</div></div>
      <div><label class="l">Język wiadomości na Discordzie</label>
        <select name="message_lang"><option value="pl" {'selected' if get_setting('message_lang') == 'pl' else ''}>Polski</option>
        <option value="en" {'selected' if get_setting('message_lang') == 'en' else ''}>English</option></select>
        <div class="hint">Język powiadomień, które bot wysyła na kanał.</div></div>
    </div>
  </div>
  <div class="card">
    <h3>Pingi dla wszystkich repozytoriów</h3><div class="desc">Te osoby i role będą oznaczane przy każdym powiadomieniu.</div>
    <div class="grid">
      <div class="full"><label class="l">Użytkownicy</label>{chips('users', get_setting('users'), labels, 'u', 'wklej ID użytkownika i Enter')}
        <div class="hint">ID: w Discordzie włącz Tryb programisty, PPM na użytkowniku → Kopiuj ID.</div></div>
      <div class="full"><label class="l">Role</label>{chips('roles', get_setting('roles'), labels, 'r', 'wybierz rolę lub wklej ID i Enter', 'rolelist')}</div>
    </div>
  </div>
  <button class="btn">Zapisz ustawienia</button>
</form>
<div class="card" style="margin-top:26px"><h3>GitHub</h3><div class="desc" style="margin:3px 0 0">Token: {token}</div></div>"""
    return layout(request, "/settings", "Ustawienia", "Kanał, częstotliwość i domyślne pingi.", body)


async def accounts_page(request):
    me = request["user"]
    users = await q("SELECT id, username, created_at FROM panel_users ORDER BY username")
    rows = ""
    for u in users:
        if u["id"] == me["id"]:
            action = '<span class="badge ok">to Ty</span>'
        else:
            action = post_button(f'/users/{u["id"]}/delete', "Usuń", "del", "", "Usunąć konto?")
        rows += (
            f'<div class="userrow"><div class="avatar">{esc(u["username"][:1].upper())}</div>'
            f'<div><b>{esc(u["username"])}</b><div class="hint" style="margin:0">dodano {esc(u["created_at"])}</div></div>'
            f'<span class="sp"></span>{action}</div>'
        )
    body = f"""
<div class="card"><h3>Konta z dostępem do panelu</h3><div class="desc">Każdy ma własny login i hasło.</div>{rows}</div>
<form class="card" method="post" action="/users/add">
  <h3>Dodaj konto</h3><div class="desc">Login: 3-32 znaki (litery, cyfry, _ . -). Hasło: min. 8 znaków.</div>
  <div class="grid"><div><label class="l">Login</label><input type="text" name="username" autocomplete="off" required></div>
  <div><label class="l">Hasło</label><input type="password" name="password" autocomplete="new-password" required></div></div>
  <div class="row top"><button class="btn">{icon('plus')}Dodaj konto</button></div>
</form>
<form class="card" method="post" action="/password">
  <h3>Zmień swoje hasło</h3><div class="desc">Po zmianie zalogujesz się ponownie.</div>
  <div class="grid"><div><label class="l">Obecne hasło</label><input type="password" name="current" autocomplete="current-password" required></div>
  <div><label class="l">Nowe hasło</label><input type="password" name="new" autocomplete="new-password" required></div></div>
  <div class="row top"><button class="btn sec">Zmień hasło</button></div>
</form>"""
    return layout(request, "/accounts", "Konta", "Kto może zarządzać botem.", body)


async def login_page(request):
    errors = {"1": "Zły login lub hasło", "2": "Za dużo prób — spróbuj za 10 minut"}
    error = f'<div class="err">{errors[request.query["e"]]}</div>' if request.query.get("e") in errors else ""
    return page(
        f"""<div class="logo" style="justify-content:center;padding-bottom:26px;font-size:22px"><i>G</i>Githubek</div>
<div class="card">{error}
<h3>Zaloguj się</h3><div class="desc">Panel zarządzania botem.</div>
<form method="post" action="/login">
<label class="l">Login</label><input type="text" name="username" autofocus autocomplete="username">
<label class="l" style="margin-top:14px">Hasło</label><input type="password" name="password" autocomplete="current-password">
<div class="row top"><button class="btn" style="width:100%;justify-content:center">Zaloguj</button></div></form></div>"""
    )
