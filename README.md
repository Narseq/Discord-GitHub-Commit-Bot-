# Githubek

**English** | [Polski](README.pl.md)

A Discord bot that watches GitHub repositories and posts a message to a channel when there is a **new commit** or a **new release**. Everything is configured in a built-in web panel (available in English and Polish) - no commands to learn.

## Features

- Checks your repositories every few minutes (you choose how often) and posts an embed on Discord
- Watches **commits** (any branch) and **releases**, per repository
- **Ping users and roles**: globally for all repositories and/or extra ones per repository
- A separate Discord channel per repository (or one default channel)
- Web panel with login/password accounts, overview with recent activity, PL/EN switch
- Uses ETags, so unchanged repositories do not use up your GitHub rate limit
- Language of the Discord messages (Polish or English) and of the panel (PL/EN) can be set independently

## Requirements

- Python 3.10 or newer (tested on 3.14)
- A MySQL / MariaDB database (only used to store the panel's login accounts)
- A Discord account to create the bot

## Setup, step by step

### 1. Create the Discord bot

1. Open the [Discord Developer Portal](https://discord.com/developers/applications) and click **New Application**.
2. Go to the **Bot** tab and click **Reset Token**, then copy the token. You will need it in step 4. Keep it secret.
3. You do **not** need to enable any "Privileged Gateway Intents".
4. Copy your **Application ID** (tab **General Information**) and open this link, replacing `YOUR_CLIENT_ID`:

   ```
   https://discord.com/oauth2/authorize?client_id=YOUR_CLIENT_ID&permissions=19456&scope=bot
   ```

   Choose your server and confirm. The permissions in the link are: View Channels, Send Messages, Embed Links.
5. Make sure the bot can see and write in the channel you want to use.

### 2. Create the MySQL database

Run this in your MySQL console (or use your hosting panel and create a database and user there):

```sql
CREATE DATABASE githubek CHARACTER SET utf8mb4;
CREATE USER 'githubek'@'%' IDENTIFIED BY 'choose-a-strong-password';
GRANT ALL PRIVILEGES ON githubek.* TO 'githubek'@'%';
FLUSH PRIVILEGES;
```

The bot creates the `panel_users` table by itself on first start. If MySQL runs on the same machine, you can use `'githubek'@'localhost'` instead of `'%'`.

### 3. Get the code and install dependencies

```bash
git clone https://github.com/Narseq/githubek.git
cd githubek
python -m venv venv
# Windows:  venv\Scripts\activate
# Linux/macOS:  source venv/bin/activate
pip install -r requirements.txt
```

### 4. Configure

Copy `.env.example` to `.env` and fill it in:

| Variable | What to put there |
| --- | --- |
| `DISCORD_TOKEN` | The bot token from step 1 |
| `PORT` | Port for the web panel, e.g. `8080` |
| `PANEL_USER`, `PANEL_PASSWORD` | Login of your first panel account (use a strong password) |
| `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE` | The database from step 2 |
| `GITHUB_TOKEN` | *Optional*, see below |

**GitHub token (recommended).** Without it GitHub allows only 60 requests per hour, which is not enough for many repositories. Create one at <https://github.com/settings/tokens> -> **Generate new token (classic)**, select **no scopes**, and paste it into `GITHUB_TOKEN`.

### 5. Start it

```bash
python app.py
```

You should see lines like `Panel www: http://0.0.0.0:8080` and `Zalogowano jako <your bot>` (logged in as).

### 6. Use the panel

1. Open `http://localhost:8080` (or your server's address and port) and log in with `PANEL_USER` / `PANEL_PASSWORD`.
2. Go to **Settings** and choose the **default channel**. Without it the bot sends nothing. Optionally set the check interval, the **language of the Discord messages** and the users/roles to ping.
3. Go to **Repositories**, paste a GitHub link (or `owner/repo`) and click **Add**. The bot remembers the current state and only reports **new** changes after that.
4. Click a repository to choose what to watch, its branch, its own channel and extra pings. Use **Send test message** to check that everything works.
5. After the first login, change your password under **Accounts** and remove `PANEL_PASSWORD` from `.env`.

**How do I get a user or role ID?** In Discord enable *Settings -> Advanced -> Developer Mode*, then right-click the user or role and choose **Copy ID**. Roles can also be picked from a list in the panel.

## Running on a game/bot hosting panel (Pterodactyl and similar)

1. Upload `app.py`, `requirements.txt`, the whole `githubek/` folder and your `.env`.
2. Set the startup file to `app.py` and make sure `requirements.txt` is installed on start.
3. Set `PORT` in `.env` to the port assigned to your server.

## Security notes

- Never commit `.env` (it is already in `.gitignore`).
- The panel serves plain HTTP. If it is reachable from the internet, put it behind a reverse proxy with HTTPS (nginx, Caddy, ...).
- Passwords are stored as salted scrypt hashes. After 5 failed logins an IP is blocked for 10 minutes.

## Project layout

```
app.py                  entry point
githubek/
  config.py             settings from .env
  storage.py            local SQLite: repositories, settings, history (data.db)
  accounts.py           panel accounts in MySQL, passwords, sessions
  messages.py           texts of the Discord messages (PL/EN)
  bot.py                Discord bot: GitHub polling, notifications
  web/
    __init__.py         routing and login middleware
    pages.py            pages (GET)
    actions.py          form actions (POST)
    ui.py               layout and UI helpers
    i18n.py             PL -> EN translations
    static/             style.css, app.js
```

To add or fix a translation of the panel, edit the `EN` dictionary in `githubek/web/i18n.py`. The texts of the Discord messages are in `githubek/messages.py`.

## License

MIT License - Copyright (c) 2026 Narseq. See [LICENSE](LICENSE).

You are free to use, copy, modify and share this bot, also for your own server or project. The only condition is that you keep the copyright notice and the license text, so the original author (Narseq) stays credited.
