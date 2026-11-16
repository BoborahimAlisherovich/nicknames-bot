"""Gemini bilan yagona, tez ulanish.

Tezlik uchun:
- bitta umumiy HTTP sessiya (har so'rovda yangi ulanish ochilmaydi);
- "fikrlash" (thinking) o'chiriladi — javob 25s o'rniga ~2s da keladi;
- har model uchun qisqa timeout, band bo'lsa darhol keyingisiga o'tiladi.
"""
import logging
import ssl

import aiohttp
import certifi

from data import settings
from data.config import GEMINI_MODELS

log = logging.getLogger(__name__)
_SSL = ssl.create_default_context(cafile=certifi.where())
_session: aiohttp.ClientSession | None = None

SYSTEM = (
    "Sen professional o'zbek tilidagi kreativ yordamchisan. Qoidalar:\n"
    "- Foydalanuvchi qaysi tilda yozsa, o'sha tilda javob ber (odatda o'zbekcha, lotin yozuvida).\n"
    "- Markdown belgilarini ishlatma (* # ` yo'q). Raqamli ro'yxat va mos emojilardan foydalan.\n"
    "- Aniq, foydali va o'qishga qulay yoz; keraksiz kirish so'zlarisiz darhol javobga o't.\n"
    "- Sifatli, noyob va ijodiy variantlar ber, bir xil narsani takrorlama."
)


async def _get_session() -> aiohttp.ClientSession:
    global _session
    if _session is None or _session.closed:
        _session = aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=_SSL))
    return _session


async def ask(prompt: str | None = None, history: list[dict] | None = None,
              system: str = SYSTEM, max_tokens: int = 1500, temperature: float = 0.9) -> str | None:
    """prompt — bitta savol; history — [{"role": "user"/"model", "text": ...}] suhbat."""
    key = settings.gemini_key()
    if not key:
        return None
    contents = [{"role": h["role"], "parts": [{"text": h["text"]}]} for h in (history or [])]
    if prompt:
        contents.append({"role": "user", "parts": [{"text": prompt}]})
    s = await _get_session()
    for model in GEMINI_MODELS:
        gc = {"temperature": temperature, "maxOutputTokens": max_tokens}
        if "lite" not in model:
            gc["thinkingConfig"] = {"thinkingBudget": 0}
        body = {"systemInstruction": {"parts": [{"text": system}]}, "contents": contents, "generationConfig": gc}
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        try:
            async with s.post(url, params={"key": key}, json=body, timeout=aiohttp.ClientTimeout(total=20)) as r:
                data = await r.json(content_type=None)
                if r.status != 200:
                    log.warning("Gemini %s: %s %s", model, r.status, str(data)[:150])
                    continue
                parts = data["candidates"][0]["content"]["parts"]
                text = "".join(p.get("text", "") for p in parts).strip()
                if text:
                    return text.replace("**", "").replace("##", "")
        except Exception as e:
            log.warning("Gemini %s xato: %s", model, e)
    return None
