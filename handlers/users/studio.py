"""AI Studio + O'yinlar + Donat (Telegram Stars va karta).

Rangli tugmalar: Bot API 9.4 `style` maydoni (primary=ko'k, success=yashil, danger=qizil).
"""
import html
import logging
import random

import ssl

import aiohttp
import certifi

_SSL = ssl.create_default_context(cafile=certifi.where())
from aiogram import F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (CallbackQuery, CopyTextButton, InlineKeyboardButton,
                           InlineKeyboardMarkup, LabeledPrice, Message, PreCheckoutQuery)

from data.config import ADMINS, CARD_OWNER, CARDS, GEMINI_API_KEY, GEMINI_MODELS
from loader import bot, dp

log = logging.getLogger(__name__)

STAR_MIN, STAR_MAX = 1, 100_000
STAR_PRESETS = [50, 100, 250, 500, 1000, 5000]

STUDIO_BTNS = ["✨ AI Studio"]
GAMES_BTNS = ["🎲 AI O'yinlar"]
DONATE_BTNS = ["💝 Donat"]


class St(StatesGroup):
    ai_input = State()
    stars_amount = State()
    guess = State()
    riddle = State()
    card_check = State()


# ------------------------------------------------------------------ yordamchilar
def b(text, cb=None, style=None, **kw):
    if style:
        kw["style"] = style
    return InlineKeyboardButton(text=text, callback_data=cb, **kw)


def kb(*rows):
    return InlineKeyboardMarkup(inline_keyboard=[list(r) for r in rows])


BACK = b("⬅️ Orqaga", "st:home", "danger")

# kalit: (sarlavha, so'rov namunasi, AI ko'rsatmasi)
TOOLS = {
    # 1. Shaxsiylashtirish
    "nick":     ("🎭 Nickname", "Masalan: gamer, qora, sher", "Telegram/o'yin uchun 10 ta chiroyli, noyob nickname yarat. Ba'zilarini maxsus belgilar (꧁ ꧂ ♛ 乂 ᴬ) bilan bezat."),
    "bio":      ("📝 Bio", "Masalan: dasturchi, sportni sevaman", "Telegram bio uchun 5 ta qisqa (70 belgigacha), ta'sirli variant yoz, emojilar bilan."),
    "about":    ("👤 Profil tavsifi", "O'zingiz haqingizda 2-3 so'z", "3 ta profil tavsifi yoz: rasmiy, do'stona, kreativ. Har biri 2-3 gap."),
    "status":   ("💬 Status", "Kayfiyat yoki mavzu", "8 ta qisqa status/iqtibos yoz, emoji bilan."),
    "username": ("🔗 Username g'oyalari", "Ism yoki soha", "10 ta Telegram username g'oyasi ber: faqat lotin harf, raqam, _; 5-32 belgi; @ bilan boshlansin."),
    # 2. Telegram yordamchi
    "post":     ("📢 Post matni", "Post mavzusi", "Telegram kanal uchun jozibali post yoz: sarlavha, asosiy matn, chaqiriq, 3-5 hashtag."),
    "channel":  ("📛 Kanal nomi", "Kanal mavzusi", "10 ta kanal nomi va har biriga mos @username taklif qil."),
    "desc":     ("📄 Kanal tavsifi", "Kanal nomi va mavzusi", "3 ta kanal tavsifi yoz (255 belgigacha), emojilar bilan."),
    "ad":       ("📣 Reklama matni", "Mahsulot/xizmat", "Sotuvchi reklama matni yoz: AIDA formulasi, qisqa, emoji, chaqiriq bilan. 2 variant."),
    "content":  ("🗓 Kontent reja", "Kanal mavzusi", "7 kunlik kontent reja tuz: har kun uchun post g'oyasi va formati."),
    # 3. Kreativ
    "brand":    ("🏷 Ism / Brend nomi", "Soha va uslub", "10 ta brend nomi taklif qil, har biriga qisqa izoh va slogan."),
    "design":   ("🎨 Dizayn g'oyalari", "Nima uchun dizayn (logo, avatar...)", "5 ta dizayn g'oyasi ber: ranglar palitrasi (HEX), shrift, kompozitsiya."),
    "style":    ("✍️ Yozuv uslublari", "Matningizni yuboring", "Berilgan matnni 4 uslubda qayta yoz: rasmiy, do'stona, she'riy, hazil."),
}
SECTIONS = {
    "sec1": ("👤 Shaxsiylashtirish", ["nick", "bio", "about", "status", "username"], "primary"),
    "sec2": ("📲 Telegram yordamchi", ["post", "channel", "desc", "ad", "content"], "success"),
    "sec3": ("🎨 Kreativ vositalar", ["brand", "design", "style"], "danger"),
}


