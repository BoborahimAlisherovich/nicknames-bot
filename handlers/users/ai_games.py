"""Kengaytirilgan AI o'yinlar: AI son topadi, tezkor matematika, ingliz tili, reyting.

Har bir to'g'ri javob ochko beradi — 🏆 Reyting bo'limida eng yaxshilar ko'rinadi.
"""
import html
import random
import time

from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from loader import db, dp


class G(StatesGroup):
    math = State()
    translate = State()


def b(text, cb, style=None):
    return InlineKeyboardButton(text=text, callback_data=cb, **({"style": style} if style else {}))


def kb(*rows):
    return InlineKeyboardMarkup(inline_keyboard=[list(r) for r in rows])


HOME = b("🎲 O'yinlar menyusi", "g:home", "danger")


def _not_menu(m: Message) -> bool:
    from handlers.users.anonymous_system import MENU_TEXTS
    return bool(m.text) and m.text not in MENU_TEXTS and not m.text.startswith("/")


async def ai(prompt: str, temp: float = 1.0) -> str | None:
    from data.gemini import ask
    return await ask(prompt, max_tokens=400, temperature=temp)


# ------------------------------------------------------------------ Ochko va reyting
def _ensure():
    db.execute("CREATE TABLE IF NOT EXISTS GameScores(user_id INTEGER PRIMARY KEY, name TEXT, points INTEGER DEFAULT 0)",
               commit=True)


def add_points(user, n: int) -> int:
    _ensure()
    db.execute("INSERT INTO GameScores(user_id, name, points) VALUES(?, ?, ?) ON CONFLICT(user_id) "
               "DO UPDATE SET points = points + excluded.points, name = excluded.name",
               (user.id, user.full_name[:40], n), commit=True)
    row = db.execute("SELECT points FROM GameScores WHERE user_id=?", (user.id,), fetchone=True)
    return row[0] if row else n


@dp.callback_query(F.data == "ag:top")
async def leaderboard(c: CallbackQuery):
    _ensure()
    rows = db.execute("SELECT user_id, name, points FROM GameScores ORDER BY points DESC LIMIT 10", fetchall=True) or []
    me = db.execute("SELECT points FROM GameScores WHERE user_id=?", (c.from_user.id,), fetchone=True)
    medals = ["🥇", "🥈", "🥉"] + [f"{i}." for i in range(4, 11)]
    lines = [f"{medals[i]} {html.escape(n or 'O‘yinchi')} — <b>{p}</b>" for i, (_, n, p) in enumerate(rows)]
    text = "🏆 <b>Reyting — TOP 10</b>\n\n" + ("\n".join(lines) or "Hali hech kim ochko yig'magan") + \
           f"\n\n⭐ Sizning ochkongiz: <b>{me[0] if me else 0}</b>"
    await c.message.answer(text, reply_markup=kb([HOME]))
    await c.answer()


# ------------------------------------------------------------------ 🤖 AI sizning soningizni topadi
@dp.callback_query(F.data == "ag:bot")
async def bot_guess_start(c: CallbackQuery, state: FSMContext):
    await state.update_data(lo=1, hi=100, n=0)
    await c.message.answer("🤖 <b>AI son topadi</b>\n\n1 dan 100 gacha bitta son o'ylang va «Tayyor» ni bosing. "
                           "Men ko'pi bilan 7 urinishda topaman! 😎", reply_markup=kb([b("✅ Tayyor", "ag:bg:go", "success")]))
    await c.answer()


