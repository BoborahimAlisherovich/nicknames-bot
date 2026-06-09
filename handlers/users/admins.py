
from aiogram.types import Message
from loader import dp, bot, ADMINS, db
from aiogram.fsm.context import FSMContext
from states.bulimlar import AdminStates
from aiogram.types import CallbackQuery, ContentType
from keyboard_buttons import admin_keyboard
from aiogram import types
from aiogram import F
from aiogram.filters import StateFilter
import logging
from aiogram.utils.keyboard import InlineKeyboardBuilder
import json
from keyboard_buttons.admin_keyboard import create_menu_buttons,create_back_button

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dp.message(F.text.in_(["♻️ Orqaga", "♻️ Back", "♻️ Назад"]), StateFilter("*"))
async def back_to_menu(message: Message, state: FSMContext):
    await state.clear()
    telegram_id = message.from_user.id
    user = db.select_user_by_id(telegram_id=telegram_id)
    language = user[2] if user else "uz"
    await message.answer(
        texts.get(language, {}).get("welcome_message", "Bosh menyu"),
        reply_markup=create_menu_buttons(language)
    )





def load_texts():
    with open("languages.json", "r", encoding="utf-8") as f:
        return json.load(f)

texts = load_texts()

def is_guied_us_message(message_text):
    possible_texts = [
        texts.get(lang, {}).get("menu", {}).get("menu_button_3", "")
        for lang in texts
    ]
    return message_text in possible_texts

@dp.message(lambda message: is_guied_us_message(message.text), StateFilter("*"))
async def admin_us(message: Message, state: FSMContext):
    await state.clear()
    telegram_id = message.from_user.id

    user = db.select_user_by_id(telegram_id=telegram_id)
    language = "uz" 
    if user:
        language = user[2]
    text = texts.get(language, {}).get("admin_1_t", "Tilga mos matn topilmadi.")

    await message.answer(text, parse_mode='html', reply_markup=create_back_button(language))
    await state.set_state(AdminStates.waiting_for_admin_message)
    

def create_inline_keyboard(user_id):
    keyboard_builder = InlineKeyboardBuilder()
    keyboard_builder.button(
        text="Javob berish", callback_data=f"reply:{user_id}"
    )
    return keyboard_builder.as_markup()


import html as htmlmod

def get_user_link(user_id, first_name):
    safe_name = htmlmod.escape(first_name)
    return f'<a href="tg://user?id={user_id}">{safe_name}</a>'

@dp.message(AdminStates.waiting_for_admin_message, F.content_type.in_([
    ContentType.TEXT, ContentType.AUDIO, ContentType.VOICE, ContentType.VIDEO,
    ContentType.PHOTO, ContentType.ANIMATION, ContentType.STICKER,
    ContentType.LOCATION, ContentType.DOCUMENT, ContentType.CONTACT,
    ContentType.VIDEO_NOTE
]))
async def handle_admin_message(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    user_link = get_user_link(user_id, first_name)
    inline_keyboard = create_inline_keyboard(user_id)

    telegram_id = message.from_user.id
    user = db.select_user_by_id(telegram_id=telegram_id)
    language = user[2] if user else "uz"

    sent_message_text = texts.get(language, {}).get("admin_sent_message", "Xatolik yuz berdi.")

    for admin_id in ADMINS:
        try:
            if message.text:
                await bot.send_message(
                    admin_id,
                    f"Foydalanuvchi: {user_link}\n\nXabar:\n{htmlmod.escape(message.text)}",
                    reply_markup=inline_keyboard
                )
            elif message.photo:
                await bot.send_photo(
                    admin_id,
                    message.photo[-1].file_id,
                    caption=f"Foydalanuvchi: {user_link}\n\nRasm xabar",
                    reply_markup=inline_keyboard
                )
            elif message.voice:
                await bot.send_voice(
                    admin_id,
                    message.voice.file_id,
                    caption=f"Foydalanuvchi: {user_link}\n\nVoice xabar",
                    reply_markup=inline_keyboard
                )
            elif message.video:
                await bot.send_video(
                    admin_id,
                    message.video.file_id,
                    caption=f"Foydalanuvchi: {user_link}\n\nVideo xabar",
                    reply_markup=inline_keyboard
                )
            else:
                await bot.send_message(admin_id, f"Foydalanuvchidan yangi xabar: {user_link}")
        except Exception as e:
            logger.error(f"Xatolik adminga xabar yuborishda: {e}")

    await state.clear()
    await message.answer(sent_message_text, reply_markup=create_menu_buttons(language))


# Handling the reply callback
@dp.callback_query(lambda c: c.data.startswith('reply:'))
async def process_reply_callback(callback_query: CallbackQuery, state: FSMContext):
    user_id = int(callback_query.data.split(":")[1])
    await callback_query.message.answer(
        "Javobingizni yozing. Sizning javobingiz foydalanuvchiga yuboriladi."
    )
    await state.update_data(reply_user_id=user_id)
    await state.set_state(AdminStates.waiting_for_reply_message)
    await callback_query.answer()

# Handle admin's reply to the user
@dp.message(AdminStates.waiting_for_reply_message)
async def handle_admin_reply(message: Message, state: FSMContext):
    if message.text and message.text in ["♻️ Orqaga", "♻️ Back", "♻️ Назад"]:
        await state.clear()
        await back_to_menu(message, state)
        return

    data = await state.get_data()
    user_id = data.get('reply_user_id')

    user = db.select_user_by_id(telegram_id=user_id) if user_id else None
    language = user[2] if user else "uz"

    sent_message_text = texts.get(language, {}).get("admin_reply_message", "Xatolik yuz berdi.")
    if user_id:
        try:
            if message.text:
                await bot.send_message(user_id, f"{sent_message_text}\n{message.text}")
            elif message.voice:
                await bot.send_voice(user_id, message.voice.file_id)
            elif message.photo:
                await bot.send_photo(user_id, message.photo[-1].file_id)
            elif message.video:
                await bot.send_video(user_id, message.video.file_id)
            await state.clear()
            await message.answer("Javob yuborildi!")
        except Exception as e:
            logger.error(f"Javob yuborishda xatolik: {e}")
            await message.reply("Xatolik: Javob yuborishda xato yuz berdi.")
    else:
        await message.reply("Xatolik: Javob yuborish uchun foydalanuvchi topilmadi.")