async def ai(prompt: str) -> str | None:
    if not GEMINI_API_KEY:
        return None
    body = {"contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 1.0, "maxOutputTokens": 1024}}
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=_SSL)) as s:
        for model in GEMINI_MODELS:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
            try:
                async with s.post(url, params={"key": GEMINI_API_KEY}, json=body,
                                  timeout=aiohttp.ClientTimeout(total=30)) as r:
                    data = await r.json(content_type=None)
                    return data["candidates"][0]["content"]["parts"][0]["text"].strip()
            except Exception as e:
                log.warning("Gemini %s xato: %s", model, e)
    return None


SYSTEM = ("Sen o'zbek tilidagi kreativ yordamchisan. Javobni foydalanuvchi tilida, "
          "markdown belgilarisiz (* # yo'q), toza ro'yxat ko'rinishida ber.\nVazifa: ")


# ------------------------------------------------------------------ AI Studio
def home_kb():
    return kb(
        *[[b(t, f"st:{k}", s)] for k, (t, _, s) in SECTIONS.items()],
        [b("🎲 AI O'yinlar", "g:home", "primary"), b("💝 Donat", "d:home", "success")],
    )


@dp.message(Command("studio"), StateFilter("*"))
@dp.message(F.text.in_(STUDIO_BTNS), StateFilter("*"))
async def studio(m: Message, state: FSMContext):
    await state.clear()
    await m.answer("✨ <b>AI Studio</b>\n\nBo'limni tanlang:", reply_markup=home_kb())


@dp.callback_query(F.data == "st:home")
async def studio_cb(c: CallbackQuery, state: FSMContext):
    await state.clear()
    await c.message.edit_text("✨ <b>AI Studio</b>\n\nBo'limni tanlang:", reply_markup=home_kb())


@dp.callback_query(F.data.in_({f"st:{k}" for k in SECTIONS}))
async def section(c: CallbackQuery):
    title, keys, style = SECTIONS[c.data[3:]]
    rows = [[b(TOOLS[k][0], f"ai:{k}", style)] for k in keys]
    await c.message.edit_text(f"<b>{title}</b>\n\nVositani tanlang:", reply_markup=kb(*rows, [BACK]))


@dp.callback_query(F.data.startswith("ai:"))
async def tool(c: CallbackQuery, state: FSMContext):
    key = c.data[3:]
    await state.set_state(St.ai_input)
    await state.update_data(tool=key)
    await c.message.edit_text(f"<b>{TOOLS[key][0]}</b>\n\n✍️ {TOOLS[key][1]}", reply_markup=kb([BACK]))


async def run_tool(m: Message, key: str, query: str):
    wait = await m.answer("⏳ AI o'ylayapti...")
    res = await ai(f"{SYSTEM}{TOOLS[key][2]}\nFoydalanuvchi so'rovi: {query}")
    if res is None:
        res = "⚠️ AI hozir mavjud emas (GEMINI_API_KEY sozlanmagan yoki limit tugagan)."
    await wait.edit_text(f"<b>{TOOLS[key][0]}</b>\n\n{html.escape(res)[:4000]}",
                         reply_markup=kb([b("🔄 Yana", "re", "success"), BACK]))


@dp.message(St.ai_input, F.text)
async def ai_input(m: Message, state: FSMContext):
    data = await state.get_data()
    await state.update_data(q=m.text[:500])
    await run_tool(m, data["tool"], m.text[:500])


@dp.callback_query(F.data == "re")
async def regen(c: CallbackQuery, state: FSMContext):
    d = await state.get_data()
    if not d.get("q"):
        return await c.answer("Qaytadan tanlang", show_alert=True)
    await c.answer()
    await run_tool(c.message, d["tool"], d["q"])


