"""Admin panel: Gemini API kalitini va karta raqamlarini qo'shish/almashtirish."""
import html

from aiogram import F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from data import settings
from filterss.admin import IsBotAdminFilter
from loader import ADMINS, db, dp


class Adm(StatesGroup):
    api_key = State()
    card = State()
    owner = State()


def b(text, cb, style=None):
    return InlineKeyboardButton(text=text, callback_data=cb, **({"style": style} if style else {}))


def mask(k: str) -> str:
    return f"{k[:6]}…{k[-4:]}" if len(k) > 12 else ("✅ bor" if k else "❌ yo'q")


# ------------------------------------------------------------- Gemini API
def api_view():
    k = settings.gemini_key()
    text = f"🔑 <b>Gemini API kalit</b>\n\nHozirgi: <code>{html.escape(mask(k))}</code>"
    rows = [[b("✏️ Qo'shish / Almashtirish", "adm:api_set", "success")]]
    if k:
        rows.append([b("🧪 Tekshirish", "adm:api_test", "primary"), b("🗑 O'chirish", "adm:api_del", "danger")])
    return text, InlineKeyboardMarkup(inline_keyboard=rows)


@dp.message(F.text == "🔑 Gemini API", IsBotAdminFilter(ADMINS), StateFilter("*"))
async def api_menu(m: Message, state: FSMContext):
    await state.clear()
    t, k = api_view()
    await m.answer(t, reply_markup=k)


@dp.callback_query(F.data == "adm:api_set", IsBotAdminFilter(ADMINS))
async def api_set(c: CallbackQuery, state: FSMContext):
    await state.set_state(Adm.api_key)
    await c.message.answer("🔑 Yangi Gemini API kalitini yuboring\n(https://aistudio.google.com/apikey)\n\n/cancel — bekor qilish")
    await c.answer()


@dp.message(Adm.api_key, F.text, IsBotAdminFilter(ADMINS))
async def api_save(m: Message, state: FSMContext):
    await state.clear()
    if m.text.startswith("/"):
        return await m.answer("Bekor qilindi")
    key = m.text.strip()
    try:
        await m.delete()  # kalit chatda ochiq qolmasin
    except Exception:
        pass
    db.set_setting("gemini_key", key)
    from handlers.users.studio import ai
    ok = await ai("Bir so'zda: salom")
    await m.answer(f"✅ Kalit saqlandi: <code>{html.escape(mask(key))}</code>\n"
                   + ("🟢 AI ishlayapti" if ok else "🔴 AI javob bermadi — kalitni tekshiring"))


@dp.callback_query(F.data == "adm:api_test", IsBotAdminFilter(ADMINS))
async def api_test(c: CallbackQuery):
    await c.answer("⏳")
    from handlers.users.studio import ai
    res = await ai("Bir so'zda: salom")
    await c.message.answer(f"🟢 Ishlayapti: {html.escape(res)}" if res else "🔴 AI javob bermadi")


@dp.callback_query(F.data == "adm:api_del", IsBotAdminFilter(ADMINS))
async def api_del(c: CallbackQuery):
    db.set_setting("gemini_key", "")
    t, k = api_view()
    await c.message.edit_text(t, reply_markup=k)
    await c.answer("O'chirildi")


# ------------------------------------------------------------- Kartalar
def cards_view():
    items = settings.cards()
    owner = settings.card_owner()
    lines = "\n".join(f"{i + 1}. <code>{html.escape(n)}</code>" for i, n in enumerate(items)) or "— karta yo'q"
    text = f"💳 <b>Donat kartalari</b>\n\n{lines}\n\n👤 Egasi: {html.escape(owner) or '—'}"
    rows = [[b(f"🗑 {n}", f"adm:cdel:{i}", "danger")] for i, n in enumerate(items)]
    rows.append([b("➕ Karta qo'shish", "adm:cadd", "success"), b("👤 Egasini o'zgartirish", "adm:owner", "primary")])
    return text, InlineKeyboardMarkup(inline_keyboard=rows)


@dp.message(F.text == "💳 Kartalar", IsBotAdminFilter(ADMINS), StateFilter("*"))
async def cards_menu(m: Message, state: FSMContext):
    await state.clear()
    t, k = cards_view()
    await m.answer(t, reply_markup=k)


@dp.callback_query(F.data == "adm:cadd", IsBotAdminFilter(ADMINS))
async def card_add(c: CallbackQuery, state: FSMContext):
    await state.set_state(Adm.card)
    await c.message.answer("💳 Karta raqamini yuboring (16 raqam)\nMasalan: 8600 1234 5678 9012\n\n/cancel — bekor qilish")
    await c.answer()


@dp.message(Adm.card, F.text, IsBotAdminFilter(ADMINS))
async def card_save(m: Message, state: FSMContext):
    if m.text.startswith("/"):
        await state.clear()
        return await m.answer("Bekor qilindi")
    digits = "".join(ch for ch in m.text if ch.isdigit())
    if len(digits) != 16:
        return await m.answer("❗ Karta raqami 16 ta raqamdan iborat bo'lishi kerak. Qaytadan yuboring:")
    await state.clear()
    num = " ".join(digits[i:i + 4] for i in range(0, 16, 4))
    items = settings.cards()
    if num not in items:
        settings.set_cards(items + [num])
    t, k = cards_view()
    await m.answer("✅ Karta qo'shildi\n\n" + t, reply_markup=k)


@dp.callback_query(F.data.startswith("adm:cdel:"), IsBotAdminFilter(ADMINS))
async def card_del(c: CallbackQuery):
    items = settings.cards()
    i = int(c.data.split(":")[2])
    if 0 <= i < len(items):
        items.pop(i)
        settings.set_cards(items)
    t, k = cards_view()
    await c.message.edit_text(t, reply_markup=k)
    await c.answer("O'chirildi")


@dp.callback_query(F.data == "adm:owner", IsBotAdminFilter(ADMINS))
async def owner_set(c: CallbackQuery, state: FSMContext):
    await state.set_state(Adm.owner)
    await c.message.answer("👤 Karta egasining ism-familiyasini yuboring:\n\n/cancel — bekor qilish")
    await c.answer()


@dp.message(Adm.owner, F.text, IsBotAdminFilter(ADMINS))
async def owner_save(m: Message, state: FSMContext):
    await state.clear()
    if m.text.startswith("/"):
        return await m.answer("Bekor qilindi")
    db.set_setting("card_owner", m.text.strip()[:64])
    t, k = cards_view()
    await m.answer("✅ Saqlandi\n\n" + t, reply_markup=k)
