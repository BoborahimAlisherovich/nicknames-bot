"""Admin paneldan o'zgartiriladigan sozlamalar.

Bazadagi qiymat bo'lsa o'sha ishlatiladi, bo'lmasa .env dagi qiymat.
"""
from data import config
from loader import db


def _get(key, default):
    try:
        v = db.get_setting(key)
    except Exception:
        v = None
    return default if v is None else v


def gemini_key() -> str:
    return _get("gemini_key", config.GEMINI_API_KEY)


def cards() -> list[str]:
    v = _get("cards", None)
    return config.CARDS if v is None else [c for c in v.split("|") if c]


def set_cards(items: list[str]):
    db.set_setting("cards", "|".join(items))


def card_owner() -> str:
    return _get("card_owner", config.CARD_OWNER)