@dp.callback_query(F.data.startswith("ag:bg:"))
async def bot_guess_step(c: CallbackQuery, state: FSMContext):
    d = await state.get_data()
    lo, hi, n = d.get("lo", 1), d.get("hi", 100), d.get("n", 0)
    act = c.data[6:]
    if act == "ok":
        await state.update_data(lo=1, hi=100, n=0)
        await c.message.edit_text(f"🎉 Topdim! Soningiz <b>{d.get('g')}</b> — {n} urinishda! 🤖",
                                  reply_markup=kb([b("🔁 Yana", "ag:bot", "success"), HOME]))
        return await c.answer()
    if act == "up":
        lo = d["g"] + 1
    elif act == "down":
        hi = d["g"] - 1
    if lo > hi:
        await state.update_data(lo=1, hi=100, n=0)
        await c.message.edit_text("🤨 Hmm, javoblarda xatolik bor shekilli. Qaytadan o'ynaymizmi?",
                                  reply_markup=kb([b("🔁 Qayta", "ag:bot", "success"), HOME]))
        return await c.answer()
    g = (lo + hi) // 2
    await state.update_data(lo=lo, hi=hi, n=n + 1, g=g)
    await c.message.edit_text(f"🤖 {n + 1}-urinish: sizning soningiz <b>{g}</b>mi?",
                              reply_markup=kb([b("⬆️ Kattaroq", "ag:bg:up", "primary"), b("⬇️ Kichikroq", "ag:bg:down", "primary")],
                                              [b("✅ Ha, topding!", "ag:bg:ok", "success")]))
    await c.answer()


# ------------------------------------------------------------------ ⚡ Tezkor matematika
LEVELS = {"1": ("🟢 Oson", 10, "+-"), "2": ("🟡 O'rta", 30, "+-×"), "3": ("🔴 Qiyin", 99, "+-×÷")}
ROUND = 10


def make_q(level: str):
    _, mx, ops = LEVELS[level]
    op = random.choice(ops)
    a, c = random.randint(2, mx), random.randint(2, mx)
    if op == "×":
        a, c = random.randint(2, min(mx, 12 if level == "2" else 25)), random.randint(2, 12)
        return f"{a} × {c}", a * c
    if op == "÷":
        c = random.randint(2, 12)
        res = random.randint(2, 20)
        return f"{c * res} ÷ {c}", res
    if op == "-":
        a, c = max(a, c), min(a, c)
        return f"{a} − {c}", a - c
    return f"{a} + {c}", a + c


@dp.callback_query(F.data == "ag:math")
async def math_menu(c: CallbackQuery):
    await c.message.answer("⚡ <b>Tezkor matematika</b>\n\n10 ta misol. Qancha tez va to'g'ri yechsangiz, "
                           "shuncha ko'p ochko! Darajani tanlang:",
                           reply_markup=kb([b(v[0], f"ag:m:{k}", "primary") for k, v in LEVELS.items()], [HOME]))
    await c.answer()


@dp.callback_query(F.data.startswith("ag:m:"))
async def math_start(c: CallbackQuery, state: FSMContext):
    level = c.data[5:]
    q, a = make_q(level)
    await state.set_state(G.math)
    await state.update_data(level=level, i=1, right=0, a=a, t0=time.time(), qt=time.time())
    await c.message.answer(f"⚡ 1/{ROUND}:  <b>{q} = ?</b>")
    await c.answer()


@dp.message(G.math, _not_menu)
async def math_answer(m: Message, state: FSMContext):
    d = await state.get_data()
    try:
        ok = int(m.text.strip().replace(" ", "")) == d["a"]
    except ValueError:
        return await m.answer("🔢 Faqat son yozing")
    fast = time.time() - d["qt"] < 5
    right = d["right"] + ok
    mark = ("✅" + (" ⚡" if fast else "")) if ok else f"❌ ({d['a']})"
    if d["i"] >= ROUND:
        await state.clear()
        total = time.time() - d["t0"]
        pts = right * int(d["level"]) * (2 if total < ROUND * 5 else 1)
        allp = add_points(m.from_user, pts)
        return await m.answer(f"{mark}\n\n🏁 <b>Natija:</b> {right}/{ROUND} to'g'ri\n⏱ Vaqt: {total:.1f} s\n"
                              f"⭐ +{pts} ochko (jami {allp})",
                              reply_markup=kb([b("🔁 Yana", f"ag:m:{d['level']}", "success"), b("🏆 Reyting", "ag:top", "primary")], [HOME]))
    q, a = make_q(d["level"])
    await state.update_data(i=d["i"] + 1, right=right, a=a, qt=time.time())
    await m.answer(f"{mark}\n\n⚡ {d['i'] + 1}/{ROUND}:  <b>{q} = ?</b>")


