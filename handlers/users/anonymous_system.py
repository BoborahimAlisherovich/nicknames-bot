"""Anonim xabarlar tizimi.

- Har bir foydalanuvchining DOIMIY havolasi bor (menyuni har ochganda yangisi yaratilmaydi).
- Havola botning haqiqiy username'i bilan yasaladi.
- Yuboruvchi ID'si tugmada emas, bazada saqlanadi (AnonMessages) — anonimlik saqlanadi.
- Ikki tomonlama javob: qabul qiluvchi ham, yuboruvchi ham "Javob berish" orqali yozishadi.
- Xabarlar soni bazada hisoblanadi (restartdan keyin ham yo'qolmaydi).
"""
import html
import logging
import secrets
import time
from urllib.parse import quote

from aiogram import F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, CopyTextButton, InlineKeyboardButton, InlineKeyboardMarkup, Message

from data.texts import get_texts
from loader import db, dp

log = logging.getLogger(__name__)
texts = get_texts()

_open_limits: dict[int, float] = {}
_send_limits: dict[int, float] = {}

# Menyu tugmalari bosilsa, ular anonim xabar sifatida ketib qolmasin
MENU_TEXTS = {v for lang in texts.values() for v in lang.get("menu", {}).values()} | {
    "✨ AI Studio", "🎲 AI O'yinlar", "💝 Donat", "🤖 AI yordamchi", "♻️ Orqaga", "♻️ Back", "♻️ Назад"}


class AnonimStates(StatesGroup):
    AnonimXabarYuborish = State()
    AnonimJavobQaytarish = State()


def is_rate_limited(user_id: int, delay: float = 3) -> bool:
    """Havolani juda tez-tez ochishdan himoya (start.py ishlatadi)."""
    now = time.time()
    if now - _open_limits.get(user_id, 0) < delay:
        return True
    _open_limits[user_id] = now
    return False


def _send_limited(user_id: int, delay: float = 3) -> bool:
    now = time.time()
    if now - _send_limits.get(user_id, 0) < delay:
        return True
    _send_limits[user_id] = now
    return False


def get_or_create_token(user_id: int) -> str:
    token = db.get_anon_token_by_user(user_id)
    if not token:
        token = secrets.token_hex(16)
        db.add_anon_token(token, user_id)
    return token


def decode_anonymous_token(token: str):
    try:
        if token.startswith("anon_"):
            token = token[5:]
        return db.get_anon_user(token)
    except Exception:
        return None


def _not_menu(message: Message) -> bool:
    return not (message.text and (message.text in MENU_TEXTS or message.text.startswith("/")))


def reply_kb(msg_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="💬 Javob berish", callback_data=f"re_an_{msg_id}", style="primary")]])


@dp.message(F.text.in_(["🕵️ Anonim xabar", "🕵️ Anonymous Msg", "🕵️ Анонимное сообщение"]), StateFilter("*"))
async def anonymous_menu_handler(message: Message, state: FSMContext):
    await state.clear()
    uid = message.from_user.id
    user = db.select_user_by_id(telegram_id=uid)
    language = user[2] if user else "uz"

    me = await message.bot.me()
    link = f"https://t.me/{me.username}?start=anon_{get_or_create_token(uid)}"
    count = db.count_anon_received(uid)

    text = (
        "🕵️ <b>Anonim xabarlar</b>\n\n"
        "1️⃣ Havolani nusxalab, story, kanal yoki guruhga qo'ying.\n"
        "2️⃣ Odamlar havola orqali sizga anonim xabar yozadi.\n"
        "3️⃣ Xabarlar shu yerga keladi — siz ham anonim javob bera olasiz.\n\n"
        f"📊 Sizga kelgan xabarlar: <b>{count}</b>\n\n"
        f"🔗 Havolangiz:\n<code>{html.escape(link)}</code>"
    )
    share = f"https://t.me/share/url?url={quote(link)}&text={quote('🕵️ Menga anonim xabar yozing!')}"
    back_text = texts.get(language, {}).get("back_button", "♻️ Orqaga")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Nusxalash", copy_text=CopyTextButton(text=link), style="success"),
         InlineKeyboardButton(text="🔗 Ulashish", url=share, style="primary")],
        [InlineKeyboardButton(text=back_text, callback_data="back_to_menu", style="danger")],
    ])
    await message.answer(text, reply_markup=kb, disable_web_page_preview=True)


