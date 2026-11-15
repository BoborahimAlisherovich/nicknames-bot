"""Stikerlar bo'limi - admin boshqaradigan tizim.

FOYDALANUVCHI uchun:
- ⭐ Stikerlar: admin to'plagan umumiy kolleksiya - stikerni bosing, darhol yuboriladi
- 📦 Paketlar: bot paketlari (paket ichidan stiker tanlash)
- 🌍 Telegram trend paketlari: t.me/addstickers linklar (bir bosishda o'rnatish)

ADMIN uchun (faqat admin qo'shadi/o'chiradi):
- ⭐ Stikerlar ichida "➕ Stiker qo'shish" tugmasi yoki /stadd_shared buyrug'i
  → botga stikerlar yuboriladi (forward qilsa ham bo'ladi) → /stshdone yoki
  "✅ Bajarildi" tugmasi bilan yakunlanadi
- 🗑 O'chirish tugmasi - kolleksiyadan stiker olib tashlash
- /stpack <nomi>          yangi paket yaratish
- /stpacks                paketlar ro'yxati
- /stadd <id>             paketga stiker qo'shish rejimi
- /stdelpack <id>         paketni o'chirish
"""
import html
import logging

from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import StateFilter
from aiogram import F
from loader import dp, db, bot
from data.texts import get_texts
from filterss.admin import IsBotAdminFilter
from data.config import ADMINS
from data.buttons import icon_button, styled_text

logger = logging.getLogger(__name__)
texts = get_texts()

# Tekshirilgan (real mavjud) Telegram paketlari - static ro'yxat
# Mashhur Telegram paketlari (nomzodlar). Bot ishga tushganda har biri
# getStickerSet bilan TEKSHIRILADI - mavjud bo'lmaganlari ro'yxatga chiqmaydi.
STATIC_PACKS = [{"name": n, "title": t} for n, t in [
    ("UtyaDuck", "🦆 Utya Duck"), ("UtyaWinter", "❄️ Utya Winter"), ("UtyaNewYear", "🎄 Utya New Year"),
    ("UtyaHalloween", "🎃 Utya Halloween"), ("UtyaBirthday", "🎂 Utya Birthday"), ("UtyaAghori", "😎 Utya Aghori"),
    ("UtyaDuckFull", "🦆 Utya Full"), ("HotCherry", "🍒 Hot Cherry"), ("PepoCrypto", "🐸 Pepo Crypto"),
    ("AnimatedEmojies", "✨ Animated Emoji"), ("EmojiAnimations", "🎬 Emoji Animations"), ("TgCat", "🐱 Telegram Cat"),
    ("Animals", "🐾 Animals"), ("ChristmasDuck", "🎅 Christmas Duck"), ("DuckDuck", "🦆 Duck Duck"),
    ("Pepe", "🐸 Pepe"), ("PepeTheFrog", "🐸 Pepe the Frog"), ("FroggyFrog", "🐸 Froggy"), ("SadPepe", "😢 Sad Pepe"),
    ("CuteCats", "😺 Cute Cats"), ("Cats", "🐈 Cats"), ("Catsss", "🐈 Catsss"), ("MemeCats", "😹 Meme Cats"),
    ("Doge", "🐕 Doge"), ("DogeMemes", "🐕 Doge Memes"), ("ShibaInu", "🐶 Shiba Inu"), ("Corgi", "🐶 Corgi"),
    ("Panda", "🐼 Panda"), ("BearBrown", "🐻 Brown Bear"), ("Bunny", "🐰 Bunny"), ("Penguin", "🐧 Penguin"),
    ("Hamster", "🐹 Hamster"), ("Bobr", "🦫 Bobr"), ("MrBean", "🤵 Mr Bean"), ("Shrek", "🟢 Shrek"),
    ("SpongeBob", "🧽 SpongeBob"), ("Minions", "💛 Minions"), ("Pikachu", "⚡ Pikachu"), ("Pokemon", "🔴 Pokemon"),
    ("Naruto", "🍥 Naruto"), ("OnePiece", "🏴‍☠️ One Piece"), ("Anime", "🌸 Anime"), ("Memes", "😂 Memes"),
    ("Mems", "😂 Mems"), ("Uzbek", "🇺🇿 Uzbek"), ("UzbekMemes", "🇺🇿 Uzbek Memes"), ("Love", "❤️ Love"),
    ("Hearts", "💖 Hearts"), ("Kolobok", "🟡 Kolobok"), ("Smileys", "🙂 Smileys"), ("Emoji", "😀 Emoji"),
]]

