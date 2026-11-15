from aiogram.types import Message, InlineKeyboardButton, CallbackQuery
from loader import dp, db
from aiogram.filters import StateFilter
from aiogram import types, F
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.state import State, StatesGroup
from keyboard_buttons.admin_keyboard import create_back_button, create_menu_buttons, texts
from handlers.users.nick_ai import get_theme_buttons, generate_nicks, format_nicks_list
import html

from handlers.users import nick_styles

PAGE = 10


def sections_markup():
    mk = InlineKeyboardBuilder()
    mk.row(*[InlineKeyboardButton(text=t, callback_data=f"nst:{k}:0:0")
             for k, (t, _) in list(nick_styles.SECTIONS.items())[:2]])
    mk.row(InlineKeyboardButton(text=nick_styles.SECTIONS["mix"][0], callback_data="nst:mix:0:0"))
    return mk

class NickState(StatesGroup):
    WaitingForName = State()

# Fetch button texts from languages.json
nick_button_texts = [
    texts["uz"]["menu"]["menu_button_11"],
    texts["us"]["menu"]["menu_button_11"],
    texts["ru"]["menu"]["menu_button_11"]
]

AI_THINKING = {
    "uz": "🤖 AI ishlayapti... ijodiy niklar yaratilmoqda (5-10 sekund)",
    "us": "🤖 AI is working... generating creative nicks (5-10 seconds)",
    "ru": "🤖 AI работает... создаю креативные ники (5-10 секунд)",
}
AI_SOURCE = {
    "uz": "🤖 AI yaratdi",
    "us": "🤖 Made by AI",
    "ru": "🤖 Создано AI",
}
LOCAL_SOURCE = {
    "uz": "⚡ Lokal generator",
    "us": "⚡ Local generator",
    "ru": "⚡ Локальный генератор",
}
CHOOSE_THEME = {
    "uz": "🎨 Kayfiyat/mavzu tanlang — AI sizga mos ijodiy niklar yaratadi:",
    "us": "🎨 Pick a vibe/theme — AI will create creative nicks for you:",
    "ru": "🎨 Выберите настроение/тему — AI создаст креативные ники:",
}

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
        "uz": "✍️ Ismingizni yozib yuboring — fontlardan tashqari endi 🤖 AI ijodiy niklar ham yaratib beradi:",
        "us": "✍️ Send your name — besides fonts, 🤖 AI now creates creative nicknames too:",
        "ru": "✍️ Напишите своё имя — теперь 🤖 AI тоже создаёт креативные ники:"
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

    # Update data (name saqlanadi - AI generatsiyada ishlatiladi)
    await state.update_data(name=name)

    # Kayfiyat/mavzu tanlash (AI). Eski shrift ro'yxati olib tashlandi -
    # foydalanuvchi faqat mavzu tanlaydi.
    markup = sections_markup()
    theme_buttons = get_theme_buttons()
    # 2 tadan qator
    for i in range(0, len(theme_buttons), 2):
        row = []
        for cb, emoji, label in theme_buttons[i:i+2]:
            row.append(InlineKeyboardButton(text=f"{emoji} {label}", callback_data=cb))
        markup.row(*row)

    await message.answer(
        f"✍️ <b>{html.escape(name)}</b> uchun bo'limni tanlang:\n\n"
        "🔤 Shriftlar · ✨ Bezakli — bepul\n👑 Premium dizayn — 10 ⭐\n"
        "🤖 Pastdagi mavzular — AI ijodiy niklar",
        reply_markup=markup.as_markup()
    )


async def _render_ai_result(message, callback, name: str, theme_key: str, language: str, page: int = 0):
    """AI lokal/zaxira generatsiya va natijani ko'rsatish (callback orqali ishlatilmaydi - aigen handlerida bajeriladi)."""
    pass


@dp.callback_query(F.data.startswith("aigen_"))
async def ai_generate(callback: CallbackQuery, state: FSMContext):
    theme_key = callback.data.replace("aigen_", "")
    data = await state.get_data()
    name = data.get("name")
    if not name:
        await callback.answer("❌ Avval ismingizni yuboring!", show_alert=True)
        return

    user = db.select_user_by_id(telegram_id=callback.from_user.id)
    language = user[2] if user else "uz"

    await callback.message.answer(AI_THINKING.get(language, AI_THINKING["uz"]))

    # natijalarni to'liq ko'rsatish
    nicks, source = await generate_nicks(name, theme_key, language, count=20)
    source_label = AI_SOURCE.get(language, "🤖 AI") if source == "ai" else LOCAL_SOURCE.get(language, "⚡ Local")
    title = f"{source_label} · {theme_key.title()}"

    page_size = 10
    total_pages = (len(nicks) + page_size - 1) // page_size
    paginated = nicks[0:page_size]

    text = format_nicks_list(paginated, title)

    markup = InlineKeyboardBuilder()
    nav = []
    if total_pages > 1:
        nav.append(InlineKeyboardButton(text="➡️", callback_data=f"aipage_{theme_key}_1"))
    if nav:
        markup.row(*nav)
    markup.row(InlineKeyboardButton(
        text="🔄 Yana generatsiya",
        callback_data=f"aigen_{theme_key}"
    ))

    await callback.message.answer(text, parse_mode="HTML", reply_markup=markup.as_markup())
    # ismni saqlab qolish (keyingi generatsiyalar uchun)
    await state.update_data(name=name)
    await callback.answer()


