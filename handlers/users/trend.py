from aiogram.types import Message
from loader import dp, db
from aiogram.filters import Command
from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from keyboard_buttons import admin_keyboard
import logging
from aiogram import F
from handlers.users.emojelar import allah_names, top_nick
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import StateFilter
from aiogram import types
import json
import html

def load_texts():
    with open("languages.json", "r", encoding="utf-8") as f:
        return json.load(f)

texts = load_texts()

def is_guied_us_message(message_text):
    possible_texts = [
        texts.get(lang, {}).get("menu", {}).get("menu_button_4", "")
        for lang in texts
    ]
    return message_text in possible_texts


@dp.message(lambda message: is_guied_us_message(message.text), StateFilter("*"))
async def guied_us(message: Message, state: FSMContext):
    telegram_id = message.from_user.id
    user = db.select_user_by_id(telegram_id=telegram_id)
    language = user[2] if user else "uz"
    
    text = texts.get(language, {}).get("guide", "Guide not found.")
    await message.answer(text, parse_mode='html')
    await state.clear()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

NAMES_PER_PAGE = 1 
NAMES_PER_PAGES = 10 

def get_pagination_keyboard(current_page):
    buttons = []
    if current_page > 0:
        buttons.append(InlineKeyboardButton(text="⬅️", callback_data=f"prev:{current_page - 1}"))
    if (current_page + 1) * NAMES_PER_PAGE < len(allah_names):
        buttons.append(InlineKeyboardButton(text="➡️", callback_data=f"next:{current_page + 1}"))
    return InlineKeyboardMarkup(inline_keyboard=[buttons])


def get_names_page(page):
    start = page * NAMES_PER_PAGE
    end = start + NAMES_PER_PAGE
    return "\n\n".join(map(str, allah_names[start:end]))

def get_pagination_keyboardd(current_pages):
    buttons = []
    if current_pages > 0:
        buttons.append(InlineKeyboardButton(text="⬅️", callback_data=f"prev1:{current_pages - 1}"))
    if (current_pages + 1) * NAMES_PER_PAGES < len(top_nick):
        buttons.append(InlineKeyboardButton(text="➡️", callback_data=f"next1:{current_pages + 1}"))
    return InlineKeyboardMarkup(inline_keyboard=[buttons])

def get_names_pages(page, telegram_id):
    start = page * NAMES_PER_PAGES
    end = start + NAMES_PER_PAGES
    paginated_nicknamess = top_nick[start:end]

    user = db.select_user_by_id(telegram_id=telegram_id)
    language = user[2] if user else "uz"
    text = texts.get(language, {}).get("invisible_nick", "Invisible")

    return "\n\n\n".join([
        f"{idx + start + 1}- <code>{html.escape(nicks)}</code> <i>{text if idx + start == 0 else ''}</i>"
        for idx, nicks in enumerate(paginated_nicknamess)
    ])


@dp.message(F.text.in_(["🔥 Mashhur Stikerlar", "🔥 Popular Stickers", "🔥 Популярные стикеры"]), StateFilter("*"))
async def send_names(message: types.Message, state: FSMContext):
    await state.clear()
    current_page = 0
    telegram_id = message.from_user.id
    user = db.select_user_by_id(telegram_id)
    language = user[2] if user else "uz"
    
    sticker_title = texts.get(language, {}).get("sticker_title", "🔥 Popular Stickers")
    
    # Use HTML for better stability
    sticker_data = get_names_page(current_page)
    await message.answer(
        text=f"<b>{sticker_title}</b>\n\n{sticker_data}",
        reply_markup=get_pagination_keyboard(current_page),
        parse_mode="HTML"
    )

@dp.callback_query(lambda c: c.data and (c.data.startswith('next:') or c.data.startswith('prev:')))
async def process_pagination(callback_query: types.CallbackQuery, state: FSMContext):
    action, page = callback_query.data.split(':')
    current_page = int(page)
    telegram_id = callback_query.from_user.id
    user = db.select_user_by_id(telegram_id)
    language = user[2] if user else "uz"
    
    sticker_title = texts.get(language, {}).get("sticker_title", "🔥 Popular Stickers")
    sticker_data = get_names_page(current_page)
    
    try:
        await callback_query.message.edit_text(
            text=f"<b>{sticker_title}</b>\n\n{sticker_data}",
            reply_markup=get_pagination_keyboard(current_page),
            parse_mode="HTML"
        )
    except:
        pass
    await callback_query.answer()

@dp.message(F.text.in_(["✨ Top nik", "✨ Top Nick", "✨ Топ ник"]), StateFilter("*"))
async def send_namess(message: types.Message, state: FSMContext):
    await state.clear()
    current_page = 0
    telegram_id = message.from_user.id
    user = db.select_user_by_id(telegram_id)
    language = user[2] if user else "uz"
    
    nick_title = texts.get(language, {}).get("nick_title", "✨ Top Nick")
    
    await message.answer(
        text=f"<b>{nick_title}</b>\n\n" + get_names_pages(current_page, telegram_id),
        reply_markup=get_pagination_keyboardd(current_page),
        parse_mode="HTML"
    )

@dp.callback_query(lambda c: c.data and (c.data.startswith('next1:') or c.data.startswith('prev1:')))
async def process_paginations(callback_query: types.CallbackQuery, state: FSMContext):
    action, page = callback_query.data.split(':')
    current_page = int(page)
    telegram_id = callback_query.from_user.id
    user = db.select_user_by_id(telegram_id)
    language = user[2] if user else "uz"
    
    nick_title = texts.get(language, {}).get("nick_title", "✨ Top Nick")
    
    try:
        await callback_query.message.edit_text(
            text=f"<b>{nick_title}</b>\n\n" + get_names_pages(current_page, telegram_id),
            reply_markup=get_pagination_keyboardd(current_page),
            parse_mode="HTML"
        )
    except:
        pass
    await callback_query.answer()