_verified_cache: dict = {"at": 0.0, "packs": []}


async def verified_packs() -> list[dict]:
    """Haqiqatan mavjud paketlar (6 soat keshlanadi). Sarlavha Telegram'dan olinadi."""
    import asyncio
    import time as _t
    if _verified_cache["packs"] and _t.time() - _verified_cache["at"] < 6 * 3600:
        return _verified_cache["packs"]
    sem = asyncio.Semaphore(8)

    async def check(p):
        async with sem:
            try:
                st = await bot.get_sticker_set(p["name"])
                return {"name": st.name, "title": p["title"], "count": len(st.stickers), "set": st}
            except Exception:
                return None

    res = [r for r in await asyncio.gather(*(check(p) for p in STATIC_PACKS)) if r]
    _verified_cache.update(at=_t.time(), packs=res)
    return res


async def fill_shared(per_pack: int = 6, added_by: int = 0) -> int:
    """Umumiy kolleksiyani mashhur paketlardan to'ldiradi (dublikatsiz)."""
    have = {row[1] for row in (db.get_shared_stickers() or [])}
    added = 0
    for p in await verified_packs():
        for st in p["set"].stickers[:per_pack]:
            if st.file_id not in have:
                db.add_shared_sticker(st.file_id, f"{p['title']} {st.emoji or ''}".strip(), added_by)
                have.add(st.file_id)
                added += 1
    return added


@dp.startup()
async def _auto_fill_stickers():
    """Kolleksiya bo'sh bo'lsa, bot ishga tushganda avtomatik to'ldiriladi."""
    import asyncio

    async def job():
        try:
            if db.count_shared_stickers() == 0:
                n = await fill_shared()
                logger.info("Stiker kolleksiyasi avtomatik to'ldirildi: %s ta", n)
        except Exception as e:
            logger.warning("Stikerlarni to'ldirib bo'lmadi: %s", e)
    asyncio.create_task(job())


@dp.message(F.text.in_(["/stfill", "🔥 Stikerlarni to'ldirish"]), IsBotAdminFilter(ADMINS), StateFilter("*"))
async def admin_fill_stickers(message: Message, state: FSMContext):
    await state.clear()
    wait = await message.answer("⏳ Mashhur paketlar tekshirilmoqda va kolleksiya to'ldirilmoqda...")
    _verified_cache["at"] = 0
    n = await fill_shared(added_by=message.from_user.id)
    packs = await verified_packs()
    await wait.edit_text(f"✅ Tayyor!\n📦 Ishlaydigan paketlar: {len(packs)} ta\n"
                         f"⭐ Kolleksiyaga qo'shildi: {n} ta stiker\n"
                         f"📊 Jami kolleksiyada: {db.count_shared_stickers()} ta")


ST_PER_PAGE = 10


class StickerAdminStates(StatesGroup):
    AddingSticker = State()   # admin paketga stiker qo'shyapti
    CreatingPack = State()    # admin yangi paket nomini kiritmoqda
    AddingShared = State()    # admin umumiy kolleksiyaga stiker qo'shyapti


def _lang(user_id) -> str:
    user = db.select_user_by_id(telegram_id=user_id)
    return user[2] if user else "uz"


def _back_btn(callback_target: str, language: str):
    return InlineKeyboardButton(
        text="♻️ Orqaga" if language == "uz" else "♻️ Back",
        callback_data=callback_target
    )


@dp.message(F.text.in_(["🔥 Mashhur Stikerlar", "🔥 Popular Stickers", "🔥 Популярные стикеры"]), StateFilter("*"))
async def stickers_menu(message: Message, state: FSMContext):
    await state.clear()
    await _show_stickers_main(message, message.from_user.id)


