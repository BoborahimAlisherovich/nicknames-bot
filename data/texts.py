"""Markaziy matnlar yuklovchisi.

languages.json butun loyihada BIR marta o'qiladi va keshlanadi.
Ilgari 11 ta fayl har birida alohida open("languages.json") chaqirilardi —
endiga yagona manba sifatida shu modul ishlatiladi.
"""
import json
import logging
import os

logger = logging.getLogger(__name__)

_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "languages.json")

_cache: dict | None = None


def get_texts() -> dict:
    """Keshlangan matnlarni qaytaradi (birinchi chaqiruvda o'qiydi)."""
    global _cache
    if _cache is None:
        try:
            with open(_PATH, "r", encoding="utf-8") as f:
                _cache = json.load(f)
        except Exception as e:
            logger.error(f"languages.json o'qishda xato: {e}")
            _cache = {}
    return _cache


def reload_texts() -> dict:
    """languages.json o'zgarsa, botni qayta ishga tushirmasdan yangilaydi."""
    global _cache
    with open(_PATH, "r", encoding="utf-8") as f:
        _cache = json.load(f)
    logger.info("languages.json qayta yuklandi")
    return _cache
