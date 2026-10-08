"""Teksty wiadomości wysyłanych na Discordzie (PL / EN, wybór w ustawieniach panelu)."""

from .storage import get_setting

MESSAGES = {
    "pl": {
        "commit_one": "nowy commit",
        "commit_many": "nowe commity",
        "more": "… i {n} więcej",
        "release": "nowa wersja {tag}",
        "release_field": "Wydanie",
        "type_field": "Typ",
        "prerelease": "pre-release",
        "test_title": "Test: {repo}",
        "test_desc": "Tak będą wyglądać powiadomienia.",
    },
    "en": {
        "commit_one": "new commit",
        "commit_many": "new commits",
        "more": "… and {n} more",
        "release": "new release {tag}",
        "release_field": "Release",
        "type_field": "Type",
        "prerelease": "pre-release",
        "test_title": "Test: {repo}",
        "test_desc": "This is what notifications will look like.",
    },
}


def msg(key, **kwargs):
    texts = MESSAGES.get(get_setting("message_lang"), MESSAGES["pl"])
    return texts[key].format(**kwargs)
