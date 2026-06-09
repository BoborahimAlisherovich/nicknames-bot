from aiogram.types import CallbackQuery
from loader import dp, db
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
import json
from keyboard_buttons.admin_keyboard import create_menu_buttons

def load_texts():
    with open("languages.json", "r", encoding="utf-8") as f:
        return json.load(f)

texts = load_texts()

# Handle back to main menu
@dp.callback_query(lambda c: c.data == "back_to_menu")
async def back_to_main_menu(callback: CallbackQuery, state: FSMContext):
    # Clear all states completely
    await state.clear()
    await state.set_data({})
    
    telegram_id = callback.from_user.id
    user = db.select_user_by_id(telegram_id=telegram_id)
    language = user[2] if user else "uz"
    
    full_name = callback.from_user.full_name
    
    # Send enhanced welcome message
    welcome_text = texts.get(language, {}).get("welcome_message", "Welcome!")
    
    await callback.message.edit_text(
        text=welcome_text.format(full_name=full_name),
        parse_mode='HTML',
        reply_markup=create_menu_buttons(language)
    )
    await callback.answer()

# Handle premium features navigation
@dp.callback_query(lambda c: c.data == "premium_features")
async def premium_features_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    
    telegram_id = callback.from_user.id
    user = db.select_user_by_id(telegram_id=telegram_id)
    language = user[2] if user else "uz"
    
    keyboard = InlineKeyboardBuilder()
    
    premium_text = {
        "uz": "👑 Premium niklar",
        "us": "👑 Premium Nicks",
        "ru": "👑 Премиум ники"
    }

    fonts_text = {
        "uz": "🎨 Chiroyli shriftlar",
        "us": "🎨 Stylish Fonts",
        "ru": "🎨 Стильные шрифты"
    }
    
    keyboard.row(
        InlineKeyboardButton(text=premium_text.get(language, premium_text["us"]), callback_data="premium_nicknames_main"),
        InlineKeyboardButton(text=fonts_text.get(language, fonts_text["us"]), callback_data="premium_fonts_main")
    )
    
    # Back button
    back_text = texts.get(language, {}).get("back_button", "♻️ Orqaga")
    keyboard.row(InlineKeyboardButton(text=back_text, callback_data="back_to_menu"))
    
    features_text = {
        "uz": "🌟 Premium xususiyatlar:\n\n• 🎨 100+ stylish shriftlar\n• 👑 13+ premium nik kategoriyalari\n• 🔥 Trending 2026 uslublari\n• 💎 Gaming, TikTok, Anime va boshqalar\n• ⚡ Bitta bosishda yaratish\n• 🎯 Emoji reaktsiyalar va stikerlar",
        "us": "🌟 Premium features:\n\n• 🎨 100+ stylish fonts\n• 👑 13+ premium nickname categories\n• 🔥 Trending 2026 styles\n• 💎 Gaming, TikTok, Anime & more\n• ⚡ One-click creation\n• 🎯 Emoji reactions and stickers",
        "ru": "🌟 Премиум функции:\n\n• 🎨 100+ стильных шрифтов\n• 👑 13+ премиум категорий ников\n• 🔥 Трендовые стили 2026\n• 💎 Игровые, TikTok, Аниме и другие\n• ⚡ Создание в одно нажатие\n• 🎯 Реакции эмодзи и стикеры"
    }
    
    await callback.message.edit_text(
        text=features_text.get(language, features_text["us"]),
        reply_markup=keyboard.as_markup()
    )
    await callback.answer()

# Handle premium nicknames main
@dp.callback_query(lambda c: c.data == "premium_nicknames_main")
async def premium_nicknames_main(callback: CallbackQuery, state: FSMContext):
    from .premium_handler import premium_nicknames_handler
    
    # Create a mock message object
    class MockMessage:
        def __init__(self, from_user, text):
            self.from_user = from_user
            self.text = text
    
    mock_message = MockMessage(callback.from_user, "👑 Premium Nicks")
    await premium_nicknames_handler(mock_message, state)

# Handle premium fonts main  
@dp.callback_query(lambda c: c.data == "premium_fonts_main")
async def premium_fonts_main(callback: CallbackQuery, state: FSMContext):
    from .premium_handler import premium_fonts_handler
    
    # Create a mock message object
    class MockMessage:
        def __init__(self, from_user, text):
            self.from_user = from_user
            self.text = text
    
    mock_message = MockMessage(callback.from_user, "🎨 Stylish Fonts")
    await premium_fonts_handler(mock_message, state)