async def _show_stickers_main(message, user_id: int):
    language = _lang(user_id)
    packs = db.get_sticker_packs()
    shared_count = db.count_shared_stickers()

    markup = InlineKeyboardBuilder()
    markup.row(icon_button(
        styled_text("stickers", f"Stikerlar ({shared_count})"),
        callback_data="st_shared",
        style_key="stickers",
    ))
    if packs:
        markup.row(icon_button(
            styled_text("packs", f"Bot paketlari ({len(packs)})"),
            callback_data="stpack_list",
            style_key="packs",
        ))
    markup.row(icon_button(
        styled_text("trend", "Telegram trend paketlari"),
        callback_data="stpack_static",
        style_key="trend",
    ))
    markup.row(icon_button(
        "♻️ Orqaga" if language == "uz" else "♻️ Back",
        callback_data="back_to_menu",
        style_key="back",
    ))

    is_admin = user_id in ADMINS
    text = (
        "🔥 <b>Stikerlar</b>\n\n"
        f"⭐ <b>Stikerlar</b> - tanlangan kolleksiya ({shared_count} ta) - "
        "stikerni bosing, darhol yuboriladi\n"
        "📦 <b>Bot paketlari</b> - paket ichidan tanlab yuborish\n"
        "🌍 <b>Telegram trend paketlari</b> - butun paketni BIR BOSISHDA o'rnatish linklari\n"
    )
    if is_admin:
        text += "\n👑 <i>Admin: ⭐ Stikerlar ichida ➕ qo'shish / 🗑 o'chirish tugmalari bor</i>"
    if isinstance(message, CallbackQuery):
        try:
            await message.message.delete()
        except Exception:
            pass
        await message.message.answer(text, parse_mode="HTML", reply_markup=markup.as_markup())
        await message.answer()
    else:
        await message.answer(text, parse_mode="HTML", reply_markup=markup.as_markup())


# ---------------- Bot paketlari (DB) ----------------

@dp.callback_query(F.data == "stpack_list")
async def sticker_packs_list(callback: CallbackQuery):
    language = _lang(callback.from_user.id)
    packs = db.get_sticker_packs()

    markup = InlineKeyboardBuilder()
    for pack_id, title, count in packs:
        markup.row(InlineKeyboardButton(
            text=f"{title} ({count} ta)",
            callback_data=f"stpk_{pack_id}"
        ))
    markup.row(icon_button("♻️ Orqaga", callback_data="st_menu", style_key="back"))

    try:
        await callback.message.edit_text(
            "⭐ <b>Bot paketlari</b> - tanlang:",
            parse_mode="HTML",
            reply_markup=markup.as_markup()
        )
    except Exception:
        await callback.message.answer(
            "⭐ <b>Bot paketlari</b> - tanlang:",
            parse_mode="HTML",
            reply_markup=markup.as_markup()
        )
    await callback.answer()


@dp.callback_query(F.data == "st_menu")
async def stickers_main_callback(callback: CallbackQuery):
    await _show_stickers_main(callback, callback.from_user.id)