@dp.message(AnonimStates.AnonimXabarYuborish, _not_menu)
async def handle_anon_message_delivery(message: Message, state: FSMContext):
    token = (await state.get_data()).get("anon_token")
    target_id = decode_anonymous_token(token) if token else None
    if not target_id:
        await state.clear()
        return await message.answer("❌ Bu anonim havola yaroqsiz.")

    if message.document and (message.document.file_name or "").lower().endswith((".zip", ".apk", ".exe")):
        return await message.answer("❌ Bunday fayllarni yuborib bo'lmaydi.")
    if _send_limited(message.from_user.id):
        return await message.answer("⏱ Biroz kuting, juda tez yozyapsiz.")

    msg_id = db.add_anon_message(message.from_user.id, target_id)
    try:
        await message.bot.send_message(target_id, "📨 <b>Sizga yangi anonim xabar keldi:</b>")
        await message.copy_to(chat_id=target_id, reply_markup=reply_kb(msg_id))
        await message.answer("✅ Xabar anonim yuborildi!\n\n✍️ Yana yozishingiz mumkin yoki menyudan chiqing.")
    except Exception as e:
        log.warning("Anonim xabar yuborilmadi (%s): %s", target_id, e)
        await state.clear()
        await message.answer("❌ Xabar yetkazilmadi — qabul qiluvchi botni bloklagan bo'lishi mumkin.")


@dp.callback_query(F.data.startswith("re_an_"))
async def start_anon_reply(callback: CallbackQuery, state: FSMContext):
    try:
        row = db.get_anon_message(int(callback.data[6:]))
    except ValueError:
        row = None
    if not row or callback.from_user.id not in row:
        return await callback.answer("❌ Bu xabarga javob berib bo'lmaydi", show_alert=True)
    sender_id, target_id = row
    other = sender_id if callback.from_user.id == target_id else target_id
    await state.set_state(AnonimStates.AnonimJavobQaytarish)
    await state.update_data(reply_target_id=other)
    await callback.message.answer("🕵️ <b>Javobingizni yozing</b> (matn, rasm, ovoz — hammasi bo'ladi):")
    await callback.answer()


@dp.message(AnonimStates.AnonimJavobQaytarish, _not_menu)
async def deliver_anon_reply(message: Message, state: FSMContext):
    target_id = (await state.get_data()).get("reply_target_id")
    await state.clear()
    if not target_id:
        return
    msg_id = db.add_anon_message(message.from_user.id, int(target_id))
    try:
        await message.bot.send_message(int(target_id), "🗣 <b>Anonim javob keldi:</b>")
        await message.copy_to(chat_id=int(target_id), reply_markup=reply_kb(msg_id))
        await message.answer("✅ Javob yuborildi!")
    except Exception as e:
        log.warning("Anonim javob yuborilmadi (%s): %s", target_id, e)
        await message.answer("❌ Javob yetkazilmadi.")


@dp.callback_query(F.data.startswith("cp_an_"))
async def copy_anon_link_old(callback: CallbackQuery):
    """Eski xabarlardagi 'Nusxalash' tugmasi uchun."""
    me = await callback.bot.me()
    link = f"https://t.me/{me.username}?start=anon_{callback.data[6:]}"
    await callback.message.answer(f"📋 Havolangiz:\n\n<code>{html.escape(link)}</code>")
    await callback.answer()
