"""Panel www (aiohttp): routing, logowanie, pliki statyczne."""

from aiohttp import web

from ..accounts import current_user, init_users
from ..config import HOST, PORT, log
from .actions import (
    check_all_now,
    login_post,
    logout,
    password_change,
    repo_add,
    repo_check,
    repo_delete,
    repo_test,
    repo_update,
    save_settings,
    set_lang,
    user_add,
    user_delete,
)
from .i18n import LANG
from .pages import (
    accounts_page,
    index,
    login_page,
    repo_page,
    repos_page,
    settings_page,
)
from .ui import STATIC_DIR


def build_app(bot):
    app = web.Application(middlewares=[auth_middleware])
    app["bot"] = bot
    app.router.add_static("/static", STATIC_DIR)
    app.add_routes(
        [
            web.get("/", index),
            web.get("/lang/{code}", set_lang),
            web.get("/repos", repos_page),
            web.get("/repos/{id}", repo_page),
            web.get("/settings", settings_page),
            web.get("/accounts", accounts_page),
            web.get("/login", login_page),
            web.post("/login", login_post),
            web.post("/logout", logout),
            web.post("/settings", save_settings),
            web.post("/repos/add", repo_add),
            web.post("/repos/{id}/update", repo_update),
            web.post("/repos/{id}/delete", repo_delete),
            web.post("/repos/{id}/check", repo_check),
            web.post("/repos/{id}/test", repo_test),
            web.post("/check-all", check_all_now),
            web.post("/users/add", user_add),
            web.post("/users/{id}/delete", user_delete),
            web.post("/password", password_change),
        ]
    )
    return app


async def start_web(bot):
    """Uruchamia panel www; zwraca runner (do zamknięcia) albo None, gdy panel jest wyłączony."""
    try:
        await init_users()
    except Exception:
        log.exception("Panel www wyłączony: błąd MySQL / brak kont (sprawdź MYSQL_* i PANEL_PASSWORD)")
        return None
    runner = web.AppRunner(build_app(bot), access_log=None)
    await runner.setup()
    await web.TCPSite(runner, HOST, PORT).start()
    log.info("Panel www: http://%s:%s", HOST, PORT)
    return runner


@web.middleware
async def auth_middleware(request, handler):
    LANG.set("en" if request.cookies.get("lang") == "en" else "pl")
    if request.path == "/login" or request.path.startswith(("/lang/", "/static/")):
        return await handler(request)
    try:
        user = await current_user(request)
    except Exception:
        log.exception("Błąd MySQL przy sprawdzaniu sesji")
        return web.Response(text="Błąd połączenia z bazą MySQL", status=503)
    if not user:
        raise web.HTTPFound("/login")
    request["user"] = user
    return await handler(request)