@dp.callback_query(F.data.startswith("stpk_"))
async def open_sticker_pack(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    pack_id = int(callback.data.replace("stpk_", ""))
    language = _lang(callback.from_user.id)
    stickers = db.get_pack_stickers(pack_id)

    if not stickers:
        await callback.answer("❌ Bu paketda hozircha stiker yo'q", show_alert=True)
        return

    markup = InlineKeyboardBuilder()
    for idx, (row_id, file_id, title) in enumerate(stickers[:30], 1):
        label = title if title else f"Stiker #{idx}"
        markup.row(InlineKeyboardButton(text=f"💫 {label}", callback_data=f"stsendpk_{row_id}"))
    markup.row(icon_button(
        styled_text("add", "Stiker qo'shish") if callback.from_user.id in ADMINS else "👤 Admin uchun",
        callback_data=f"staddpk_{pack_id}",
        style_key="add",
    ))
    markup.row(icon_button("♻️ Orqaga", callback_data="stpack_list", style_key="back"))

    title_row = db.get_sticker_packs()
    pack_title = next((t for pid, t, c in title_row if pid == pack_id), "Paket")

    try:
        await callback.message.edit_text(
            f"📦 <b>{html.escape(str(pack_title))}</b> ({len(stickers)} ta stiker)\n\n"
            "Stikerni bosing - darhol yuboriladi.\n"
            "💡 Yuborilgan stikerni ustiga bosib <b>Add to Favorites</b> qiling!",
            parse_mode="HTML",
            reply_markup=markup.as_markup()
        )
    except Exception:
        await callback.message.answer(
            f"📦 <b>{html.escape(str(pack_title))}</b> ({len(stickers)} ta stiker)",
            parse_mode="HTML",
            reply_markup=markup.as_markup()
        )
    await callback.answer()


@dp.callback_query(F.data.startswith("stsendpk_"))
async def send_pack_sticker(callback: CallbackQuery):
    row_id = int(callback.data.replace("stsendpk_", ""))
    row = db.get_pack_sticker_file(row_id)
    if not row:
        await callback.answer("❌ Stiker topilmadi", show_alert=True)
        return
    pack_id, file_id, title = row
    try:
        await bot.send_sticker(chat_id=callback.from_user.id, sticker=file_id)
        await callback.answer("✅ Yuborildi! Add to Favorites qiling 💡")
    except Exception as e:
        logger.warning(f"Paket stikerni yuborishda xato: {e}")
        await callback.answer("❌ Yuborilmadi", show_alert=True)


# ---------------- Admin: paket yaratish/qo'shish ----------------

@dp.message(F.text.startswith("/stpacks"), IsBotAdminFilter(ADMINS), StateFilter("*"))
async def admin_list_packs(message: Message, state: FSMContext):
    await state.clear()
    packs = db.get_sticker_packs()
    if not packs:
        await message.answer("Paketlar yo'q. Yaratish: /stpack Nomi")
        return
    text = "📦 <b>Paketlar:</b>\n\n" + "\n".join(
        f"{pid}. <b>{html.escape(str(title))}</b> ({count} ta)" for pid, title, count in packs
    )
    text += "\n\nO'chirish: /stdelpack <id>"
    await message.answer(text, parse_mode="HTML")


@dp.message(F.text.startswith("/stdelpack"), IsBotAdminFilter(ADMINS), StateFilter("*"))
async def admin_delete_pack(message: Message, state: FSMContext):
    await state.clear()
    try:
        pack_id = int(message.text.split()[1])
    except (IndexError, ValueError):
        await message.answer("Foydalanish: /stdelpack <id>")
        return
    db.delete_sticker_pack(pack_id)
    await message.answer(f"🗑 Paket #{pack_id} o'chirildi.")


@dp.message(F.text.startswith("/stpack "), IsBotAdminFilter(ADMINS), StateFilter("*"))
async def admin_create_pack(message: Message, state: FSMContext):
    await state.clear()
    title = message.text.replace("/stpack ", "", 1).strip()
    if not title:
        await message.answer("Foydalanish: /stpack Paket nomi")
        return
    db.add_sticker_pack(title, message.from_user.id)
    packs = db.get_sticker_packs()
    new_id = packs[-1][0] if packs else None
    await message.answer(
        f"✅ Paket yaratildi: <b>{html.escape(title)}</b> (id: {new_id})\n\n"
        f"Stiker qo'shish: <code>/stadd {new_id}</code>",
        parse_mode="HTML"
    )


@dp.message(F.text.startswith("/stadd "), IsBotAdminFilter(ADMINS), StateFilter("*"))
async def admin_add_sticker_start(message: Message, state: FSMContext):
    try:
        pack_id = int(message.text.split()[1])
    except (IndexError, ValueError):
        await message.answer("Foydalanish: /stadd <pack_id>")
        return
    packs = db.get_sticker_packs()
    if not any(pid == pack_id for pid, _, _ in packs):
        await message.answer("❌ Bunday paket yo'q. /stpacks bilan ro'yxatni ko'ring.")
        return
    await state.clear()
    await state.set_state(StickerAdminStates.AddingSticker)
    await state.update_data(pack_id=pack_id)
    await message.answer(
        f"➕ Paket #{pack_id}ga stiker qo'shish rejimi.\n"
        "Endi botga stikerlarni yuboring (bir nechta yuborishingiz mumkin).\n"
        "Bitirish uchun: /stadd_done"
    )


@dp.message(F.text == "/stadd_done", StickerAdminStates.AddingSticker)
async def admin_add_sticker_done(message: Message, state: FSMContext):
    data = await state.get_data()
    pack_id = data.get("pack_id")
    count = db.count_pack_stickers(pack_id)
    await state.clear()
    await message.answer(f"✅ Bajarildi! Paket #{pack_id}da jami {count[0] if count else 0} ta stiker.")


@dp.message(StickerAdminStates.AddingSticker, F.sticker)
async def admin_add_sticker(message: Message, state: FSMContext):
    data = await state.get_data()
    pack_id = data.get("pack_id")
    sticker = message.sticker
    title = sticker.emoji or f"Stiker"
    try:
        db.add_pack_sticker(pack_id, sticker.file_id, title)
        count = db.count_pack_stickers(pack_id)
        await message.answer(f"➕ Qo'shildi! (jami {count[0] if count else 1} ta)")
    except Exception as e:
        logger.warning(f"Pak stiker qo'shishda xato: {e}")
        await message.answer("❌ Saqlanmadi, qayta urinib ko'ring.")


# "➕ Stiker qo'shish" tugmasi (admin)
@dp.callback_query(F.data.startswith("staddpk_"))
async def add_sticker_via_button(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMINS:
        await callback.answer("❌ Faqat admin", show_alert=True)
        return
    pack_id = int(callback.data.replace("staddpk_", ""))
    await state.clear()
    await state.set_state(StickerAdminStates.AddingSticker)
    await state.update_data(pack_id=pack_id)
    await callback.message.answer(
        f"➕ Paket #{pack_id}ga stiker qo'shish rejimi.\n"
        "Endi botga stikerlarni yuboring.\nBitirish: /stadd_done"
    )
    await callback.answer()


# ---------------- Telegram statik paketlari ----------------

@dp.callback_query(F.data == "stpack_static")
async def static_packs(callback: CallbackQuery):
    language = _lang(callback.from_user.id)

    await callback.answer("⏳")
    packs = await verified_packs() or [dict(p, count=0) for p in STATIC_PACKS[:10]]
    markup = InlineKeyboardBuilder()
    for p in packs[:60]:
        markup.button(text=f"{p['title']} ({p['count']})" if p["count"] else p["title"],
                      url=f"https://t.me/addstickers/{p['name']}")
    markup.adjust(2)
    markup.row(icon_button("♻️ Orqaga", callback_data="st_menu", style_key="back"))

    try:
        await callback.message.edit_text(
            "🌍 <b>Telegram trend paketlari</b>\n\n"
            "Bosib oching va <b>ADD STICKERS</b> tugmasini bosing - "
            "butun paket bir bosishda o'rnatiladi!",
            parse_mode="HTML",
            reply_markup=markup.as_markup()
        )
    except Exception:
        await callback.message.answer(
            "🌍 <b>Telegram trend paketlari</b>",
            parse_mode="HTML",
            reply_markup=markup.as_markup()
        )


# ---------------- ⭐ Umumiy stikerlar kolleksiyasi (faqat admin qo'shadi) ----------------

SH_PER_PAGE = 8


def _shared_markup(page: int, is_admin: bool, language: str):
    rows = db.get_shared_stickers()
    start = page * SH_PER_PAGE
    chunk = rows[start:start + SH_PER_PAGE]

    markup = InlineKeyboardBuilder()
    if chunk:
        for row_id, file_id, title in chunk:
            markup.row(icon_button(
                f"💫 {title}",
                callback_data=f"stshsend_{row_id}",
            ))
        nav = []
        if page > 0:
            nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"stshpg_{page-1}"))
        if start + SH_PER_PAGE < len(rows):
            nav.append(InlineKeyboardButton(text="➡️", callback_data=f"stshpg_{page+1}"))
        if nav:
            markup.row(*nav)
        if is_admin:
            markup.row(icon_button(
                styled_text("add", "Stiker qo'shish"),
                callback_data="stshadd",
                style_key="add",
            ))
            markup.row(icon_button(
                styled_text("delete", "O'chirish rejimi"),
                callback_data="stshdel_0",
                style_key="delete",
            ))
    else:
        if is_admin:
            markup.row(icon_button(
                styled_text("add", "Birinchi stikerni qo'shish"),
                callback_data="stshadd",
                style_key="add",
            ))
    markup.row(icon_button(
        "♻️ Orqaga",
        callback_data="st_menu",
        style_key="back",
    ))
    return markup, len(rows)


