"""Telegram Stars orqali pullik funksiyalarni ochish.

Bir marta to'langach, funksiya o'sha foydalanuvchi uchun DOIMIY ochiladi.
Adminlar uchun hammasi bepul. Narxlar shu yerda o'zgartiriladi.
"""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice

from loader import ADMINS, bot, db

ITEMS = {
    "nick_premium": (10, "👑 Premium nik dizaynlari", "Cheksiz premium nik dizaynlari (shrift + bezak) — doimiy ochiladi"),
    "stickers_all": (10, "⭐ Barcha stikerlar", "Stikerlar kolleksiyasining barcha sahifalari — doimiy ochiladi"),
}


def _ensure():
    db.execute("CREATE TABLE IF NOT EXISTS Unlocks(user_id INTEGER, item TEXT, paid INTEGER, charge_id TEXT,"
               " PRIMARY KEY(user_id, item))", commit=True)


def has(user_id: int, item: str) -> bool:
    if user_id in ADMINS:
        return True
    _ensure()
    return bool(db.execute("SELECT 1 FROM Unlocks WHERE user_id=? AND item=?", (user_id, item), fetchone=True))


def grant(user_id: int, item: str, paid: int, charge_id: str):
    _ensure()
    db.execute("INSERT OR REPLACE INTO Unlocks(user_id, item, paid, charge_id) VALUES(?, ?, ?, ?)",
               (user_id, item, paid, charge_id), commit=True)


def offer_kb(item: str, back_cb: str) -> InlineKeyboardMarkup:
    price = ITEMS[item][0]
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"⭐ {price} Stars bilan ochish", callback_data=f"unlock:{item}", style="success")],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data=back_cb, style="danger")],
    ])


def offer_text(item: str) -> str:
    price, title, desc = ITEMS[item]
    return (f"🔒 <b>{title}</b>\n\n{desc}.\n\n"
            f"💰 Narxi: <b>{price} ⭐</b> (bir martalik to'lov)\n"
            "To'lovdan so'ng darhol ochiladi.")


async def send_invoice(chat_id: int, item: str):
    price, title, desc = ITEMS[item]
    await bot.send_invoice(chat_id, title=title, description=desc, payload=f"unlock:{item}",
                           currency="XTR", provider_token="", prices=[LabeledPrice(label=title, amount=price)])
