"""Parol generatori - 3 xil uslub.

1. 🧠 Eslab qoladigan: 3-4 ta o'zbekcha so'z + raqam (passphrase uslubi)
2. 🗣 Talaffuz qilinadigan: bo'g'inlardan tuzilgan (Bavu-Keti-29)
3. 💪 Super kuchli: tasodifiy belgilar (eski uslub, xakerlar uchun)

Har bir parol bilan uning quvvati (taxminiy kraker vaqti) ko'rsatiladi.
"""
import secrets
import math
import random
import string
import html
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import StateFilter
from aiogram import F
from loader import dp, db
from data.texts import get_texts
from data.buttons import icon_button

texts = get_texts()

pwd_button_texts = [
    texts["uz"]["menu"]["menu_button_10"],
    texts["us"]["menu"]["menu_button_10"],
    texts["ru"]["menu"]["menu_button_10"],
]


class PwdStates(StatesGroup):
    WaitingForBase = State()


# ------------------------------------------------------------------
# So'z bazasi (o'zbekcha, eslab qolish oson)
# ------------------------------------------------------------------
UZ_WORDS = [
    "Olma", "Oy", "Yulduz", "Dengiz", "Quyon", "Sher", "Burgut", "Tog'",
    "Daryo", "Gul", "Baxt", "Qaldirgo", "Chinor", "Novda", "Bolajon",
    "Do'st", "Jasur", "Shirin", "Osiyo", "Bahor", "Kuz", "Yomg'ir",
    "Qor", "Shabadal", "Sohil", "Osmon", "Bulut", "Shamol", "Farg'ona",
    "Samarqand", "Buxoro", "Xiva", "Termiz", "Andijon", "Namangan",
    "Kaptar", "Chumoli", "Ilg'ich", "Burchak", "Do'pi", "Choy",
    "Osh", "Somun", "Suv", "Kelajak", "Orzu", "Nur", "Ilhom",
]

SYLLABLES = ["ba", "vu", "ke", "ti", "mo", "ra", "zu", "li", "sha", "no",
             "ga", "du", "mi", "ta", "vo", "ki", "se", "bu", "la", "ny"]

STYLES = {
    "memorable": {
        "uz": "🟦 🧠 Eslab qoladigan", "us": "🟦 🧠 Memorable", "ru": "🟦 🧠 Запоминающийся",
    },
    "speakable": {
        "uz": "🟩 🗣 Talaffuz qilinadigan", "us": "🟩 🗣 Speakable", "ru": "🟩 🗣 Произносимый",
    },
    "strong": {
        "uz": "🟥 💪 Super kuchli", "us": "🟥 💪 Super strong", "ru": "🟥 💪 Супер-надёжный",
    },
}


def generate_memorable_from_word(base_word: str) -> str:
    """Ism/so'z asosida eslab qoladigan parol: Salom-Qaldirgo47-Nur!"""
    base = base_word.strip().capitalize()[:14]
    helper = random.choice(UZ_WORDS)
    digits = random.randint(10, 99)
    symbol = random.choice("!?*#@%$")
    tail = random.choice(UZ_WORDS)
    return f"{base}-{helper}{digits}-{tail}{symbol}"


def generate_speakable_from_word(base_word: str) -> str:
    """Ism/so'z asosida talaffuz qilinadigan parol: Salom-Vubu-42"""
    base = base_word.strip().capitalize()[:14]
    syl1 = "".join(random.sample(SYLLABLES, 2)).capitalize()
    syl2 = "".join(random.sample(SYLLABLES, 2))
    digits = random.randint(10, 99)
    return f"{base}-{syl1}{syl2}-{digits}"


def generate_memorable_password() -> str:
    """4 ta so'z + 2 ta raqam: Olma-Kaptar-73-Farg'ona"""
    words = random.sample(UZ_WORDS, 3)
    digits = random.randint(10, 99)
    parts = [words[0], f"{words[1]}{digits}", words[2]]
    # bir so'zga belgi qo'shamiz
    symbols = "!?*#@%$"
    parts.append(f"{words[2]}{random.choice(symbols)}" if random.random() < 0.5 else random.choice(UZ_WORDS))
    return "-".join(parts[:4])


