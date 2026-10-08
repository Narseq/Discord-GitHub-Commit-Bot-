# Githubek

[English](README.md) | **Polski**

Bot Discord, który obserwuje repozytoria GitHub i wysyła wiadomość na kanał, gdy pojawi się **nowy commit** lub **nowa wersja (release)**. Całość ustawiasz we wbudowanym panelu www (po polsku lub angielsku) - bez uczenia się komend.

## Funkcje

- Sprawdza repozytoria co kilka minut (sam wybierasz jak często) i wysyła embed na Discorda
- Śledzi **commity** (dowolny branch) i **wersje (releases)**, osobno dla każdego repozytorium
- **Pingowanie użytkowników i ról**: globalnie dla wszystkich repozytoriów i/lub dodatkowe dla wybranego
- Osobny kanał dla każdego repozytorium (albo jeden kanał domyślny)
- Panel www z kontami (login i hasło), przegląd z ostatnią aktywnością, przełącznik PL/EN
- Używa ETag, więc niezmienione repozytoria nie zużywają limitu zapytań GitHuba
- Język wiadomości na Discordzie (polski lub angielski) i język panelu (PL/EN) ustawiasz niezależnie

## Wymagania

- Python 3.10 lub nowszy (testowane na 3.14)
- Baza MySQL / MariaDB (służy tylko do przechowywania kont logowania do panelu)
- Konto Discord, aby stworzyć bota

## Instalacja krok po kroku

### 1. Stwórz bota na Discordzie

