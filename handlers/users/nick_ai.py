"""AI va ijodiy nick generatori.

Gemini API orqali haqiqiy AI niklar yaratadi. API kalit bo'lmasa yoki
limit tugasa - lokal ijodiy dvigatel ishga tushadi (bir necha soniyada,
cheksiz va bepul).
"""
import html
import logging
import random
import re

import ssl

import aiohttp
import certifi

_SSL = ssl.create_default_context(cafile=certifi.where())

from data.config import GEMINI_API_KEY, GEMINI_MODEL

logger = logging.getLogger(__name__)

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent"
)

# ------------------------------------------------------------------
# Lokal ijodiy dvigatel (API'siz ishlaydigan zaxira)
# ------------------------------------------------------------------

THEMES = {
    "gaming": {
        "emoji_uz": "🎮", "label_uz": "Gaming", "label_us": "Gaming", "label_ru": "Gaming",
        "words": ["Shadow", "Reaper", "Slayer", "Hunter", "Sniper", "Blade", "Wolf", "Venom",
                  "Killer", "Phantom", "Legend", "Sniper", "Rider", "Beast", "Rampage", "Overlord"],
    },
    "anime": {
        "emoji_uz": "🥷", "label_uz": "Anime", "label_us": "Anime", "label_ru": "Аниме",
        "words": ["Itachi", "Kakashi", "Zoro", "Levi", "Gojo", "Tanjiro", "Naruto", "Rengoku",
                  "Saitama", "Kirito", "Yato", "Kaneki", "Senju", "Uchiha", "Akatsuki", "Sensei"],
    },
    "sevgi": {
        "emoji_uz": "💖", "label_uz": "Sevgi", "label_us": "Love", "label_ru": "Любовь",
        "words": ["Sweet", "Angel", "Cherry", "Blossom", "Darling", "Lovely", "Sweetie", "Honey",
                  "Rose", "Butterfly", "Melody", "Stardust", "Dreamy", "Cutie", "Sunshine", "Moonlight"],
    },
    "dark": {
        "emoji_uz": "🖤", "label_uz": "Dark", "label_us": "Dark", "label_ru": "Dark",
        "words": ["Demon", "Ghost", "Death", "Nyx", "Raven", "Grim", "Void", "Shadow",
                  "Hollow", "Wraith", "Sinister", "Nocturne", "Abyss", "Cursed", "Eclipse", "Requiem"],
    },
    "premium": {
        "emoji_uz": "👑", "label_uz": "Premium", "label_us": "Premium", "label_ru": "Премиум",
        "words": ["Lord", "King", "Baron", "Emperor", "Royal", "Crown", "Imperial", "Monarch",
                  "Grand", "Duke", "Knight", "Elite", "Supreme", "Ace", "Titan", "Sovereign"],
    },
    "qiziqarli": {
        "emoji_uz": "😂", "label_uz": "Qiziqarli", "label_us": "Funny", "label_ru": "Смешные",
        "words": ["Shalva", "Gapa", "Shoshilo", "Kulcha", "Bossik", "Jigar", "Dosli", "Oripov",
                  "ShumBola", "Koptok", "Chimchik", "Do'pi", "Kelasi", "Poshsha", "Laqqi", "Tuya"],
    },
}

DECO = ["༄", "乂", "亗", "࿐", "☰", "⌁", "♛", "★", "෴", "ش", "™", "乡", "๛", "✗", "⚡", "꧁", "꧂"]
EMOJIS = ["🐺", "🖤", "⚡", "🔥", "💜", "👑", "🥷", "🌙", "✨", "😎", "🍀", "🐉"]

TRANSLIT = {
    "a": "a", "b": "b", "c": "c", "d": "d", "e": "e", "f": "f", "g": "g", "h": "h",
    "i": "i", "j": "j", "k": "k", "l": "l", "m": "m", "n": "n", "o": "o", "p": "p",
    "q": "q", "r": "r", "s": "s", "t": "t", "u": "u", "v": "v", "w": "w", "x": "x",
    "y": "y", "z": "z", "'": "", "’": "", "‘": "",
}


def _clean_name(name: str) -> str:
    return name.strip().title()[:20]


def _stylize(word: str) -> str:
    """So'zga turli bezaklar qo'shib kayfiyat beradi."""
    variants = [
        word,
        f"꧁{word}꧂",
        f"{random.choice(DECO)}{word}{random.choice(DECO)}",
        f"{word}™",
        f"{word.upper()}",
        f"{word.lower()}",
        f"{word}{random.choice(EMOJIS)}",
        f"{random.choice(EMOJIS)}{word}",
        f"『{word}』",
        f"〖{word}〗",
    ]
    return random.choice(variants)