def generate_speakable_password() -> str:
    """Bo'g'inlardan tuzilgan: Bavu-Keti-29-Mora"""
    parts = []
    for _ in range(2):
        word = "".join(random.sample(SYLLABLES, 2))
        word = word.capitalize()
        parts.append(word)
    parts.append(str(random.randint(10, 99)))
    if random.random() < 0.6:
        parts.append(random.choice(UZ_WORDS))
    return "-".join(parts)


def generate_strong_password(length=16):
    """Tasodifiy belgilar - eski kuchli uslub (maxfiylik uchun)"""
    chars = string.ascii_letters + string.digits + "!@#$%^&*()_+-="
    password = [
        random.choice(string.ascii_lowercase),
        random.choice(string.ascii_uppercase),
        random.choice(string.digits),
        random.choice("!@#$%^&*")
    ]
    password += [secrets.choice(chars) for _ in range(length - 4)]
    random.shuffle(password)
    return "".join(password)


def scramble_word(word):
    """Ism/so'zdan kuchli parol (eski funksiya - qoldirildi)"""
    symbols = "!@#$%^&*"
    digits = "0123456789"
    result = ""
    for char in word:
        chance = random.random()
        if chance < 0.3:
            result += random.choice(symbols)
        elif chance < 0.6:
            result += random.choice(digits)
        if char.isalpha() and random.random() > 0.7:
            char = char.swapcase()
        result += char
        if random.random() > 0.7:
            result += random.choice(symbols)
    while len(result) < 12:
        result += random.choice(symbols + digits + string.ascii_letters)
    return result


def password_strength(password: str) -> tuple[str, str]:
    """(daraja emojisi, taxminiy kraker vaqti)"""
    charset = 0
    if any(c.islower() for c in password):
        charset += 26
    if any(c.isupper() for c in password):
        charset += 26
    if any(c.isdigit() for c in password):
        charset += 10
    if any(c in "!@#$%^&*()_+-=!?#%$" for c in password):
        charset += 10
    # o'zbekcha harflar ham alifboga kiradi
    if any(c.isalpha() and c not in string.ascii_letters for c in password):
        charset += 10

    if charset == 0:
        charset = 26
    entropy = len(password) * math.log2(max(charset, 2))
    guesses = 2 ** entropy
    # sekundiga 100 mlrd taxmin (GPU farm) - taxminiy
    seconds = guesses / 1e11

    if seconds > 3.15e16:  # 1 mlrd yil+
        level, time_str = "🛡🛡🛡🛡🛡", "bir milliard yildan ko'p"
    elif seconds > 3.15e13:  # 1 mln yil+
        level, time_str = "🛡🛡🛡🛡", "million yillar"
    elif seconds > 3.15e10:  # 1000 yil+
        level, time_str = "🛡🛡🛡", "ming yillar"
    elif seconds > 3.15e7:  # 1 yil+
        level, time_str = "🛡🛡", "yillar"
    else:
        level, time_str = "🛡", "kunlar"

    return level, time_str


def format_password_response(password: str, language: str) -> str:
    level, time_str = password_strength(password)
    texts_fmt = {
        "uz": f"✅ <b>Sizning parolingiz:</b>\n\n<code>{html.escape(password)}</code>\n\n"
              f"{level} Quvvat: kraker uchun <b>~{time_str}</b> kerak bo'lardi\n"
              "👆 Nusxa olish uchun parolni ustiga bosing!",
        "us": f"✅ <b>Your password:</b>\n\n<code>{html.escape(password)}</code>\n\n"
              f"{level} Strength: a cracker would need <b>~{time_str}</b>\n"
              "👆 Click the password to copy!",
        "ru": f"✅ <b>Ваш пароль:</b>\n\n<code>{html.escape(password)}</code>\n\n"
              f"{level} Надёжность: взлому нужно <b>~{time_str}</b>\n"
              "👆 Нажмите на пароль чтобы скопировать!",
    }
    return texts_fmt.get(language, texts_fmt["us"])


