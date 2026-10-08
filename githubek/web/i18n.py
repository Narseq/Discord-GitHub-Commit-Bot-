"""Tłumaczenia panelu (PL domyślnie, EN przez słownik)."""

import contextvars
import re


LANG = contextvars.ContextVar("lang", default="pl")

EN = {
    # menu / układ
    "Przegląd": "Overview",
    "Repozytoria": "Repositories",
    "Ustawienia": "Settings",
    "Konta": "Accounts",
    "łączenie…": "connecting…",
    "Zalogowano:": "Signed in as:",
    "Wyloguj": "Log out",
    "Sprawdź teraz": "Check now",
    # przegląd
    "Co się dzieje z Twoimi repozytoriami.": "What is happening with your repositories.",
    "Nie ustawiono domyślnego kanału — powiadomienia nie będą wysyłane.": "No default channel set — notifications will not be sent.",
    "Ustaw kanał": "Set channel",
    "Aktywne": "Active",
    "Powiadomień (24h)": "Notifications (24h)",
    "Z błędem": "With errors",
    "Ostatnia aktywność": "Recent activity",
    "Wysłane powiadomienia": "Sent notifications",
    "Jeszcze nic nie wysłano. Dodaj repozytorium i poczekaj na pierwszy commit.": "Nothing sent yet. Add a repository and wait for the first commit.",
    "Wiadomość testowa": "Test message",
    # repozytoria
    "Kliknij repozytorium, aby zmienić jego ustawienia.": "Click a repository to change its settings.",
    "Dodaj repozytorium": "Add repository",
    "Wklej link do GitHuba albo wpisz owner/nazwa. Bot zapamięta obecny stan i da znać o kolejnych zmianach.": "Paste a GitHub link or type owner/name. The bot will remember the current state and notify you about future changes.",
    "Dodaj": "Add",
    "Brak repozytoriów — dodaj pierwsze powyżej.": "No repositories yet — add the first one above.",
    "commity": "commits",
    "wersje": "releases",
    "nic": "nothing",
    "kanał globalny": "global channel",
    "własny kanał": "custom channel",
    "dodatkowe pingi:": "extra pings:",
    "Sprawdzono:": "Checked:",
    "błąd": "error",
    "wyłączone": "disabled",
    "aktywne": "active",
    # strona repo
    "← Repozytoria": "← Repositories",
    "Ustawienia powiadomień": "Notification settings",
    "Otwórz na GitHubie ↗": "Open on GitHub ↗",
    "Ostatni błąd:": "Last error:",
    "Co śledzić": "What to track",
    "Wybierz, o czym bot ma Cię informować.": "Choose what the bot should notify you about.",
    "Commity": "Commits",
    "Nowe commity na wybranym branchu": "New commits on the selected branch",
    "Wersje (releases)": "Releases",
    "Nowe wydania na GitHubie": "New releases on GitHub",
    "Repozytorium włączone": "Repository enabled",
    "Wyłącz, aby wstrzymać sprawdzanie": "Turn off to pause checking",
    "puste = domyślny branch repozytorium": "empty = repository default branch",
    "Gdzie i kogo powiadomić": "Where and who to notify",
    "Pingi z tej strony dodają się do globalnych z zakładki Ustawienia.": "Pings from this page are added to the global ones from the Settings tab.",
    "Kanał": "Channel",
    "— kanał domyślny z ustawień —": "— default channel from settings —",
    "Użytkownicy do pingu": "Users to ping",
    "wklej ID użytkownika i Enter": "paste a user ID and press Enter",
    "ID: w Discordzie włącz Tryb programisty, PPM na użytkowniku → Kopiuj ID.": "ID: enable Developer Mode in Discord, right-click the user → Copy ID.",
    "Role do pingu": "Roles to ping",
    "wybierz rolę lub wklej ID i Enter": "pick a role or paste an ID and press Enter",
    "Zapisz zmiany": "Save changes",
    "Anuluj": "Cancel",
    "Zapis ustawia nowy punkt odniesienia — stare zmiany nie zostaną wysłane.": "Saving sets a new baseline — old changes will not be sent.",
    "Akcje": "Actions",
    "Ostatnie sprawdzenie:": "Last check:",
    "ostatni commit:": "last commit:",
    "Wyślij wiadomość testową": "Send test message",
    "Usuń repozytorium": "Delete repository",
    "Usunąć repozytorium?": "Delete this repository?",
    # ustawienia
    "Kanał, częstotliwość i domyślne pingi.": "Channel, frequency and default pings.",
    "Kanał i częstotliwość": "Channel and frequency",
    "Gdzie bot wysyła wiadomości i jak często sprawdza GitHuba.": "Where the bot sends messages and how often it checks GitHub.",
    "Domyślny kanał": "Default channel",
    "Język wiadomości na Discordzie": "Discord message language",
    "Język powiadomień, które bot wysyła na kanał.": "Language of the notifications the bot posts in the channel.",
    "Nie ustawiono kanału (ani globalnego, ani dla repo)": "No channel set (neither global nor for this repository)",
    "— wybierz kanał —": "— choose a channel —",
    "Każde repo może mieć własny kanał w swoich ustawieniach.": "Each repository can have its own channel in its settings.",
    "Sprawdzaj co (minuty)": "Check every (minutes)",
    "Pingi dla wszystkich repozytoriów": "Pings for all repositories",
    "Te osoby i role będą oznaczane przy każdym powiadomieniu.": "These people and roles are mentioned in every notification.",
    "Użytkownicy": "Users",
    "Role": "Roles",
    "Zapisz ustawienia": "Save settings",
    "podany — limit 5000 zapytań/h": "provided — limit 5000 requests/h",
    "brak — limit 60 zapytań/h (dodaj GITHUB_TOKEN w .env)": "missing — limit 60 requests/h (add GITHUB_TOKEN to .env)",
    # konta
    "Kto może zarządzać botem.": "Who can manage the bot.",
    "Konta z dostępem do panelu": "Accounts with panel access",
    "Każdy ma własny login i hasło.": "Everyone has their own login and password.",
    "to Ty": "you",
    "Usuń": "Delete",
    "Usunąć konto?": "Delete this account?",
    "dodano": "added",
    "Dodaj konto": "Add account",
    "Login: 3-32 znaki (litery, cyfry, _ . -). Hasło: min. 8 znaków.": "Login: 3-32 characters (letters, digits, _ . -). Password: min. 8 characters.",
    "Hasło": "Password",
    "Zmień swoje hasło": "Change your password",
    "Po zmianie zalogujesz się ponownie.": "You will have to sign in again afterwards.",
    "Obecne hasło": "Current password",
    "Nowe hasło": "New password",
    "Zmień hasło": "Change password",
    # logowanie
    "Zaloguj się": "Sign in",
    "Panel zarządzania botem.": "Bot management panel.",
    "Zaloguj": "Log in",
    "Zły login lub hasło": "Wrong login or password",
    "Za dużo prób — spróbuj za 10 minut": "Too many attempts — try again in 10 minutes",
    # komunikaty
    "Nieprawidłowy link/nazwa repo": "Invalid repository link/name",
    "To repo już jest dodane": "This repository is already added",
    "Zapisano zmiany": "Changes saved",
    "Zapisano ustawienia": "Settings saved",
    "Usunięto repozytorium": "Repository deleted",
    "Sprawdzono wszystkie repozytoria": "Checked all repositories",
    "Sprawdzono": "Checked",
    "Wysłano wiadomość testową": "Test message sent",
    "Login: 3-32 znaków (litery, cyfry, _ . -)": "Login: 3-32 characters (letters, digits, _ . -)",
    "Hasło musi mieć min. 8 znaków": "Password must have at least 8 characters",
    "Taki login już istnieje": "This login already exists",
    "Nie możesz usunąć własnego konta": "You cannot delete your own account",
    "Usunięto konto": "Account deleted",
    "Obecne hasło jest nieprawidłowe": "Current password is incorrect",
    "Nowe hasło musi mieć min. 8 znaków": "New password must have at least 8 characters",
    "Nie znaleziono repozytorium": "Repository not found",
}

EN_PATTERNS = [
    (re.compile(r"sprawdzanie co (\d+) min"), r"checking every \1 min"),
    (re.compile(r"(\d+) nowy commit"), r"\1 new commit"),
    (re.compile(r"(\d+) nowe commity"), r"\1 new commits"),
    (re.compile(r"nowa wersja (\S+)"), r"new release \1"),
    (re.compile(r"Dodano konto ([^<]+)"), r"Account \1 added"),
    (re.compile(r"Dodano ([^<]+?) — ustaw teraz powiadomienia"), r"Added \1 — now set up notifications"),
    (re.compile(r"Błąd wysyłania: ([^<]*)"), r"Sending error: \1"),
]


def _build_regex():
    parts = []
    for key in sorted(EN, key=len, reverse=True):
        before = r"(?<!\w)" if key[0].isalnum() else ""
        after = r"(?!\w)" if key[-1].isalnum() else ""
        parts.append(before + re.escape(key) + after)
    return re.compile("|".join(parts))


EN_RE = _build_regex()


def translate(text):
    for pattern, repl in EN_PATTERNS:
        text = pattern.sub(repl, text)
    return EN_RE.sub(lambda m: EN[m.group(0)], text)