# ------------------------------------------------------------------ O'yinlar
def games_kb():
    return kb(
        [b("🧩 AI topishmoq", "g:riddle", "primary"), b("🔢 Son top", "g:guess", "success")],
        [b("🎲", "g:d:🎲"), b("🎯", "g:d:🎯"), b("🏀", "g:d:🏀"),
         b("⚽", "g:d:⚽"), b("🎳", "g:d:🎳"), b("🎰", "g:d:🎰")],
        [BACK],
    )


@dp.message(F.text.in_(GAMES_BTNS), StateFilter("*"))
async def games(m: Message, state: FSMContext):
    await state.clear()
    await m.answer("🎲 <b>AI O'yinlar</b>", reply_markup=games_kb())


@dp.callback_query(F.data == "g:home")
async def games_cb(c: CallbackQuery, state: FSMContext):
    await state.clear()
    await c.message.edit_text("🎲 <b>AI O'yinlar</b>", reply_markup=games_kb())


@dp.callback_query(F.data.startswith("g:d:"))
async def dice(c: CallbackQuery):
    await c.answer()
    await c.message.answer_dice(emoji=c.data[4:])


@dp.callback_query(F.data == "g:guess")
async def guess_start(c: CallbackQuery, state: FSMContext):
    await state.set_state(St.guess)
    await state.update_data(n=random.randint(1, 100), tries=0)
    await c.message.edit_text("🔢 Men 1 dan 100 gacha son o'yladim. Toping!", reply_markup=kb([b("⬅️ Orqaga", "g:home", "danger")]))


@dp.message(St.guess, F.text)
async def guess(m: Message, state: FSMContext):
    if not m.text.isdigit():
        return await m.answer("Faqat son yozing")
    d = await state.get_data()
    x, tries = int(m.text), d["tries"] + 1
    await state.update_data(tries=tries)
    if x == d["n"]:
        await state.clear()
        return await m.answer(f"🎉 Topdingiz! {tries} urinishda.", reply_markup=games_kb())
    await m.answer("⬆️ Kattaroq" if x < d["n"] else "⬇️ Kichikroq")


@dp.callback_query(F.data == "g:riddle")
async def riddle(c: CallbackQuery, state: FSMContext):
    await c.answer("⏳")
    res = await ai("O'zbek tilida bitta qiziqarli topishmoq yoz. Format aynan: "
                   "TOPISHMOQ: <matn>\nJAVOB: <bir so'z>")
    if not res or "JAVOB:" not in res:
        q, a = random.choice([("Og'zi yo'q, gapiradi; oyog'i yo'q, yuradi.", "soat"),
                              ("Kechasi chiqadi, kunduzi yo'qoladi.", "yulduz")])
    else:
        q, a = res.split("JAVOB:")
        q, a = q.replace("TOPISHMOQ:", "").strip(), a.strip().strip(".").lower()
    await state.set_state(St.riddle)
    await state.update_data(a=a)
    await c.message.answer(f"🧩 {html.escape(q)}\n\nJavobni yozing:",
                           reply_markup=kb([b("🙈 Javobni ko'rsat", "g:ans", "danger")]))


@dp.message(St.riddle, F.text)
async def riddle_ans(m: Message, state: FSMContext):
    a = (await state.get_data())["a"]
    if a in m.text.lower():
        await state.clear()
        await m.answer("✅ To'g'ri! Barakalla 🎉", reply_markup=games_kb())
    else:
        await m.answer("❌ Noto'g'ri, yana urinib ko'ring")


@dp.callback_query(F.data == "g:ans")
async def riddle_show(c: CallbackQuery, state: FSMContext):
    a = (await state.get_data()).get("a", "?")
    await state.clear()
    await c.message.answer(f"💡 Javob: <tg-spoiler>{html.escape(a)}</tg-spoiler>", reply_markup=games_kb())


# ------------------------------------------------------------------ Donat
def donate_kb():
    rows = [[b(f"⭐ {n}", f"d:s:{n}", "primary") for n in STAR_PRESETS[i:i + 3]] for i in (0, 3)]
    rows.append([b("✏️ Boshqa miqdor", "d:custom", "success")])
    if CARDS:
        rows.append([b("💳 Karta orqali", "d:card", "success")])
    rows.append([BACK])
    return kb(*rows)


DONATE_TEXT = (f"💝 <b>Botni qo'llab-quvvatlash</b>\n\n⭐ Telegram Stars: {STAR_MIN} dan "
               f"{STAR_MAX:,} tagacha.\nTo'lashingiz mumkin, masalan: <b>50 ta yulduz</b>.")


