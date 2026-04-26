import secrets
import random
import string
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import StateFilter
from aiogram import F
from loader import dp, db
import json
import html

class PwdStates(StatesGroup):
    WaitingForBase = State()

def scramble_word(word):
    """Scrambles a word aggressively with symbols and numbers as requested"""
    symbols = "!@#$%^&*"
    digits = "0123456789"
    result = ""
    for char in word:
        # Add random symbols/digits before or after each char
        chance = random.random()
        if chance < 0.3:
            result += random.choice(symbols)
        elif chance < 0.6:
            result += random.choice(digits)
            
        # Swap case occasionally
        if char.isalpha() and random.random() > 0.7:
            char = char.swapcase()
            
        result += char
        
        # Add another symbol occasionally
        if random.random() > 0.7:
            result += random.choice(symbols)
            
    # Ensure it's not too short
    while len(result) < 12:
        result += random.choice(symbols + digits + string.ascii_letters)
        
    return result

def generate_strong_password(length=14):
    """Generate a truly strong random password"""
    chars = string.ascii_letters + string.digits + "!@#$%^&*()_+-="
    password = [
        random.choice(string.ascii_lowercase),
        random.choice(string.ascii_uppercase),
        random.choice(string.digits),
        random.choice("!@#$%^&*")
    ]
    password += [random.choice(chars) for _ in range(length - 4)]
    random.shuffle(password)
    return "".join(password)

def load_texts():
    with open("languages.json", "r", encoding="utf-8") as f:
        return json.load(f)

texts = load_texts()

@dp.message(F.text.in_(["🔐 Password Generator", "🔐 Password Generator", "🔐 Генератор паролей"]), StateFilter("*"))
async def password_generator_handler(message: Message, state: FSMContext):
    await state.clear()
    telegram_id = message.from_user.id
    user = db.select_user_by_id(telegram_id=telegram_id)
    language = user[2] if user else "uz"
    
    welcome = {
        "uz": "🔐 <b>Xavfsiz Parol Generatori</b>\n\nIsmingizni yoki biror so'z yuboring, men uni daxshatli darajada kuchli parolga aylantirib beraman! \n",
        "us": "🔐 <b>Secure Password Generator</b>\n\nSend a word for basis and I'll make it ultra-strong!",
        "ru": "🔐 <b>Генератор паролей</b>\n\nОтправьте слово и я сделаю его супер-надежным!"
    }
    
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(text="⚡ Tasodifiy parol", callback_data="pwd_random"))
    keyboard.row(InlineKeyboardButton(text=texts[language].get("back_button", "Back"), callback_data="back_to_menu"))
    
    # Using a more direct and reliable image URL
    image = "https://img.freepik.com/free-photo/security-safety-concept-with-lock_23-2148128509.jpg"
    
    try:
        await message.answer_photo(
            photo=image, 
            caption=welcome.get(language, welcome["us"]), 
            reply_markup=keyboard.as_markup(), 
            parse_mode="HTML"
        )
    except Exception:
        # Fallback to text if image fails
        await message.answer(
            welcome.get(language, welcome["us"]), 
            reply_markup=keyboard.as_markup(), 
            parse_mode="HTML"
        )
    
    await state.set_state(PwdStates.WaitingForBase)

@dp.message(PwdStates.WaitingForBase)
async def handle_pwd_base(message: Message, state: FSMContext):
    if not message.text:
        return
        
    if message.text.startswith("📝") or message.text.startswith("🎮") or message.text.startswith("🕵️") or message.text.startswith("📙") or message.text.startswith("/"): 
        return

    base_word = message.text.strip()
    password = scramble_word(base_word)
    
    # Escape HTML to prevent parsing issues with generated symbols like & or <
    safe_pwd = html.escape(password)
    
    response = {
        "uz": f"✅ <b>Siz uchun yaratilgan kuchli parol:</b>\n\n<code>{safe_pwd}</code>\n\n👆 Nusxa olish uchun parolni ustiga bosing!",
        "us": f"✅ <b>Your smart mixed password:</b>\n\n<code>{safe_pwd}</code>\n\n👆 Click the password to copy!",
        "ru": f"✅ <b>Ваш перемешанный пароль:</b>\n\n<code>{safe_pwd}</code>\n\n👆 Нажмите, чтобы скопировать!"
    }
    
    telegram_id = message.from_user.id
    user = db.select_user_by_id(telegram_id=telegram_id)
    language = user[2] if user else "uz"
    
    await message.answer(response.get(language, response["us"]), parse_mode="HTML")
    await state.set_state(PwdStates.WaitingForBase) 

@dp.callback_query(lambda c: c.data == "pwd_random")
async def pwd_random_handler(callback: CallbackQuery):
    password = generate_strong_password(16)
    safe_pwd = html.escape(password)
    await callback.message.answer(f"⚡ <b>Tasodifiy parol:</b>\n\n<code>{safe_pwd}</code>\n\n👆 Nusxa olish uchun ustiga bosing!", parse_mode="HTML")
    await callback.answer()