def main_menu_markup(language: str):
    markup = InlineKeyboardBuilder()
    for key, labels in STYLES.items():
        markup.row(icon_button(
            labels.get(language, labels["us"]),
            callback_data=f"pwd_{key}",
            style_key=key,
        ))
    markup.row(icon_button(
        {"uz": "🎲 Tasodifiy (ismsiz)", "us": "🎲 Random (no name)", "ru": "🎲 Случайный (без имени)"}[language],
        callback_data="pwd_random",
        style_key="random",
    ))
    markup.row(icon_button(
        texts.get(language, {}).get("back_button", "♻️ Back"),
        callback_data="back_to_menu",
        style_key="back",
    ))
    return markup.as_markup()


@dp.message(F.text.in_(pwd_button_texts), StateFilter("*"))
async def password_generator_handler(message: Message, state: FSMContext):
    await state.clear()
    telegram_id = message.from_user.id
    user = db.select_user_by_id(telegram_id=telegram_id)
    language = user[2] if user else "uz"

    welcome = {
        "uz": "🔐 <b>Xavfsiz Parol Generatori</b>\n\n"
              "1️⃣ Avval uslubni tanlang:\n"
              "🧠 <b>Eslab qoladigan</b> - Olma-Kaptar-73-Farg'ona (odamlar eslaydi!)\n"
              "🗣 <b>Talaffuz qilinadigan</b> - Bavu-Keti-29 (aytish oson)\n"
              "💪 <b>Super kuchli</b> - x9$Qm!zP (xakerlarga qarshi, eslab qolish qiyin)\n\n"
              "2️⃣ So'ng ismingizni yoki biror so'z yuboring - parol aynan shu uslubda yaratiladi.",
        "us": "🔐 <b>Secure Password Generator</b>\n\n"
              "1️⃣ Pick a style\n2️⃣ Then send your name or a word.",
        "ru": "🔐 <b>Генератор паролей</b>\n\n"
              "1️⃣ Выберите стиль\n2️⃣ Затем отправьте имя или слово.",
    }

    await message.answer(
        welcome.get(language, welcome["us"]),
        reply_markup=main_menu_markup(language),
        parse_mode="HTML"
    )


@dp.callback_query(F.data.startswith("pwd_"))
async def pwd_choose_style(callback: CallbackQuery, state: FSMContext):
    action = callback.data.replace("pwd_", "")
    user = db.select_user_by_id(telegram_id=callback.from_user.id)
    language = user[2] if user else "uz"

    if action == "random":
        password = generate_strong_password()
        await callback.message.answer(
            format_password_response(password, language),
            parse_mode="HTML"
        )
        await callback.answer()
        return

    # Uslub tanlandi - endi so'z kutamiz
    await state.clear()
    await state.set_state(PwdStates.WaitingForBase)
    await state.update_data(pwd_style=action)

    style_label = STYLES.get(action, {}).get(language, action)
    ask = {
        "uz": f"✍️ <b>{style_label}</b> uslubi tanlandi.\n\nEndi ismingizni yoki biror so'z yuboring - parol shu uslubda yaratiladi:",
        "us": f"✍️ <b>{style_label}</b> style selected.\n\nNow send your name or a word:",
        "ru": f"✍️ <b>{style_label}</b> стиль выбран.\n\nТеперь отправьте имя или слово:",
    }
    await callback.message.answer(ask.get(language, ask["us"]), parse_mode="HTML")
    await callback.answer()


@dp.message(PwdStates.WaitingForBase)
async def handle_pwd_base(message: Message, state: FSMContext):
    if not message.text:
        return

    if message.text.startswith("📝") or message.text.startswith("🎮") or message.text.startswith("🕵️") or message.text.startswith("📙") or message.text.startswith("/"):
        return

    base_word = message.text.strip()
    data = await state.get_data()
    style = data.get("pwd_style", "strong")

    if style == "memorable":
        password = generate_memorable_from_word(base_word)
    elif style == "speakable":
        password = generate_speakable_from_word(base_word)
    else:
        password = scramble_word(base_word)

    telegram_id = message.from_user.id
    user = db.select_user_by_id(telegram_id=telegram_id)
    language = user[2] if user else "uz"

    await message.answer(
        format_password_response(password, language),
        parse_mode="HTML"
    )
    await state.clear()