@dp.callback_query(F.data.startswith("aipage_"))
async def ai_page(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    # aipage_{theme}_{page}
    theme_key = parts[1]
    page = int(parts[2])
    data = await state.get_data()
    name = data.get("name")
    if not name:
        await callback.answer("❌ Ma'lumot vaqti o'tib ketgan.", show_alert=True)
        return

    user = db.select_user_by_id(telegram_id=callback.from_user.id)
    language = user[2] if user else "uz"

    # saqlangan natijalar yo'q - qayta generatsiya (local tez, AI sekinroq)
    nicks, source = await generate_nicks(name, theme_key, language, count=20)
    source_label = AI_SOURCE.get(language, "🤖 AI") if source == "ai" else LOCAL_SOURCE.get(language, "⚡ Local")
    title = f"{source_label} · {theme_key.title()}"

    page_size = 10
    total_pages = (len(nicks) + page_size - 1) // page_size
    paginated = nicks[page*page_size:(page+1)*page_size]

    text = format_nicks_list(paginated, title)
    markup = InlineKeyboardBuilder()
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"aipage_{theme_key}_{page-1}"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton(text="➡️", callback_data=f"aipage_{theme_key}_{page+1}"))
    if nav:
        markup.row(*nav)
    markup.row(InlineKeyboardButton(text="🔄 Yana generatsiya", callback_data=f"aigen_{theme_key}"))

    try:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=markup.as_markup())
    except Exception:
        await callback.message.answer(text, parse_mode="HTML", reply_markup=markup.as_markup())
    await callback.answer()


@dp.callback_query(F.data.startswith("nst:"))
async def nick_section(callback: CallbackQuery, state: FSMContext):
    _, kind, page, seed = callback.data.split(":")
    page = int(page)
    name = (await state.get_data()).get("name")
    if not name:
        return await callback.answer("❌ Avval ismingizni yuboring!", show_alert=True)
    if kind == "mix":
        from data import paywall
        if not paywall.has(callback.from_user.id, "nick_premium"):
            await callback.message.edit_text(paywall.offer_text("nick_premium"),
                                             reply_markup=paywall.offer_kb("nick_premium", "nst_back"))
            return await callback.answer()
    items = nick_styles.build(kind, name, seed)
    pages = (len(items) + PAGE - 1) // PAGE
    page %= pages
    chunk = items[page * PAGE:(page + 1) * PAGE]
    title, desc = nick_styles.SECTIONS[kind]
    lines = [f"{title} — <i>{desc}</i>", "👆 Nikni bosing — nusxalanadi\n"]
    for i, (label, nick) in enumerate(chunk, page * PAGE + 1):
        tag = f" <i>({html.escape(label)})</i>" if label else ""
        lines.append(f"{i}. <code>{html.escape(nick)}</code>{tag}")
    lines.append(f"\n📄 {page + 1}/{pages} · Jami: {len(items)}")

    mk = InlineKeyboardBuilder()
    mk.row(InlineKeyboardButton(text="⬅️", callback_data=f"nst:{kind}:{page - 1}:{seed}"),
           InlineKeyboardButton(text="➡️", callback_data=f"nst:{kind}:{page + 1}:{seed}"))
    if kind == "mix":
        mk.row(InlineKeyboardButton(text="🔄 Yangi dizaynlar", callback_data=f"nst:mix:0:{int(seed) + 1}"))
    mk.row(InlineKeyboardButton(text="📂 Boshqa bo'lim", callback_data="nst_back"))
    try:
        await callback.message.edit_text("\n".join(lines), reply_markup=mk.as_markup())
    except Exception:
        await callback.message.answer("\n".join(lines), reply_markup=mk.as_markup())
    await callback.answer()


@dp.callback_query(F.data == "nst_back")
async def nick_sections_back(callback: CallbackQuery, state: FSMContext):
    name = (await state.get_data()).get("name")
    if not name:
        return await callback.answer("❌ Avval ismingizni yuboring!", show_alert=True)
    markup = sections_markup()
    tb = get_theme_buttons()
    for i in range(0, len(tb), 2):
        markup.row(*[InlineKeyboardButton(text=f"{e} {l}", callback_data=cb) for cb, e, l in tb[i:i + 2]])
    await callback.message.edit_text(f"✍️ <b>{html.escape(name)}</b> uchun bo'limni tanlang:", reply_markup=markup.as_markup())
    await callback.answer()