@dp.message(Command("donate"), StateFilter("*"))
@dp.message(F.text.in_(DONATE_BTNS), StateFilter("*"))
async def donate(m: Message, state: FSMContext):
    await state.clear()
    await m.answer(DONATE_TEXT, reply_markup=donate_kb())


@dp.callback_query(F.data == "d:home")
async def donate_cb(c: CallbackQuery, state: FSMContext):
    await state.clear()
    await c.message.edit_text(DONATE_TEXT, reply_markup=donate_kb())


async def send_stars_invoice(chat_id: int, amount: int):
    await bot.send_invoice(
        chat_id, title="Donat ⭐", description=f"{amount} ta yulduz — rahmat! 💝",
        payload=f"donate:{amount}", currency="XTR", provider_token="",
        prices=[LabeledPrice(label="Donat", amount=amount)],
    )


@dp.callback_query(F.data.startswith("d:s:"))
async def stars_preset(c: CallbackQuery):
    await c.answer()
    await send_stars_invoice(c.from_user.id, int(c.data[4:]))


@dp.callback_query(F.data == "d:custom")
async def stars_custom(c: CallbackQuery, state: FSMContext):
    await state.set_state(St.stars_amount)
    await c.message.edit_text(f"✏️ Nechta yulduz? ({STAR_MIN}–{STAR_MAX:,})\nMasalan: <b>50</b>",
                              reply_markup=kb([b("⬅️ Orqaga", "d:home", "danger")]))


@dp.message(St.stars_amount, F.text)
async def stars_amount(m: Message, state: FSMContext):
    t = m.text.replace(" ", "").replace(",", "")
    if not t.isdigit() or not STAR_MIN <= int(t) <= STAR_MAX:
        return await m.answer(f"❗ {STAR_MIN} dan {STAR_MAX:,} gacha son kiriting")
    await state.clear()
    await send_stars_invoice(m.chat.id, int(t))


@dp.pre_checkout_query()
async def pre_checkout(q: PreCheckoutQuery):
    await q.answer(ok=True)


@dp.message(F.successful_payment)
async def paid(m: Message):
    p = m.successful_payment
    await m.answer(f"🎉 Rahmat! {p.total_amount} ⭐ qabul qilindi. Siz zo'rsiz! 💝")
    for a in ADMINS:
        try:
            await bot.send_message(a, f"⭐ Donat: {p.total_amount} XTR\n👤 {html.escape(m.from_user.full_name)} "
                                      f"(<code>{m.from_user.id}</code>)\n🧾 <code>{p.telegram_payment_charge_id}</code>")
        except Exception:
            pass


@dp.callback_query(F.data == "d:card")
async def card(c: CallbackQuery):
    rows = [[InlineKeyboardButton(text=f"📋 {n}", copy_text=CopyTextButton(text=n.replace(' ', '')), style="primary")]
            for n in CARDS]
    rows.append([b("✅ To'ladim (chek yuborish)", "d:chk", "success")])
    rows.append([b("⬅️ Orqaga", "d:home", "danger")])
    cards = "\n".join(f"💳 <code>{n}</code>" for n in CARDS)
    owner = f"\n👤 {html.escape(CARD_OWNER)}" if CARD_OWNER else ""
    await c.message.edit_text(f"💳 <b>Karta orqali donat</b>\n\n{cards}{owner}\n\n"
                              "Raqamni nusxalash uchun tugmani bosing. To'lovdan so'ng chekni yuboring.",
                              reply_markup=kb(*rows))


@dp.callback_query(F.data == "d:chk")
async def card_check(c: CallbackQuery, state: FSMContext):
    await state.set_state(St.card_check)
    await c.message.answer("🧾 To'lov chekini (rasm yoki skrinshot) yuboring:")
    await c.answer()


@dp.message(St.card_check, F.photo | F.document)
async def card_receipt(m: Message, state: FSMContext):
    await state.clear()
    for a in ADMINS:
        try:
            await m.forward(a)
            await bot.send_message(a, f"💳 Karta donati cheki\n👤 {html.escape(m.from_user.full_name)} "
                                      f"(<code>{m.from_user.id}</code>)")
        except Exception:
            pass
    await m.answer("✅ Chek adminga yuborildi. Katta rahmat! 💝")