def generate_local_nicks(name: str, theme_key: str, count: int = 10) -> list[str]:
    """API'siz ishlaydigan ijodiy generator: ism + mavzu so'zlari + bezaklar."""
    theme = THEMES.get(theme_key, THEMES["gaming"])
    clean = _clean_name(name)
    base_words = theme["words"][:]
    random.shuffle(base_words)

    # ismning harflaridan qisqartmalar: Ali -> ALI, AliXon
    nicks = []
    patterns = [
        lambda w: f"{clean}{w[:4]}",
        lambda w: f"{w}{clean}",
        lambda w: f"{clean}『{w}』",
        lambda w: f"{w}〘{clean}〙",
        lambda w: f"{clean} x {w}",
        lambda w: f"{clean}{random.randint(1, 99)}",
        lambda w: f"{w}{clean[:1]}",
        lambda w: f"{clean[:4]}{w}",
    ]
    for i, w in enumerate(base_words[:count]):
        nick = patterns[i % len(patterns)](w)
        if random.random() < 0.6:
            nick = _stylize(nick)
        nicks.append(nick)

    # har doim bir nechta sof ism varianti ham qo'shamiz
    extra = [
        f"꧁{clean}꧂",
        f"『{clean}』{random.choice(EMOJIS)}",
        f"{clean} ༄ {random.choice(theme['words'])}",
        f"亗 {clean} 亗",
        f"{random.choice(DECO)}{clean}{random.choice(EMOJIS)}",
    ]
    nicks.extend(extra[: max(0, count - len(nicks))])
    return nicks[:count]


def get_theme_buttons() -> list[tuple]:
    """[(callback_data, label_uz, emoji), ...]"""
    return [
        (f"aigen_{key}", theme["emoji_uz"], theme["label_uz"])
        for key, theme in THEMES.items()
    ]


# ------------------------------------------------------------------
# Gemini AI (haqiqiy ijodiy niklar)
# ------------------------------------------------------------------

async def generate_ai_nicks(name: str, theme_key: str, language: str = "uz", count: int = 10) -> list[str] | None:
    """Gemini orqali ijodiy niklar. Xato/limit bo'lsa None qaytaradi."""
    if not GEMINI_API_KEY:
        return None

    theme = THEMES.get(theme_key, THEMES["gaming"])
    lang_name = {"uz": "uzbek", "us": "english", "ru": "russian"}.get(language, "uzbek")
    prompt = (
        f"Create {count} creative, stylish gaming/social media nicknames based on the "
        f"name '{name}' with a '{theme_key}' vibe. Mix the person's name with creative words, "
        f"use unicode decorations like ꧁ 亗 ༄ 乂 and rare emojis. 1-2 word styles, "
        f"each under 22 characters. Reply ONLY with the nicknames, one per line, "
        f"no numbers, no explanations. Descriptions must feel natural in {lang_name} culture."
    )

    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=_SSL)) as session:
            async with session.post(
                f"{GEMINI_URL}?key={GEMINI_API_KEY}",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=25),
            ) as resp:
                if resp.status != 200:
                    logger.warning(f"Gemini API {resp.status}: {(await resp.text())[:200]}")
                    return None
                data = await resp.json()

        text = data["candidates"][0]["content"]["parts"][0]["text"]
        nicks = [line.strip().lstrip("0123456789.-) ") for line in text.splitlines()]
        nicks = [n for n in nicks if n][:count]
        return nicks if nicks else None
    except Exception as e:
        logger.warning(f"Gemini API xato: {e}")
        return None


async def generate_nicks(name: str, theme_key: str, language: str = "uz", count: int = 10) -> tuple[list[str], str]:
    """Asosiy kirish nuqtasi: (nicks, source) qaytaradi. source: 'ai' yoki 'local'."""
    nicks = await generate_ai_nicks(name, theme_key, language, count)
    if nicks:
        return nicks, "ai"
    return generate_local_nicks(name, theme_key, count), "local"


def format_nicks_list(nicks: list[str], title: str) -> str:
    lines = [f"<b>{html.escape(title)}</b>\n"]
    for i, nick in enumerate(nicks, 1):
        lines.append(f"{i}. <code>{html.escape(nick)}</code>")
    return "\n".join(lines)