# ------------------------------------------------------------------ 🇬🇧 Ingliz tili
WORDS = [("apple", "olma"), ("book", "kitob"), ("house", "uy"), ("water", "suv"), ("friend", "do'st"),
         ("school", "maktab"), ("teacher", "o'qituvchi"), ("city", "shahar"), ("money", "pul"), ("time", "vaqt"),
         ("family", "oila"), ("happy", "xursand"), ("strong", "kuchli"), ("beautiful", "chiroyli"), ("fast", "tez"),
         ("slow", "sekin"), ("cold", "sovuq"), ("hot", "issiq"), ("road", "yo'l"), ("tree", "daraxt"),
         ("bird", "qush"), ("dog", "it"), ("cat", "mushuk"), ("sun", "quyosh"), ("moon", "oy"), ("star", "yulduz"),
         ("river", "daryo"), ("mountain", "tog'"), ("bread", "non"), ("milk", "sut"), ("window", "deraza"),
         ("door", "eshik"), ("work", "ish"), ("dream", "orzu"), ("heart", "yurak"), ("hand", "qo'l"), ("eye", "ko'z"),
         ("night", "tun"), ("morning", "ertalab"), ("answer", "javob"), ("question", "savol"), ("language", "til"),
         ("journey", "sayohat"), ("brave", "jasur"), ("clever", "aqlli"), ("lazy", "dangasa"), ("hungry", "och"),
         ("rich", "boy"), ("poor", "kambag'al"), ("young", "yosh"), ("old", "qari"), ("weather", "ob-havo"),
         ("kitchen", "oshxona"), ("library", "kutubxona"), ("hospital", "kasalxona"), ("market", "bozor"),
         ("summer", "yoz"), ("winter", "qish"), ("spring", "bahor"), ("autumn", "kuz")]


@dp.callback_query(F.data == "ag:en")
async def en_menu(c: CallbackQuery, state: FSMContext):
    await state.clear()
    await c.message.answer("🇬🇧 <b>Ingliz tili</b>\n\nO'ynab o'rganing — har to'g'ri javob ochko beradi!",
                           reply_markup=kb([b("📚 So'z tarjimasi", "ag:enw", "primary"), b("🔁 Teskari (UZ→EN)", "ag:enr", "primary")],
                                           [b("🧠 AI grammatika testi", "ag:eng", "success")],
                                           [b("✍️ Gap tarjima (AI tekshiradi)", "ag:ent", "success")],
                                           [HOME]))
    await c.answer()


async def _choice(c: CallbackQuery, state: FSMContext, question: str, opts: list[str], right: str, nxt: str, tag: str):
    random.shuffle(opts)
    await state.update_data(en_right=right, en_next=nxt)
    rows = [[b(o, f"ag:ea:{int(o == right)}", "primary")] for o in opts]
    await c.message.answer(f"{tag}\n\n{question}", reply_markup=kb(*rows))


@dp.callback_query(F.data.in_({"ag:enw", "ag:enr"}))
async def en_words(c: CallbackQuery, state: FSMContext):
    await c.answer()
    w = random.sample(WORDS, 4)
    rev = c.data == "ag:enr"
    en, uz = w[0]
    if rev:
        await _choice(c, state, f"«<b>{uz}</b>» inglizcha qanday?", [x[0] for x in w], en, c.data, "🔁 <b>UZ → EN</b>")
    else:
        await _choice(c, state, f"«<b>{en}</b>» so'zining tarjimasi?", [x[1] for x in w], uz, c.data, "📚 <b>So'z tarjimasi</b>")


