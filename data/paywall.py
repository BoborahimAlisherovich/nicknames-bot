"""Telegram Stars orqali pullik funksiyalar.

- Bir marta to'langach, funksiya o'sha foydalanuvchi uchun DOIMIY ochiladi.
- Ba'zi funksiyalarda bepul limit bor (masalan AI Studio: 3 ta so'rov).
- ADMIN_FREE = False — to'lov HAMMA uchun majburiy (admin ham sinab ko'rishi uchun).
Narx va limitlarni shu fayldan o'zgartiring.
"""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice

from loader import ADMINS, bot, db

ADMIN_FREE = False

# kalit: (narx ⭐, sarlavha, tavsif)
ITEMS = {
    "nick_premium": (10, "👑 Premium nik dizaynlari", "Cheksiz premium nik dizaynlari (shrift + bezak)"),
    "stickers_all": (10, "⭐ Barcha stikerlar", "Stikerlar kolleksiyasi va trend paketlarning barcha sahifalari"),
    "ai_pro": (10, "🤖 AI Pro", "AI Studio va AI yordamchidan cheksiz foydalanish"),
}

# Bepul limitlar: hisoblagich nomi -> (qaysi item ochadi, nechta bepul)
FREE = {
    "ai_studio": ("ai_pro", 3),   # AI Studio — 3 ta bepul so'rov
    "ai_chat": ("ai_pro", 10),    # AI yordamchi — 10 ta bepul xabar
}

# Sahifalash: nechta sahifa bepul (4 => 3 marta ➡️ bosish bepul, 4-bosishda to'lov)
FREE_PAGES = 4

_ready = False


def _ensure():
    global _ready
    if _ready:
        return
    db.execute("CREATE TABLE IF NOT EXISTS Unlocks(user_id INTEGER, item TEXT, paid INTEGER, charge_id TEXT,"
               " PRIMARY KEY(user_id, item))", commit=True)
    db.execute("CREATE TABLE IF NOT EXISTS Usage(user_id INTEGER, counter TEXT, used INTEGER DEFAULT 0,"
               " PRIMARY KEY(user_id, counter))", commit=True)
    _ready = True


def has(user_id: int, item: str) -> bool:
    if ADMIN_FREE and user_id in ADMINS:
        return True
    _ensure()
    return bool(db.execute("SELECT 1 FROM Unlocks WHERE user_id=? AND item=?", (user_id, item), fetchone=True))


def grant(user_id: int, item: str, paid: int, charge_id: str):
    _ensure()
    db.execute("INSERT OR REPLACE INTO Unlocks(user_id, item, paid, charge_id) VALUES(?, ?, ?, ?)",
               (user_id, item, paid, charge_id), commit=True)


def used(user_id: int, counter: str) -> int:
    _ensure()
    row = db.execute("SELECT used FROM Usage WHERE user_id=? AND counter=?", (user_id, counter), fetchone=True)
    return row[0] if row else 0


def left(user_id: int, counter: str) -> int | None:
    """Qolgan bepul urinishlar. None = cheksiz (to'langan)."""
    item, free = FREE[counter]
    if has(user_id, item):
        return None
    return max(0, free - used(user_id, counter))


def consume(user_id: int, counter: str):
    _ensure()
    db.execute("INSERT INTO Usage(user_id, counter, used) VALUES(?, ?, 1) "
               "ON CONFLICT(user_id, counter) DO UPDATE SET used = used + 1", (user_id, counter), commit=True)


def offer_kb(item: str, back_cb: str) -> InlineKeyboardMarkup:
    price = ITEMS[item][0]
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"⭐ {price} Stars bilan ochish", callback_data=f"unlock:{item}", style="success")],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data=back_cb, style="danger")],
    ])


def offer_text(item: str, extra: str = "") -> str:
    price, title, desc = ITEMS[item]
    return (f"🔒 <b>{title}</b>\n\n{desc} — doimiy ochiladi.\n"
            f"{extra}\n💰 Narxi: <b>{price} ⭐</b> (bir martalik to'lov)\n"
            "To'lovdan so'ng darhol ochiladi.")


async def send_invoice(chat_id: int, item: str):
    price, title, desc = ITEMS[item]
    await bot.send_invoice(chat_id, title=title, description=desc, payload=f"unlock:{item}",
                           currency="XTR", provider_token="", prices=[LabeledPrice(label=title, amount=price)])
