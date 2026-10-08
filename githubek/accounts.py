"""Konta panelu w MySQL: hasła, sesje, limit prób logowania."""

import asyncio
import base64
import hashlib
import hmac
import secrets
import time

import pymysql
import pymysql.cursors

from .config import MYSQL, PANEL_PASSWORD, PANEL_USER, SESSION_DAYS, SESSION_SECRET, log


def _mysql(sql, args, mode):
    conn = pymysql.connect(
        **MYSQL, cursorclass=pymysql.cursors.DictCursor, connect_timeout=10, autocommit=True, charset="utf8mb4"
    )
    try:
        with conn.cursor() as cur:
            cur.execute(sql, args)
            if mode == "one":
                return cur.fetchone()
            if mode == "all":
                return cur.fetchall()
            return cur.rowcount
    finally:
        conn.close()


async def q(sql, args=(), mode="all"):
    return await asyncio.to_thread(_mysql, sql, args, mode)


def hash_password(password):
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1, dklen=32)
    return f"scrypt${base64.b64encode(salt).decode()}${base64.b64encode(digest).decode()}"


def verify_password(password, stored):
    try:
        _, salt, digest = stored.split("$")
        expected = base64.b64decode(digest)
        actual = hashlib.scrypt(password.encode(), salt=base64.b64decode(salt), n=2**14, r=8, p=1, dklen=32)
    except Exception:
        return False
    return hmac.compare_digest(actual, expected)


async def init_users():
    await q(
        """CREATE TABLE IF NOT EXISTS panel_users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(64) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ) DEFAULT CHARSET=utf8mb4""",
        mode=None,
    )
    count = (await q("SELECT COUNT(*) AS c FROM panel_users", mode="one"))["c"]
    if count == 0:
        if not PANEL_PASSWORD:
            raise RuntimeError("Brak kont w panel_users — ustaw PANEL_USER i PANEL_PASSWORD, by utworzyć pierwsze")
        await q(
            "INSERT INTO panel_users(username, password_hash) VALUES(%s, %s)",
            (PANEL_USER, hash_password(PANEL_PASSWORD)),
            mode=None,
        )
        log.info("Utworzono pierwsze konto panelu: %s (możesz usunąć PANEL_PASSWORD z .env)", PANEL_USER)


def session_cookie(user):
    exp = int(time.time()) + SESSION_DAYS * 86400
    return f"{user['username']}|{exp}|{_sign(user, exp)}"


def _sign(user, exp):
    key = f"{SESSION_SECRET}:{user['password_hash']}".encode()
    return hmac.new(key, f"{user['username']}|{exp}".encode(), hashlib.sha256).hexdigest()


async def current_user(request):
    parts = request.cookies.get("session", "").split("|")
    if len(parts) != 3 or not parts[1].isdigit() or int(parts[1]) < time.time():
        return None
    user = await q("SELECT * FROM panel_users WHERE username=%s", (parts[0],), mode="one")
    if user and hmac.compare_digest(parts[2], _sign(user, parts[1])):
        return user
    return None


LOGIN_FAILS = {}


def login_locked(ip):
    recent = [t for t in LOGIN_FAILS.get(ip, []) if t > time.time() - 600]
    LOGIN_FAILS[ip] = recent
    return len(recent) >= 5