@dp.callback_query(F.data == "ag:eng")
async def en_grammar(c: CallbackQuery, state: FSMContext):
    await c.answer("⏳")
    res = await ai("Create ONE English grammar multiple-choice question for an Uzbek learner (A2-B1 level, "
                   "fill in the blank with ___). Output exactly one line: "
                   "QUESTION|option1|option2|option3|option4|correct_number(1-4)")
    q = None
    try:
        p = [x.strip() for x in res.strip().splitlines()[0].split("|")]
        if len(p) == 6:
            q = (p[0], p[1:5], p[1:5][int(p[5]) - 1])
    except Exception:
        pass
    q = q or random.choice([("She ___ to school every day.", ["goes", "go", "going", "gone"], "goes"),
                            ("I have ___ apple.", ["an", "a", "the", "-"], "an"),
                            ("They ___ football yesterday.", ["played", "play", "plays", "playing"], "played")])
    await _choice(c, state, html.escape(q[0]), list(q[1]), q[2], "ag:eng", "🧠 <b>Grammatika</b>")


@dp.callback_query(F.data.startswith("ag:ea:"))
async def en_answer(c: CallbackQuery, state: FSMContext):
    d = await state.get_data()
    ok = c.data.endswith("1")
    pts = add_points(c.from_user, 2) if ok else None
    try:
        await c.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    text = f"✅ To'g'ri! +2 ⭐ (jami {pts})" if ok else f"❌ Noto'g'ri. To'g'ri javob: <b>{html.escape(d.get('en_right', ''))}</b>"
    await c.message.answer(text, reply_markup=kb([b("➡️ Keyingisi", d.get("en_next", "ag:en"), "success"),
                                                  b("🇬🇧 Menyu", "ag:en", "primary")]))
    await c.answer()


@dp.callback_query(F.data == "ag:ent")
async def en_translate(c: CallbackQuery, state: FSMContext):
    await c.answer("⏳")
    s = await ai("Write ONE short simple Uzbek sentence (5-9 words, Latin script) for an English learner to translate. "
                 "Output only the sentence.")
    s = (s or random.choice(["Men har kuni ertalab kitob o'qiyman.", "Bugun havo juda issiq.",
                             "Do'stim bilan bozorga bordik."])).strip().strip('"')
    await state.set_state(G.translate)
    await state.update_data(src=s)
    await c.message.answer(f"✍️ <b>Inglizchaga tarjima qiling:</b>\n\n🇺🇿 {html.escape(s)}")


@dp.message(G.translate, _not_menu)
async def en_translate_check(m: Message, state: FSMContext):
    src = (await state.get_data()).get("src", "")
    await state.clear()
    await m.bot.send_chat_action(m.chat.id, "typing")
    res = await ai(f"Uzbek sentence: {src}\nStudent's English translation: {m.text}\n"
                   "Evaluate in Uzbek (Latin). Format exactly:\nBALL: <0-10>\nTO'G'RI VARIANT: <correct English>\n"
                   "IZOH: <1-2 short sentences about mistakes>", temp=0.3)
    score = 0
    if res:
        for line in res.splitlines():
            if line.upper().startswith("BALL"):
                import re
                found = re.search(r"\d+", line.split(":", 1)[-1])
                score = min(10, int(found.group())) if found else 0
    pts = add_points(m.from_user, score // 2) if score else None
    body = html.escape(res) if res else "⚠️ AI hozir tekshira olmadi."
    extra = f"\n\n⭐ +{score // 2} ochko (jami {pts})" if pts else ""
    await m.answer(f"🧑‍🏫 <b>Natija</b>\n\n{body}{extra}",
                   reply_markup=kb([b("➡️ Yana gap", "ag:ent", "success"), b("🇬🇧 Menyu", "ag:en", "primary")]))
