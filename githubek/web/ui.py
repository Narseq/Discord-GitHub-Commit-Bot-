"""Wspólny układ strony i elementy interfejsu."""

import html
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

from aiohttp import web

from .i18n import LANG, translate


STATIC_DIR = Path(__file__).resolve().parent / "static"
ASSET_V = int(max(p.stat().st_mtime for p in STATIC_DIR.glob("*.*")))  # odświeża cache po zmianie plików


ICONS = {
    "home": '<path d="M3 11l9-8 9 8v10a1 1 0 0 1-1 1h-5v-7H9v7H4a1 1 0 0 1-1-1z"/>',
    "repos": '<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>',
    "settings": '<path d="M4 6h9M17 6h3M4 12h3M11 12h9M4 18h11M19 18h1"/><circle cx="15" cy="6" r="2"/><circle cx="9" cy="12" r="2"/><circle cx="17" cy="18" r="2"/>',
    "users": '<circle cx="9" cy="8" r="4"/><path d="M2 21a7 7 0 0 1 14 0M17 4a4 4 0 0 1 0 8M22 21a7 7 0 0 0-4-6"/>',
    "commit": '<circle cx="12" cy="12" r="3"/><path d="M3 12h6M15 12h6"/>',
    "release": '<path d="M20 12l-8 8-9-9V3h8z"/><circle cx="7.5" cy="7.5" r="1"/>',
    "test": '<path d="M22 2L11 13M22 2l-7 20-4-9-9-4z"/>',
    "refresh": '<path d="M21 12a9 9 0 1 1-3-6.7L21 8M21 3v5h-5"/>',
    "plus": '<path d="M12 5v14M5 12h14"/>',
    "out": '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9"/>',
}


def icon(name):
    return f'<svg viewBox="0 0 24 24">{ICONS[name]}</svg>'


def lang_switch(path):
    current = LANG.get()
    links = "".join(
        f'<a class="{"on" if code == current else ""}" href="/lang/{code}?next={quote(path)}">{code.upper()}</a>'
        for code in ("pl", "en")
    )
    return f'<div class="lang">{links}</div>'


def shell(inner):
    lang = LANG.get()
    text = (
        f"<!doctype html><html lang='{lang}'><head><meta charset='utf-8'>"
        f"<meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<title>Githubek</title><link rel='stylesheet' href='/static/style.css?v={ASSET_V}'></head>"
        f"<body>{inner}<script src='/static/app.js?v={ASSET_V}'></script></body></html>"
    )
    return web.Response(text=translate(text) if lang == "en" else text, content_type="text/html")


def page(body, msg=""):
    """Strona bez menu (logowanie)."""
    flash = f'<div class="msg">{html.escape(msg)}</div>' if msg else ""
    return shell(f'<div class="login"><div style="display:flex;justify-content:flex-end">{lang_switch("/login")}</div>{flash}{body}</div>')


NAV = [
    ("/", "Przegląd", "home"),
    ("/repos", "Repozytoria", "repos"),
    ("/settings", "Ustawienia", "settings"),
    ("/accounts", "Konta", "users"),
]


def layout(request, active, title, sub, body, actions="", crumb="", wide=False):
    bot = request.app["bot"]
    me = request["user"]["username"]
    nav = "".join(
        f'<a class="nav {"on" if href == active else ""}" href="{href}">{icon(ic)}<span>{label}</span></a>'
        for href, label, ic in NAV
    )
    online = bool(bot.user)
    flash = f'<div class="msg">{esc(request.query.get("msg", ""))}</div>' if request.query.get("msg") else ""
    return shell(
        f"""<div class="app">
<aside>
  <div class="logo"><i>G</i>Githubek</div>
  {nav}
  <div class="side-foot">
    <div class="who"><span class="dot {'on' if online else ''}"></span>{esc(bot.user) if online else 'łączenie…'}</div>
    <div class="sub">Zalogowano: {esc(me)}</div>
    {lang_switch(request.path)}
    <form method="post" action="/logout"><button class="btn sec" style="width:100%;justify-content:center">{icon('out')}<span style="display:inline">Wyloguj</span></button></form>
  </div>
</aside>
<main{' class="wide"' if wide else ''}>
  <div class="pagehead"><div>{crumb}<h1>{title}</h1><p>{sub}</p></div><div class="row">{actions}</div></div>
  {flash}{body}
</main></div>"""
    )


