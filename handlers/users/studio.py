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

from data import settings
from data.config import ADMINS, GEMINI_MODELS
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
    from data.gemini import ask
    return await ask(prompt)


SYSTEM = "Vazifa: "


# ------------------------------------------------------------------ AI Studio
def home_kb():
    return kb(
        [b("🤖 AI yordamchi (har qanday mavzu)", "chat:open", "success")],
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


async def run_tool(m: Message, uid: int, key: str, query: str):
    from data import paywall
    left = paywall.left(uid, "ai_studio")
    if left == 0:
        return await m.answer(paywall.offer_text("ai_pro", "🆓 3 ta bepul so'rovingiz tugadi.\n"),
                              reply_markup=paywall.offer_kb("ai_pro", "st:home"))
    wait = await m.answer("⏳ AI yozmoqda...")
    await m.bot.send_chat_action(m.chat.id, "typing")
    res = await ai(f"{SYSTEM}{TOOLS[key][2]}\nFoydalanuvchi so'rovi: {query}")
    if res is None:
        return await wait.edit_text("⚠️ AI hozir javob bermadi, birozdan so'ng qayta urinib ko'ring.",
                                    reply_markup=kb([b("🔄 Qayta urinish", "re", "success"), BACK]))
    paywall.consume(uid, "ai_studio")
    left = paywall.left(uid, "ai_studio")
    note = "" if left is None else f"\n\n🆓 Bepul so'rovlar qoldi: {left}/3"
    await wait.edit_text(f"<b>{TOOLS[key][0]}</b>\n\n{html.escape(res)[:3900]}{note}",
                         reply_markup=kb([b("🔄 Yana", "re", "success"), BACK]))


@dp.message(St.ai_input, F.text)
async def ai_input(m: Message, state: FSMContext):
    data = await state.get_data()
    await state.update_data(q=m.text[:800])
    await run_tool(m, m.from_user.id, data["tool"], m.text[:800])


@dp.callback_query(F.data == "re")
async def regen(c: CallbackQuery, state: FSMContext):
    d = await state.get_data()
    if not d.get("q"):
        return await c.answer("Qaytadan tanlang", show_alert=True)
    await c.answer()
    await run_tool(c.message, c.from_user.id, d["tool"], d["q"])


# ------------------------------------------------------------------ AI yordamchi (erkin suhbat)
CHAT_BTNS = ["🤖 AI yordamchi"]
CHAT_SYSTEM = ("Sen aqlli, do'stona va bilimdon AI yordamchisan. Har qanday mavzuda (o'qish, dasturlash, "
               "biznes, sog'liq bo'yicha umumiy maslahat, tarjima, matn yozish, hayotiy savollar) aniq va foydali "
               "javob ber. Foydalanuvchi tilida yoz. Markdown belgilarini ishlatma (* # ` yo'q), ro'yxat va emojilardan "
               "foydalan. Javob qisqa va mazmunli bo'lsin, kerak bo'lsa batafsil tushuntir.")


class Chat(StatesGroup):
    talk = State()


def chat_kb():
    return kb([b("🧹 Yangi suhbat", "chat:new", "primary"), b("⬅️ Chiqish", "chat:exit", "danger")])


async def chat_open(m: Message, state: FSMContext, uid: int):
    from data import paywall
    await state.clear()
    await state.set_state(Chat.talk)
    await state.update_data(hist=[])
    left = paywall.left(uid, "ai_chat")
    limit = "♾ Cheksiz (AI Pro)" if left is None else f"🆓 Bepul xabarlar: {left}/10"
    await m.answer("🤖 <b>AI yordamchi</b>\n\nIstalgan mavzuda savol bering — men javob beraman!\n"
                   f"Masalan: «Ingliz tilini qanday tez o'rganaman?»\n\n{limit}", reply_markup=chat_kb())


@dp.message(Command("ai"), StateFilter("*"))
@dp.message(F.text.in_(CHAT_BTNS), StateFilter("*"))
async def chat_start(m: Message, state: FSMContext):
    await chat_open(m, state, m.from_user.id)


@dp.callback_query(F.data == "chat:open")
async def chat_start_cb(c: CallbackQuery, state: FSMContext):
    await c.answer()
    await chat_open(c.message, state, c.from_user.id)


@dp.callback_query(F.data == "chat:new")
async def chat_new(c: CallbackQuery, state: FSMContext):
    await state.set_state(Chat.talk)
    await state.update_data(hist=[])
    await c.answer("🧹 Suhbat tozalandi")
    await c.message.answer("🆕 Yangi suhbat boshlandi. Savolingizni yozing:")


@dp.callback_query(F.data == "chat:exit")
async def chat_exit(c: CallbackQuery, state: FSMContext):
    await state.clear()
    await c.answer()
    await c.message.answer("👋 AI yordamchidan chiqdingiz.")


def _not_menu(m: Message) -> bool:
    from handlers.users.anonymous_system import MENU_TEXTS
    return m.text not in MENU_TEXTS and not m.text.startswith("/")


@dp.message(Chat.talk, F.text, _not_menu)
async def chat_msg(m: Message, state: FSMContext):
    from data import paywall
    from data.gemini import ask
    uid = m.from_user.id
    if paywall.left(uid, "ai_chat") == 0:
        return await m.answer(paywall.offer_text("ai_pro", "🆓 10 ta bepul xabaringiz tugadi.\n"),
                              reply_markup=paywall.offer_kb("ai_pro", "chat:exit"))
    hist = (await state.get_data()).get("hist", [])[-10:]
    await m.bot.send_chat_action(m.chat.id, "typing")
    res = await ask(m.text[:2000], history=hist, system=CHAT_SYSTEM, max_tokens=1800, temperature=0.7)
    if not res:
        return await m.answer("⚠️ AI hozir javob bermadi, qayta yozib ko'ring.")
    paywall.consume(uid, "ai_chat")
    hist += [{"role": "user", "text": m.text[:2000]}, {"role": "model", "text": res[:3000]}]
    await state.update_data(hist=hist[-10:])
    left = paywall.left(uid, "ai_chat")
    note = "" if left is None else f"\n\n🆓 Qoldi: {left}/10"
    text = html.escape(res)
    for i in range(0, len(text), 3900):
        last = i + 3900 >= len(text)
        await m.answer(text[i:i + 3900] + (note if last else ""), reply_markup=chat_kb() if last else None)


# ------------------------------------------------------------------ O'yinlar
def games_kb():
    return kb(
        [b("⚡ Tezkor matematika", "ag:math", "success"), b("🇬🇧 Ingliz tili", "ag:en", "success")],
        [b("🤖 AI sizning soningizni topadi", "ag:bot", "primary")],
        [b("🧩 AI topishmoq", "g:riddle", "primary"), b("🔢 Son top", "g:guess", "success")],
        [b("❓ AI viktorina", "g:quiz", "success"), b("🔤 So'z top", "g:word", "primary")],
        [b("🎬 Emoji topishmoq", "g:emoji", "primary"), b("✂️ Tosh-qaychi-qog'oz", "g:rps", "success")],
        [b("🎲", "g:d:🎲"), b("🎯", "g:d:🎯"), b("🏀", "g:d:🏀"),
         b("⚽", "g:d:⚽"), b("🎳", "g:d:🎳"), b("🎰", "g:d:🎰")],
        [b("🏆 Reyting", "ag:top", "success")],
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
    if settings.cards():
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
    if p.invoice_payload.startswith("unlock:"):
        from data import paywall
        item = p.invoice_payload.split(":", 1)[1]
        paywall.grant(m.from_user.id, item, p.total_amount, p.telegram_payment_charge_id)
        title = paywall.ITEMS.get(item, (0, item))[1]
        await m.answer(f"✅ To'lov qabul qilindi! <b>{title}</b> endi siz uchun ochiq. Rahmat! 💝")
        for a in ADMINS:
            try:
                await bot.send_message(a, f"🔓 Sotildi: {title} — {p.total_amount} ⭐\n👤 {html.escape(m.from_user.full_name)} "
                                          f"(<code>{m.from_user.id}</code>)")
            except Exception:
                pass
        return
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
            for n in settings.cards()]
    rows.append([b("✅ To'ladim (chek yuborish)", "d:chk", "success")])
    rows.append([b("⬅️ Orqaga", "d:home", "danger")])
    cards = "\n".join(f"💳 <code>{n}</code>" for n in settings.cards())
    owner_name = settings.card_owner()
    owner = f"\n👤 {html.escape(owner_name)}" if owner_name else ""
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


# ---------------------------------------------------------- Qo'shimcha AI o'yinlar
QUIZ_FALLBACK = [
    ("O'zbekistonning poytaxti qaysi?", ["Toshkent", "Samarqand", "Buxoro", "Xiva"], 0),
    ("Yer Quyosh atrofini necha kunda aylanadi?", ["365", "30", "100", "24"], 0),
    ("Eng katta okean qaysi?", ["Tinch", "Atlantika", "Hind", "Shimoliy Muz"], 0),
    ("Alisher Navoiy qaysi asrda yashagan?", ["XV", "XII", "XVIII", "X"], 0),
]
WORDS = ["kitob", "maktab", "telefon", "kompyuter", "olma", "bahor", "do'stlik", "quyosh", "daryo", "samolyot",
         "futbol", "shaxmat", "tarvuz", "yulduz", "kapalak", "muzqaymoq", "televizor", "universitet"]
EMOJI_FALLBACK = [("🦁👑", "sher qirol"), ("🕷🧑", "o'rgimchak odam"), ("❄️👸", "muz malika"), ("🚢🧊💔", "titanik")]


async def _ask(c: CallbackQuery, state: FSMContext, question: str, answer: str, tag: str):
    await state.set_state(St.riddle)
    await state.update_data(a=answer.lower().strip(" ."))
    await c.message.answer(f"{tag}\n\n{html.escape(question)}\n\n✍️ Javobni yozing:",
                           reply_markup=kb([b("🙈 Javobni ko'rsat", "g:ans", "danger")]))


@dp.callback_query(F.data == "g:quiz")
async def quiz(c: CallbackQuery, state: FSMContext):
    await c.answer("⏳")
    res = await ai("O'zbek tilida bitta qiziqarli umumiy bilim savoli tuz. Format aynan bitta qator: "
                   "SAVOL|variant1|variant2|variant3|variant4|to'g'ri_variant_raqami(1-4)")
    q = None
    try:
        parts = [p.strip() for p in res.strip().splitlines()[0].split("|")]
        if len(parts) == 6:
            q = (parts[0], parts[1:5], int(parts[5]) - 1)
    except Exception:
        pass
    q = q or random.choice(QUIZ_FALLBACK)
    question, opts, right = q
    order = list(range(4))
    random.shuffle(order)
    await state.update_data(quiz_right=opts[right])
    rows = [[b(opts[i], f"g:qa:{int(i == right)}", "primary")] for i in order]
    await c.message.answer(f"❓ <b>Viktorina</b>\n\n{html.escape(question)}", reply_markup=kb(*rows))


@dp.callback_query(F.data.startswith("g:qa:"))
async def quiz_answer(c: CallbackQuery, state: FSMContext):
    right = (await state.get_data()).get("quiz_right", "")
    ok = c.data.endswith("1")
    await c.message.edit_reply_markup(reply_markup=None)
    await c.message.answer(("✅ To'g'ri! 🎉" if ok else f"❌ Noto'g'ri. To'g'ri javob: <b>{html.escape(right)}</b>"),
                           reply_markup=kb([b("➡️ Keyingi savol", "g:quiz", "success")], [b("⬅️ O'yinlar", "g:home", "danger")]))
    await c.answer()


@dp.callback_query(F.data == "g:word")
async def word_game(c: CallbackQuery, state: FSMContext):
    await c.answer()
    w = random.choice(WORDS)
    letters = list(w)
    while "".join(letters) == w and len(set(w)) > 1:
        random.shuffle(letters)
    await _ask(c, state, f"Harflardan so'z tuzing: {' '.join(letters).upper()}", w, "🔤 <b>So'z top</b>")


@dp.callback_query(F.data == "g:emoji")
async def emoji_game(c: CallbackQuery, state: FSMContext):
    await c.answer("⏳")
    res = await ai("Mashhur film, multfilm yoki maqolni 2-4 ta emoji bilan ifodala. Javob o'zbekcha. "
                   "Format aynan: EMOJI: <emojilar>\nJAVOB: <nomi>")
    if res and "JAVOB:" in res:
        e, a = res.split("JAVOB:", 1)
        e = e.replace("EMOJI:", "").strip()
    else:
        e, a = random.choice(EMOJI_FALLBACK)
    await _ask(c, state, f"Bu qaysi film/multfilm?  {e}", a.strip(), "🎬 <b>Emoji topishmoq</b>")


RPS = {"tosh": ("🪨", "qaychi"), "qaychi": ("✂️", "qog'oz"), "qog'oz": ("📄", "tosh")}


@dp.callback_query(F.data == "g:rps")
async def rps(c: CallbackQuery):
    await c.answer()
    await c.message.answer("✂️ Tanlang:", reply_markup=kb(
        [b(f"{e} {k.title()}", f"g:rp:{k}", "primary") for k, (e, _) in RPS.items()], [b("⬅️ O'yinlar", "g:home", "danger")]))


@dp.callback_query(F.data.startswith("g:rp:"))
async def rps_play(c: CallbackQuery):
    me, bot_pick = c.data[5:], random.choice(list(RPS))
    res = "🤝 Durang!" if me == bot_pick else ("🎉 Siz yutdingiz!" if RPS[me][1] == bot_pick else "😎 Men yutdim!")
    await c.message.edit_text(f"Siz: {RPS[me][0]}  ·  Bot: {RPS[bot_pick][0]}\n\n<b>{res}</b>",
                              reply_markup=kb([b(f"{e} {k.title()}", f"g:rp:{k}", "primary") for k, (e, _) in RPS.items()],
                                              [b("⬅️ O'yinlar", "g:home", "danger")]))
    await c.answer()


@dp.callback_query(F.data.startswith("unlock:"))
async def unlock_buy(c: CallbackQuery):
    from data import paywall
    item = c.data.split(":", 1)[1]
    if item not in paywall.ITEMS:
        return await c.answer()
    if paywall.has(c.from_user.id, item):
        return await c.answer("✅ Bu sizda allaqachon ochiq", show_alert=True)
    await c.answer()
    await paywall.send_invoice(c.from_user.id, item)


@dp.shutdown()
async def _close_ai_session():
    from data import gemini
    if gemini._session and not gemini._session.closed:
        await gemini._session.close()
