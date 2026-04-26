import secrets
import time
from datetime import datetime
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import StateFilter
from aiogram import F
from loader import dp, db
import json

# In-memory storage for non-critical ephemeral data
anonymous_tokens = {} # For statistics/cache
rate_limits = {}

class AnonimStates(StatesGroup):
    AnonimXabarYuborish = State()
    AnonimJavobQaytarish = State()

def generate_anonymous_token(user_id):
    """Generate stateless secure unique token for anonymous messages using hex."""
    return hex(user_id)[2:]

def decode_anonymous_token(token):
    """Retrieve user_id from the hex token."""
    try:
        if token.startswith('anon_'):
            token = token[5:]
        return int(token, 16)
    except Exception:
        return None

def generate_anonymous_link(token):
    """Generate anonymous message link"""
    return f"https://t.me/niknames_new_bot?start=anon_{token}"

def is_rate_limited(user_id):
    """Check if user is rate limited for anonymous messages (5s cooldown)"""
    now = time.time()
    if user_id in rate_limits:
        last_time = rate_limits[user_id]
        if now - last_time < 5:
            return True
    rate_limits[user_id] = now
    return False

def load_texts():
    try:
        with open("languages.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

texts = load_texts()

@dp.message(F.text.in_(["🕵️ Anonymous Msg", "🕵️ Анонимное сообщение", "🕵️ Anonymous Message"]), StateFilter("*"))
async def anonymous_menu_handler(message: Message, state: FSMContext):
    await state.clear()
    telegram_id = message.from_user.id
    user = db.select_user_by_id(telegram_id=telegram_id)
    language = user[2] if user else "uz"
    
    user_token = generate_anonymous_token(telegram_id)
    if user_token not in anonymous_tokens:
        anonymous_tokens[user_token] = {'user_id': telegram_id, 'message_count': 0}
    
    anon_link = generate_anonymous_link(user_token)
    message_count = anonymous_tokens[user_token]['message_count']
    
    anon_texts = {
        "uz": {
            "title": "🕵️ **Anonim Xabarlar Sistemi**",
            "instructions": f"🚀 **Qanday ishlaydi:**\n\n1️⃣ Pastdagi linkni oling va uni kanal hamda guruhlarga yuboring.\n2️⃣ Ular sizning havola orqali sizga anonim tarzda xabarlar yuborishadi.\n3️⃣ Xabarlar sizga shu bot orqali keladi va siz javob bera olasiz.\n\n📊 Jami kelgan xabarlar: {message_count}\n\n🔗 **Sizning havolangiz:**",
            "copy_link": "📋 Linkni nusxala",
            "share_link": "🔗 Ulashish"
        }
    }
    
    # Simple fallback for other languages to Uz for now as requested for these specific instructions
    t = anon_texts.get("uz") 
    
    response_text = f"{t['title']}\n\n"
    response_text += f"{t['instructions']}\n\n"
    response_text += f"`{anon_link}`\n\n"
    response_text += "👆 **Nusxa olish uchun havola ustiga bosing!**"
    
    keyboard = InlineKeyboardBuilder()
    keyboard.row(
        InlineKeyboardButton(text=t['copy_link'], callback_data=f"cp_an_{user_token}"),
        InlineKeyboardButton(text=t['share_link'], switch_inline_query=f"\n🕵️ Menga anonim xabar yuborishingiz mumkin! \n👉 {anon_link}")
    )
    
    back_text = texts.get(language, {}).get("back_button", "♻️ Orqaga")
    keyboard.row(InlineKeyboardButton(text=back_text, callback_data="back_to_menu"))
    
    await message.answer(response_text, reply_markup=keyboard.as_markup(), parse_mode="Markdown")

@dp.message(AnonimStates.AnonimXabarYuborish)
async def handle_anon_message_delivery(message: Message, state: FSMContext):
    user_data = await state.get_data()
    token = user_data.get("anon_token")
    if not token:
        await state.clear()
        return

    target_id = decode_anonymous_token(token)
    if not target_id:
        await state.clear()
        return

    # Zip check
    if message.document and message.document.file_name and message.document.file_name.lower().endswith(".zip"):
        await message.answer("❌ .zip fayllar taqiqlangan.")
        return

    try:
        reply_markup = InlineKeyboardBuilder()
        reply_markup.add(InlineKeyboardButton(text="Javob berish 💬", callback_data=f"re_an_{message.from_user.id}"))
        
        await message.bot.send_message(chat_id=target_id, text="📨 **Yangi anonim xabar tushdi:**", parse_mode="Markdown")
        await message.copy_to(chat_id=target_id, reply_markup=reply_markup.as_markup())
        
        if token not in anonymous_tokens:
            anonymous_tokens[token] = {'user_id': target_id, 'message_count': 0}
        anonymous_tokens[token]['message_count'] += 1
        
        await message.answer("✅ Xabar yuborildi!")
    except:
        await message.answer("❌ Xabar yuborilmadi.")
    
    await state.clear()

@dp.callback_query(lambda c: c.data.startswith("re_an_"))
async def start_anon_reply(callback: CallbackQuery, state: FSMContext):
    target_id = callback.data.split("_")[2]
    await state.update_data(reply_target_id=target_id)
    await state.set_state(AnonimStates.AnonimJavobQaytarish)
    await callback.message.answer("🕵️ **Javobingizni kiriting:**")
    await callback.answer()

@dp.message(AnonimStates.AnonimJavobQaytarish)
async def deliver_anon_reply(message: Message, state: FSMContext):
    data = await state.get_data()
    target_id = data.get("reply_target_id")
    if not target_id:
        await state.clear()
        return

    try:
        reply_markup = InlineKeyboardBuilder()
        reply_markup.add(InlineKeyboardButton(text="Javob berish 💬", callback_data=f"re_an_{message.from_user.id}"))
        await message.bot.send_message(chat_id=int(target_id), text="🗣 **Anonim javob keldi:**", parse_mode="Markdown")
        await message.copy_to(chat_id=int(target_id), reply_markup=reply_markup.as_markup())
        await message.answer("✅ Yuborildi!")
    except:
        await message.answer("❌ Xato.")
    await state.clear()

@dp.callback_query(lambda c: c.data.startswith("cp_an_"))
async def copy_anon_link(callback: CallbackQuery):
    token = callback.data.split("_")[2]
    link = generate_anonymous_link(token)
    # Give a message that is easy to copy
    await callback.message.answer(f"📋 **Sizning havolangiz (Nusxa olish uchun bosing):**\n\n`{link}`", parse_mode="Markdown")
    await callback.answer("Link yuborildi!")

@dp.callback_query(lambda c: c.data == "back_to_menu")
async def back_to_main_menu(callback: CallbackQuery, state: FSMContext):
    from keyboard_buttons.admin_keyboard import create_menu_buttons
    await state.clear()
    user = db.select_user_by_id(telegram_id=callback.from_user.id)
    language = user[2] if user else "uz"
    await callback.message.answer(texts.get(language, {}).get("welcome_message", "🏠"), reply_markup=create_menu_buttons(language))
    await callback.message.delete()
    await callback.answer()