def esc(value):
    return html.escape(str(value or ""), quote=True)


def soft_break(text):
    """Tekst z escapowaniem; zawija się tylko w naturalnych miejscach (- _ . i zmiana wielkości liter)."""
    out = esc(text)
    out = re.sub(r"([-_.])", r"\1<wbr>", out)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1<wbr>\2", out)


def hue_of(text):
    """Stały kolor (0-359) dla danego tekstu, np. właściciela repo."""
    return sum(map(ord, text)) * 37 % 360


def checked(value):
    return "checked" if value else ""


_user_names = {}


async def user_label(bot, uid):
    if uid not in _user_names:
        user = bot.get_user(int(uid))
        if not user:
            try:
                user = await bot.fetch_user(int(uid))
            except Exception:
                user = None
        _user_names[uid] = ("@" + user.display_name) if user else None
    return _user_names[uid]


def role_label(bot, rid):
    for guild in bot.guilds:
        role = guild.get_role(int(rid))
        if role:
            return f"@{role.name}"
    return None


async def labels_for(bot, users, roles):
    out = {}
    for uid in filter(None, users.split(",")):
        out["u" + uid] = await user_label(bot, uid)
    for rid in filter(None, roles.split(",")):
        out["r" + rid] = role_label(bot, rid)
    return out


def chips(name, ids, labels, prefix, placeholder, listid=""):
    items = ""
    for cid in filter(None, ids.split(",")):
        label = labels.get(prefix + cid)
        small = f"<small>{cid}</small>" if label else ""
        items += f'<span class="chip" data-id="{cid}">{esc(label or cid)}{small}<b>&times;</b></span>'
    list_attr = f'list="{listid}"' if listid else ""
    return (
        f'<div class="chips"><input type="hidden" name="{name}" value="{esc(ids)}">'
        f'<div class="chiplist">{items}</div>'
        f'<input type="text" class="chipadd" placeholder="{placeholder}" {list_attr}></div>'
    )


def roles_datalist(bot):
    options = "".join(
        f'<option value="{role.id}" label="@{esc(role.name)} ({esc(g.name)})">'
        for g in bot.guilds
        for role in g.roles
        if not role.is_default()
    )
    return f'<datalist id="rolelist">{options}</datalist>'


def channel_select(bot, name, current, blank):
    opts = f'<option value="">{blank}</option>'
    found = not current
    for guild in bot.guilds:
        group = ""
        for chan in guild.text_channels:
            sel = "selected" if str(chan.id) == current else ""
            found = found or bool(sel)
            group += f'<option value="{chan.id}" {sel}>#{esc(chan.name)}</option>'
        opts += f'<optgroup label="{esc(guild.name)}">{group}</optgroup>'
    if not found:
        opts += f'<option value="{esc(current)}" selected>ID {esc(current)} (nieznany kanał)</option>'
    return f'<select name="{name}">{opts}</select>'


def channel_name(bot, channel_id):
    chan = bot.get_channel(int(channel_id)) if channel_id else None
    return f"#{chan.name}" if chan else ""


def repo_state(row):
    if row["last_error"]:
        return '<span class="badge bad">błąd</span>'
    if not row["enabled"]:
        return '<span class="badge">wyłączone</span>'
    return '<span class="badge ok">aktywne</span>'


def post_button(action, label, cls="sec", ic="", confirm=""):
    onsubmit = f' onsubmit="return confirm(\'{confirm}\')"' if confirm else ""
    return f'<form method="post" action="{action}"{onsubmit}><button class="btn {cls}">{icon(ic) if ic else ""}{label}</button></form>'


def redirect(msg="", to="/"):
    raise web.HTTPFound(to + (f"?msg={quote(msg)}" if msg else ""))


def time_label(ts):
    try:
        return datetime.strptime(ts, "%Y-%m-%d %H:%M:%S").strftime("%d.%m %H:%M")
    except ValueError:
        return ts