async def _show_shared(callback: CallbackQuery, page: int = 0):
    language = _lang(callback.from_user.id)
    is_admin = callback.from_user.id in ADMINS
    markup, total = _shared_markup(page, is_admin, language)

    text = (
        f"⭐ <b>Stikerlar kolleksiyasi</b> ({total} ta)\n\n"
        "Stikerni bosing - darhol yuboriladi.\n"
        "💡 Yuborilgan stikerni ustiga bosib <b>Add to Favorites</b> qilsangiz, "
        "doim qo'lingizda bo'ladi!\n"
    )
    if is_admin:
        text += "\n👑 <i>Admin bo'limi: ➕ qo'shish yoki 🗑 o'chirish mumkin (faqat sizga ko'rinadi)</i>"

    try:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=markup.as_markup())
    except Exception:
        await callback.message.answer(text, parse_mode="HTML", reply_markup=markup.as_markup())
    await callback.answer()


@dp.callback_query(F.data == "st_shared")
async def shared_stickers(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await _show_shared(callback, 0)


@dp.callback_query(F.data.startswith("stshpg_"))
async def shared_stickers_page(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    page = int(callback.data.replace("stshpg_", ""))
    await _show_shared(callback, page)


@dp.callback_query(F.data.startswith("stshsend_"))
async def send_shared_sticker(callback: CallbackQuery):
    row_id = int(callback.data.replace("stshsend_", ""))
    row = db.get_shared_sticker_file(row_id)
    if not row:
        await callback.answer("❌ Stiker topilmadi", show_alert=True)
        return
    _, file_id, title = row
    try:
        await bot.send_sticker(chat_id=callback.from_user.id, sticker=file_id)
        await callback.answer("✅ Yuborildi! Add to Favorites qiling 💡")
    except Exception as e:
        logger.warning(f"Umumiy stikerni yuborishda xato: {e}")
        await callback.answer("❌ Yuborilmadi, stiker eski bo'lishi mumkin", show_alert=True)


# --- Admin: umumiy kolleksiyaga stiker qo'shish ---

@dp.callback_query(F.data == "stshadd")
async def add_shared_start(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMINS:
        await callback.answer("❌ Faqat admin qo'sha oladi", show_alert=True)
        return
    await state.clear()
    await state.set_state(StickerAdminStates.AddingShared)
    await callback.message.answer(
        "➕ <b>Stiker qo'shish rejimi</b>\n\n"
        "Endi shu chatga stikerlarni yuboring (oddiy yoki forward qilib).\n"
        "Har biri kolleksiyaga qo'shiladi - nechta xohlasangiz shuncha.\n\n"
        "✅ Bitirish: <code>/stshdone</code> yukidagi tugma bilan",
        parse_mode="HTML",
        reply_markup=_shared_done_markup(),
    )
    await callback.answer()


def _shared_done_markup():
    markup = InlineKeyboardBuilder()
    markup.row(icon_button(
        styled_text("back", "Bajarildi"),
        callback_data="stshdone",
        style_key="back",
    ))
    return markup.as_markup()


@dp.message(F.text == "/stshdone", StickerAdminStates.AddingShared)
async def add_shared_done_cmd(message: Message, state: FSMContext):
    await state.clear()
    total = db.count_shared_stickers()
    await message.answer(f"✅ Bajarildi! Kolleksiyada jami {total} ta stiker.")


@dp.callback_query(F.data == "stshdone")
async def add_shared_done_cb(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMINS:
        await callback.answer("❌ Faqat admin", show_alert=True)
        return
    await state.clear()
    try:
        await callback.message.delete()
    except Exception:
        pass
    total = db.count_shared_stickers()
    await callback.message.answer(f"✅ Bajarildi! Kolleksiyada jami {total} ta stiker.")
    await callback.answer()


@dp.message(StickerAdminStates.AddingShared, F.sticker)
async def add_shared_sticker(message: Message, state: FSMContext):
    sticker = message.sticker
    title = sticker.emoji or (sticker.set_name or "Stiker")
    try:
        db.add_shared_sticker(sticker.file_id, title, message.from_user.id)
    except Exception as e:
        logger.warning(f"Umumiy stiker qo'shishda xato: {e}")
        await message.answer("❌ Saqlanmadi, qayta urinib ko'ring.")
        return
    total = db.count_shared_stickers()
    await message.answer(f"➕ Qo'shildi! ({html.escape(title)})\nKolleksiyada jami: {total} ta")


@dp.message(StickerAdminStates.AddingShared)
async def add_shared_hint(message: Message, state: FSMContext):
    """Stiker emas boshqa narsa yuborilsa - izoh beramiz. Buyruqlar keyingi handlerga o'tadi."""
    if message.text and message.text.startswith("/"):
        return  # None qaytadi - aiogram keyingi mos handlerni qidiradi
    await message.answer("📥 Aynan STIKER yuboring (oddiy yoki forward). Bitirish: /stshdone")


# --- Admin: umumiy kolleksiyadan o'chirish ---

@dp.callback_query(F.data.startswith("stshdel_"))
async def delete_shared_mode(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMINS:
        await callback.answer("❌ Faqat admin", show_alert=True)
        return
    await state.clear()
    page = int(callback.data.replace("stshdel_", ""))
    rows = db.get_shared_stickers()
    start = page * SH_PER_PAGE
    chunk = rows[start:start + SH_PER_PAGE]

    if not chunk:
        await callback.answer("❌ Kolleksiya bo'sh", show_alert=True)
        return

    markup = InlineKeyboardBuilder()
    for row_id, file_id, title in chunk:
        markup.row(icon_button(
            f"🗑 {title}",
            callback_data=f"stshr_{row_id}",
            style_key="delete",
        ))
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="⬅️", callback_data=f"stshdel_{page-1}"))
    if start + SH_PER_PAGE < len(rows):
        nav.append(InlineKeyboardButton(text="➡️", callback_data=f"stshdel_{page+1}"))
    if nav:
        markup.row(*nav)
    markup.row(icon_button("♻️ Orqaga", callback_data="st_shared", style_key="back"))

    try:
        await callback.message.edit_text(
            "🗑 <b>Qaysi stikerni o'chiramiz?</b> (bosing)",
            parse_mode="HTML",
            reply_markup=markup.as_markup()
        )
    except Exception:
        await callback.message.answer(
            "🗑 <b>Qaysi stikerni o'chiramiz?</b> (bosing)",
            parse_mode="HTML",
            reply_markup=markup.as_markup()
        )
    await callback.answer()


@dp.callback_query(F.data.startswith("stshr_"))
async def delete_shared_confirm(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMINS:
        await callback.answer("❌ Faqat admin", show_alert=True)
        return
    await state.clear()
    row_id = int(callback.data.replace("stshr_", ""))
    db.delete_shared_sticker(row_id)
    await callback.answer("🗑 O'chirildi!")
    await _show_shared(callback, 0)


# ---------------- Admin: /stadd_shared buyrug'i (klaviaturasiz qo'shish) ----------------

@dp.message(F.text == "/stadd_shared", IsBotAdminFilter(ADMINS), StateFilter("*"))
async def admin_add_shared_cmd(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(StickerAdminStates.AddingShared)
    await message.answer(
        "➕ <b>Stiker qo'shish rejimi</b>\n\n"
        "Stikerlarni yuboring (oddiy yoki forward).\n"
        "Bitirish: /stshdone",
        parse_mode="HTML",
        reply_markup=_shared_done_markup(),
    )


# ---------------- Inline rejim ----------------
# BotFather'da /setinline yoqilgan bo'lishi kerak.

from aiogram.types import InlineQuery, InlineQueryResultCachedSticker

@dp.inline_query()
async def inline_stickers(query: InlineQuery):
    """Inline rejim: admin to'plagan umumiy kolleksiyadan qidirish.
    BotFather'da /setinline yoqilgan bo'lishi kerak."""
    q = (query.query or "").strip()
    if q:
        rows = db.search_shared_stickers(q)
    else:
        rows = db.get_shared_stickers()

    results = []
    for row_id, file_id, title in (rows or [])[:20]:
        results.append(InlineQueryResultCachedSticker(
            id=str(row_id),
            sticker_file_id=file_id,
        ))
    await query.answer(results, cache_time=10, is_personal=True)
