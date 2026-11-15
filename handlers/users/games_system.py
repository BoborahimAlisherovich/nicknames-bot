"""Brauzer o'yinlari (Poki) — Telegram ichida WebApp sifatida ochiladi.

O'yinlar ro'yxati data/games.json da: har bir rasm va havola tekshirilgan.
"""
import html
import json
import logging
import os
import random

from aiogram import F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import (CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup,
                           InputMediaPhoto, Message, WebAppInfo)

from data.texts import get_texts
from loader import db, dp

logger = logging.getLogger(__name__)
texts = get_texts()

_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "games.json")
with open(_PATH, encoding="utf-8") as f:
    GAMES: list[dict] = json.load(f)

CATEGORIES = sorted({g["category"] for g in GAMES}, key=lambda c: [g["category"] for g in GAMES].index(c))


def _lang(user_id: int) -> str:
    user = db.select_user_by_id(telegram_id=user_id)
    return user[2] if user else "uz"


def _ids(cat: int) -> list[int]:
    """cat = -1 barcha o'yinlar, aks holda CATEGORIES indeksi."""
    if cat < 0:
        return list(range(len(GAMES)))
    return [i for i, g in enumerate(GAMES) if g["category"] == CATEGORIES[cat]]


def card(pos: int, cat: int, lang: str):
    ids = _ids(cat)
    pos %= len(ids)
    g = GAMES[ids[pos]]
    caption = (f"🎮 <b>{html.escape(g['name'])}</b>\n\n"
               f"📝 {html.escape(g['description'])}\n\n"
               f"📂 {html.escape(g['category'])}\n"
               f"📄 {pos + 1}/{len(ids)}\n\n"
               "📱 Telegram ichida ochiladi — yuklab olish shart emas!")
    b = InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [b(text="▶️ O'ynash", web_app=WebAppInfo(url=g["url"]), style="success")],
        [b(text="⬅️", callback_data=f"gm:{cat}:{pos - 1}", style="primary"),
         b(text="🎲 Tasodifiy", callback_data=f"gm:{cat}:r"),
         b(text="➡️", callback_data=f"gm:{cat}:{pos + 1}", style="primary")],
        [b(text="📂 Kategoriyalar", callback_data="gm:cats")],
        [b(text=texts.get(lang, {}).get("back_button", "♻️ Asosiy menyu"), callback_data="back_to_menu", style="danger")],
    ])
    return g["image"], caption, kb


def cats_kb():
    b = InlineKeyboardButton
    rows = [[b(text=f"🌐 Barchasi ({len(GAMES)})", callback_data="gm:-1:0", style="success")]]
    pair = []
    for i, c in enumerate(CATEGORIES):
        pair.append(b(text=f"{c} ({len(_ids(i))})", callback_data=f"gm:{i}:0", style="primary"))
        if len(pair) == 2:
            rows.append(pair)
            pair = []
    if pair:
        rows.append(pair)
    return InlineKeyboardMarkup(inline_keyboard=rows)


@dp.message(F.text.in_(["🎮 O'yinlar", "🎮 Games", "🎮 Игры"]), StateFilter("*"))
async def games_menu_handler(message: Message, state: FSMContext):
    await state.clear()
    photo, caption, kb = card(0, -1, _lang(message.from_user.id))
    try:
        await message.answer_photo(photo=photo, caption=caption, reply_markup=kb)
    except Exception as e:
        logger.warning("O'yin rasmi yuborilmadi: %s", e)
        await message.answer(caption, reply_markup=kb)


@dp.callback_query(F.data == "gm:cats")
async def games_categories(c: CallbackQuery):
    await c.message.answer("📂 <b>Kategoriyani tanlang:</b>", reply_markup=cats_kb())
    await c.answer()


@dp.callback_query(F.data.startswith("gm:"))
async def games_nav(c: CallbackQuery, state: FSMContext):
    await state.clear()
    _, cat, pos = c.data.split(":")
    cat = int(cat)
    pos = random.randrange(len(_ids(cat))) if pos == "r" else int(pos)
    photo, caption, kb = card(pos, cat, _lang(c.from_user.id))
    await c.answer()
    try:
        if c.message.photo:
            await c.message.edit_media(InputMediaPhoto(media=photo, caption=caption), reply_markup=kb)
            return
    except Exception as e:
        logger.warning("edit_media xato: %s", e)
    try:
        await c.message.answer_photo(photo=photo, caption=caption, reply_markup=kb)
    except Exception:
        await c.message.answer(caption, reply_markup=kb)
    if not c.message.photo:
        try:
            await c.message.delete()
        except Exception:
            pass