1. Wejdź do [Discord Developer Portal](https://discord.com/developers/applications) i kliknij **New Application**.
2. Przejdź do zakładki **Bot**, kliknij **Reset Token** i skopiuj token. Przyda się w kroku 4. Nikomu go nie pokazuj.
3. **Nie** musisz włączać żadnych „Privileged Gateway Intents".
4. Skopiuj **Application ID** (zakładka **General Information**) i otwórz poniższy link, podmieniając `YOUR_CLIENT_ID`:

   ```
   https://discord.com/oauth2/authorize?client_id=YOUR_CLIENT_ID&permissions=19456&scope=bot
   ```

   Wybierz serwer i potwierdź. Uprawnienia w linku to: Wyświetlanie kanałów, Wysyłanie wiadomości, Osadzanie linków (embedy).
5. Upewnij się, że bot widzi kanał, na którym ma pisać, i ma na nim prawo pisania.

### 2. Stwórz bazę MySQL

Wykonaj to w konsoli MySQL (albo utwórz bazę i użytkownika w panelu swojego hostingu):

```sql
CREATE DATABASE githubek CHARACTER SET utf8mb4;
CREATE USER 'githubek'@'%' IDENTIFIED BY 'wymysl-mocne-haslo';
GRANT ALL PRIVILEGES ON githubek.* TO 'githubek'@'%';
FLUSH PRIVILEGES;
```

Tabelę `panel_users` bot utworzy sam przy pierwszym starcie. Jeśli MySQL działa na tej samej maszynie, zamiast `'%'` możesz użyć `'localhost'`.

### 3. Pobierz kod i zainstaluj zależności

```bash
git clone https://github.com/Narseq/githubek.git
cd githubek
python -m venv venv
# Windows:  venv\Scripts\activate
# Linux/macOS:  source venv/bin/activate
pip install -r requirements.txt
```

### 4. Skonfiguruj

Skopiuj `.env.example` do `.env` i uzupełnij:

| Zmienna | Co wpisać |
| --- | --- |
| `DISCORD_TOKEN` | Token bota z kroku 1 |
| `PORT` | Port panelu www, np. `8080` |
| `PANEL_USER`, `PANEL_PASSWORD` | Login i hasło pierwszego konta w panelu (użyj mocnego hasła) |
| `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE` | Baza z kroku 2 |
| `GITHUB_TOKEN` | *Opcjonalnie*, patrz niżej |

**Token GitHub (zalecany).** Bez niego GitHub pozwala tylko na 60 zapytań na godzinę, co nie wystarczy przy wielu repozytoriach. Utwórz go na <https://github.com/settings/tokens> -> **Generate new token (classic)**, **nie zaznaczaj żadnych uprawnień** i wklej do `GITHUB_TOKEN`.

### 5. Uruchom

```bash
python app.py
```

W konsoli powinny pojawić się linie typu `Panel www: http://0.0.0.0:8080` i `Zalogowano jako <nazwa twojego bota>`.

### 6. Korzystaj z panelu

1. Otwórz `http://localhost:8080` (albo adres i port swojego serwera) i zaloguj się danymi `PANEL_USER` / `PANEL_PASSWORD`.
2. Wejdź w **Ustawienia** i wybierz **domyślny kanał**. Bez niego bot niczego nie wyśle. Opcjonalnie ustaw częstotliwość sprawdzania, **język wiadomości na Discordzie** oraz użytkowników/role do pingowania.
3. Wejdź w **Repozytoria**, wklej link do GitHuba (albo `owner/repo`) i kliknij **Dodaj**. Bot zapamięta obecny stan i od tej pory zgłasza tylko **nowe** zmiany.
4. Kliknij repozytorium, aby wybrać, co śledzić, branch, własny kanał i dodatkowe pingi. Przyciskiem **Wyślij wiadomość testową** sprawdzisz, czy wszystko działa.
5. Po pierwszym logowaniu zmień hasło w zakładce **Konta** i usuń `PANEL_PASSWORD` z `.env`.

**Skąd wziąć ID użytkownika lub roli?** W Discordzie włącz *Ustawienia -> Zaawansowane -> Tryb programisty*, potem kliknij użytkownika lub rolę prawym przyciskiem i wybierz **Kopiuj ID**. Role można też wybrać z listy w panelu.

## Uruchomienie na hostingu (Pterodactyl i podobne)

1. Wgraj `app.py`, `requirements.txt`, cały folder `githubek/` oraz swój `.env`.
2. Ustaw plik startowy na `app.py` i zadbaj, żeby `requirements.txt` instalował się przy starcie.
3. W `.env` ustaw `PORT` na port przydzielony Twojemu serwerowi.

## Bezpieczeństwo

- Nigdy nie wrzucaj `.env` do repozytorium (jest już w `.gitignore`).
- Panel działa po zwykłym HTTP. Jeśli jest dostępny z internetu, postaw przed nim reverse proxy z HTTPS (nginx, Caddy itp.).
- Hasła są zapisane jako hashe scrypt z solą. Po 5 nieudanych logowaniach adres IP jest blokowany na 10 minut.

## Struktura projektu

```
app.py                  punkt startowy
githubek/
  config.py             ustawienia z .env
  storage.py            lokalny SQLite: repozytoria, ustawienia, historia (data.db)
  accounts.py           konta panelu w MySQL, hasła, sesje
  messages.py           teksty wiadomości na Discordzie (PL/EN)
  bot.py                bot Discord: sprawdzanie GitHuba, powiadomienia
  web/
    __init__.py         routing i logowanie (middleware)
    pages.py            strony (GET)
    actions.py          akcje formularzy (POST)
    ui.py               układ strony i elementy interfejsu
    i18n.py             tłumaczenia PL -> EN
    static/             style.css, app.js
```

Aby dodać lub poprawić tłumaczenie panelu, edytuj słownik `EN` w `githubek/web/i18n.py`. Teksty wiadomości na Discordzie są w `githubek/messages.py`.

## Licencja

Licencja MIT - Copyright (c) 2026 Narseq. Zobacz [LICENSE](LICENSE).

Możesz swobodnie używać, kopiować, modyfikować i udostępniać tego bota, także na własnym serwerze lub w swoim projekcie. Jedyny warunek to zachowanie informacji o prawach autorskich i tekstu licencji, dzięki czemu autor (Narseq) pozostaje wskazany.
