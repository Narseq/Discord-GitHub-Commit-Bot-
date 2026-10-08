"""Konfiguracja z pliku .env / zmiennych środowiskowych."""

import logging
import os
import re
from pathlib import Path

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

TOKEN = os.getenv("DISCORD_TOKEN", "")
PANEL_PASSWORD = os.getenv("PANEL_PASSWORD", "")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "9260"))
DB_PATH = os.getenv("DB_PATH", "data.db")
PANEL_USER = os.getenv("PANEL_USER", "admin")
MYSQL = {
    "host": os.getenv("MYSQL_HOST", "127.0.0.1"),
    "port": int(os.getenv("MYSQL_PORT", "3306")),
    "user": os.getenv("MYSQL_USER", ""),
    "password": os.getenv("MYSQL_PASSWORD", ""),
    "database": os.getenv("MYSQL_DATABASE", ""),
}
SESSION_SECRET = os.getenv("SECRET_KEY") or MYSQL["password"]
SESSION_DAYS = 14
USERNAME_RE = re.compile(r"^[A-Za-z0-9_.-]{3,32}$")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("githubek")
