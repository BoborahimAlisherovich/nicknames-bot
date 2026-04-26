from aiogram.types import Message, InlineKeyboardButton
from loader import dp, db
from aiogram.filters import Command, StateFilter
from aiogram import types, F
from aiogram.fsm.context import FSMContext
from handlers.users.nick_generator import nick_generator
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.state import State, StatesGroup
from keyboard_buttons.admin_keyboard import create_back_button, create_menu_buttons, texts
import html

class NickState(StatesGroup):
    WaitingForName = State()

# Fetch button texts from languages.json
nick_button_texts = [
    texts["uz"]["menu"]["menu_button_11"],
    texts["us"]["menu"]["menu_button_11"],
    texts["ru"]["menu"]["menu_button_11"]
]

# Use state="*" to ensure the menu button works regardless of current state
@dp.message(F.text.in_(nick_button_texts), StateFilter("*"))
async def ask_nick_name(message: types.Message, state: FSMContext):
    # Clear any previous state
    await state.clear()
    await state.set_state(NickState.WaitingForName)
    
    telegram_id = message.from_user.id
    user = db.select_user_by_id(telegram_id=telegram_id)
    language = user[2] if user else "uz"
    
    prompt = {
        "uz": "✍️ Iltimos, nick yaratish uchun ismingizni yozib yuboring:",
        "us": "✍️ Please enter your name to create a nick:",
        "ru": "✍️ Пожалуйста, введите свое имя для создания ника:"
    }
    
    await message.answer(
        prompt.get(language, prompt["us"]),
        reply_markup=create_back_button(language)
    )

@dp.message(NickState.WaitingForName)
async def generate_short_nicks(message: types.Message, state: FSMContext):
    name = message.text
    telegram_id = message.from_user.id
    user = db.select_user_by_id(telegram_id=telegram_id)
    language = user[2] if user else "uz"
    
    # Check for back button
    back_btn_text = texts[language]["back_button"]
    if name == back_btn_text:
        await state.clear()
        home_msg = {"uz": "🏠 Bosh menyu", "us": "🏠 Home page", "ru": "🏠 Главное меню"}
        await message.answer(home_msg.get(language, home_msg["us"]), reply_markup=create_menu_buttons(language))
        return

    # Filter out commands
    if name.startswith('/'):
        # If user starts over, let it proceed to next handlers
        await state.clear()
        return

    # Update data
    await state.update_data(name=name)
    
    # Generate
    nicknames = nick_generator(name=name)
    
    if not nicknames:
        await message.answer("❌ Natija topilmadi.")
        return

    page_size = 10
    page_num = 0
    total_pages = (len(nicknames) + page_size - 1) // page_size
    paginated = nicknames[page_num * page_size:(page_num + 1) * page_size]
    
    res_title = {
        "uz": "✨ <b>Siz uchun natijalar:</b>",
        "us": "✨ <b>Results for you:</b>",
        "ru": "✨ <b>Результаты для вас:</b>"
    }
    
    text = f"{res_title.get(language, res_title['us'])}\n\n"
    for idx, nick in enumerate(paginated, start=page_num * page_size + 1):
        safe_nick = html.escape(nick.strip())
        text += f"{idx}. <code>{safe_nick}</code>\n\n"
    
    markup = InlineKeyboardBuilder()
    if total_pages > 1:
        if page_num < total_pages - 1:
            markup.add(InlineKeyboardButton(text="➡️", callback_data=f"short_page_{page_num+1}"))
    
    await message.answer(text, reply_markup=markup.as_markup(), parse_mode="HTML")

@dp.callback_query(lambda c: c.data.startswith("short_page_"))
async def handle_short_page(callback_query: types.CallbackQuery, state: FSMContext):
    data = callback_query.data.split("_")
    page_num = int(data[2])
    user_data = await state.get_data()
    name = user_data.get('name')
    
    if not name:
        # If name is lost (e.g. restart), we can't paginate
        await callback_query.answer("❌ Ma'lumot vaqti o'tib ketgan.")
        return

    nicknames = nick_generator(name=name)
    user = db.select_user_by_id(telegram_id=callback_query.from_user.id)
    language = user[2] if user else "uz"

    page_size = 10
    total_pages = (len(nicknames) + page_size - 1) // page_size
    paginated = nicknames[page_num * page_size:(page_num + 1) * page_size]
    
    page_title = {
        "uz": f"✨ <b>Natijalar (Sahifa {page_num + 1}):</b>\n\n",
        "us": f"✨ <b>Results (Page {page_num + 1}):</b>\n\n",
        "ru": f"✨ <b>Результаты (Страница {page_num + 1}):</b>\n\n"
    }

    text = page_title.get(language, page_title["us"])
    for idx, nick in enumerate(paginated, start=page_num * page_size + 1):
        safe_nick = html.escape(nick.strip())
        text += f"{idx}. <code>{safe_nick}</code>\n\n"

    markup = InlineKeyboardBuilder()
    if page_num > 0:
        markup.add(InlineKeyboardButton(text="⬅️", callback_data=f"short_page_{page_num-1}"))
    if page_num < total_pages - 1:
        markup.add(InlineKeyboardButton(text="➡️", callback_data=f"short_page_{page_num+1}"))

    await callback_query.message.edit_text(text, reply_markup=markup.as_markup(), parse_mode="HTML")
    await callback_query.answer()