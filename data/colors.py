"""Barcha tugmalarni avtomatik rangli qilish (Bot API 9.4 `style`).

loader.py eng boshida import qilinadi. Shundan keyin botdagi HAR QANDAY
InlineKeyboardButton yoki KeyboardButton (builder orqali yaratilganlari ham)
style berilmagan bo'lsa, matniga qarab rang oladi:
  🔴 danger  — orqaga, bekor qilish, o'chirish
  🟢 success — qo'shish, tasdiqlash, o'ynash, yuborish, nusxalash
  🔵 primary / 🟢 success — qolganlari navbatma-navbat (rangbarang ko'rinish uchun)
Qo'lda style berilgan tugmalar o'zgarmaydi.
"""
import zlib

from aiogram.types import InlineKeyboardButton, KeyboardButton

DANGER = ("orqaga", "back", "назад", "bekor", "cancel", "отмена", "o'chir", "ochir", "delete",
          "удал", "🗑", "❌", "♻️", "🔙", "chiqish", "exit", "yopish", "close")
SUCCESS = ("✅", "➕", "qo'sh", "qosh", "add", "добав", "o'ynash", "play", "▶️", "yubor", "send",
           "отправ", "nusx", "copy", "копир", "tasdiq", "confirm", "ha,", "yes", "boshlash", "start",
           "💝", "⭐", "donat")


def pick_style(text: str) -> str:
    t = (text or "").lower()
    if any(w in t for w in DANGER):
        return "danger"
    if any(w in t for w in SUCCESS):
        return "success"
    return "primary" if zlib.crc32(t.encode()) % 3 else "success"


def _patch(cls):
    orig = cls.__init__
    if getattr(orig, "_colored", False):
        return

    def __init__(self, *args, **kwargs):
        if kwargs.get("style") is None:
            kwargs["style"] = pick_style(kwargs.get("text", ""))
        orig(self, *args, **kwargs)

    __init__._colored = True
    cls.__init__ = __init__


_patch(InlineKeyboardButton)
_patch(KeyboardButton)
