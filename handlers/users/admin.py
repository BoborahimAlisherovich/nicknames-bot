from aiogram.dispatcher.event.bases import SkipHandler
from filterss.check_sub_channel import IsCheckSubChannels
from loader import dp, bot, db, ADMINS, TOKEN
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import Message, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command, StateFilter
from filterss.admin import IsBotAdminFilter
from states.reklama import Adverts
from states.bulimlar import ChannelStates
from aiogram.fsm.context import FSMContext
from keyboard_buttons import admin_keyboard
from keyboard_buttons.admin_keyboard import create_menu_buttons
from aiogram.exceptions import ClientDecodeError, TelegramRetryAfter, TelegramForbiddenError
import asyncio
import json
import html
import aiohttp
from types import SimpleNamespace
from aiogram import F
import logging

logger = logging.getLogger(__name__)

from data.texts import get_texts


async def get_chat_safe(chat_id):
    try:
        return await bot.get_chat(chat_id)
    except ClientDecodeError:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"https://api.telegram.org/bot{TOKEN}/getChat",
                data={"chat_id": chat_id},
            ) as response:
                data = await response.json()

        if not data.get("ok"):
            description = data.get("description", "getChat failed")
            raise RuntimeError(description)

        result = data["result"]
        title = result.get("title") or result.get("username") or str(result.get("id", chat_id))
        return SimpleNamespace(id=result.get("id", chat_id), title=title)


@dp.message(IsCheckSubChannels(), lambda message: not (message.text and message.text.startswith("/start")))
async def kanalga_obuna(message: Message, state: FSMContext):
    # Eslatma: ilgari foydalanuvchi biror holatda (anonim xabar, AI so'rov...) bo'lsa,
    # bu yerda jimgina return qilinardi va xabar YO'QOLARDI. Endi obuna so'raladi,
    # holat saqlanadi - obunadan keyin foydalanuvchi davom ettira oladi.
    channels = db.get_channels()
    if not channels:
        raise SkipHandler()

    inline_channel = InlineKeyboardBuilder()
    valid_channels = []

    for channel in channels:
        try:
            chat = await get_chat_safe(int(channel))
            inline_channel.add(InlineKeyboardButton(
                text=chat.title,
                url=(await bot.create_chat_invite_link(int(channel))).invite_link
            ))
            valid_channels.append(channel)
        except Exception as e:
            logger.warning(f"Kanal {channel} haqida ma'lumot olishda xato: {e}")

    if not valid_channels:
        raise SkipHandler()  # kanal ma'lumoti olinmadi - foydalanuvchini bloklamaymiz

    inline_channel.adjust(1, repeat=True)
    inline_channel.row(InlineKeyboardButton(
        text="Tekshirish ✅",
        callback_data="check_subscription"
    ))
    await message.answer(
        "📢 Botdan foydalanish uchun quyidagi kanal(lar)ga a'zo bo'ling, so'ng «Tekshirish ✅» ni bosing:",
        reply_markup=inline_channel.as_markup()
    )


@dp.callback_query(lambda c: c.data == "check_subscription")
async def check_subscription_callback(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    channels = db.get_channels()

    for channel in channels:
        try:
            result = await bot.get_chat_member(int(channel), user_id)
            if result.status not in ("member", "administrator", "creator"):
                await callback.answer("Hali kanalga azo emassiz!", show_alert=True)
                return
        except:
            await callback.answer("Xatolik yuz berdi!", show_alert=True)
            return

    await callback.answer("Barcha kanallarga azo siz! ✅")
    await callback.message.delete()

    # Azo bo'ldi - keshga yozamiz, keyingi 10 daqiqa qayta tekshirilmaydi
    from filterss.check_sub_channel import IsCheckSubChannels
    IsCheckSubChannels.mark_verified(user_id)

    # Anonim xabar yozayotgan edi - menyu emas, davom ettirishni aytamiz
    from handlers.users.anonymous_system import AnonimStates
    if await state.get_state() == AnonimStates.AnonimXabarYuborish.state:
        await callback.message.answer("✅ Rahmat! Endi anonim xabaringizni yozib yuboring:")
        return

    user = db.select_user_by_id(telegram_id=user_id)
    language = user[2] if user else "uz"
    texts = get_texts()
    welcome_text = texts.get(language, {}).get("welcome_message", "Welcome!")
    await callback.message.answer(
        welcome_text.format(full_name=callback.from_user.full_name) if "{full_name}" in welcome_text else welcome_text,
        reply_markup=create_menu_buttons(language)
    )


@dp.message(Command("admin"), IsBotAdminFilter(ADMINS), StateFilter("*"))
async def is_admin(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(text="Admin menu", reply_markup=admin_keyboard.admin_button)


@dp.message(F.text == "Foydalanuvchilar soni", IsBotAdminFilter(ADMINS), StateFilter("*"))
async def users_count(message: Message, state: FSMContext):
    await state.clear()
    counts = db.count_users()
    await message.answer(text=f"Botimizda {counts[0]} ta foydalanuvchi bor")


@dp.message(F.text == "Reklama yuborish", IsBotAdminFilter(ADMINS), StateFilter("*"))
async def advert_dp(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(Adverts.adverts)
    await message.answer(text="Reklama yuborishingiz mumkin!")


@dp.message(Adverts.adverts)
async def send_advert(message: Message, state: FSMContext):
    message_id = message.message_id
    from_chat_id = message.from_user.id
    users = db.all_users_id()
    count = 0
    blocked = 0
    failed = 0
    for user in users:
        try:
            await bot.copy_message(chat_id=user[0], from_chat_id=from_chat_id, message_id=message_id)
            count += 1
        except TelegramRetryAfter as e:
            # Telegram flood limit - qancha kutish kerakligini o'zi aytadi
            logger.warning(f"Telegram FloodWait: {e.retry_after}s kutamiz...")
            await asyncio.sleep(e.retry_after + 1)
            try:
                await bot.copy_message(chat_id=user[0], from_chat_id=from_chat_id, message_id=message_id)
                count += 1
            except Exception as err:
                logger.warning(f"Reklama qayta yuborilmadi (user {user[0]}): {err}")
                failed += 1
        except TelegramForbiddenError:
            # Foydalanuvchi botni bloklagan
            blocked += 1
        except Exception as e:
            logger.warning(f"Reklama yuborilmadi (user {user[0]}): {e}")
            failed += 1
        # Bloklovchi kutish emas! Boshqa foydalanuvchilar xabarlari shu paytda ham ishlaydi
        await asyncio.sleep(0.05)
    await message.answer(
        f"✅ Reklama {count} ta foydalanuvchiga yuborildi\n"
        f"🚫 Bloklagan: {blocked} ta\n"
        f"⚠️ Yuborilmadi: {failed} ta"
    )
    await state.clear()


@dp.message(F.text == "Kanal qoshish", IsBotAdminFilter(ADMINS), StateFilter("*"))
async def add_channel_start(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(ChannelStates.waiting_for_channel)
    await message.answer(
        "Kanal ID sini yoki kanal username/linkini yuboring:\n\n"
        "Masalan:\n"
        "-1001234567890 (kanal ID)\n"
        "@kanal_username (username)\n"
        "https://t.me/kanal_username (link)"
    )


@dp.message(ChannelStates.waiting_for_channel, IsBotAdminFilter(ADMINS))
async def add_channel_handle(message: Message, state: FSMContext):
    text = message.text.strip()

    kanal_id = None

    if text.startswith("https://t.me/+"):
        invite_hash = text.split("+")[1]
        try:
            chat = await get_chat_safe(f"invite/{invite_hash}")
            kanal_id = str(chat.id)
        except Exception as e:
            logger.warning(f"Private kanal linkini tekshirish xatosi ({text}): {e}")
    elif text.startswith("https://t.me/"):
        username = text.split("https://t.me/")[1].split("/")[0]
        try:
            chat = await get_chat_safe(f"@{username}")
            kanal_id = str(chat.id)
        except Exception as e:
            logger.warning(f"Kanal linkini tekshirish xatosi ({text}): {e}")
    elif text.startswith("@"):
        try:
            chat = await get_chat_safe(text)
            kanal_id = str(chat.id)
        except Exception as e:
            logger.warning(f"Kanal username'ini tekshirish xatosi ({text}): {e}")
    elif text.lstrip("-").isdigit():
        kanal_id = text

    if not kanal_id:
        await message.answer("Notogri kanal ID yoki link. Qaytadan urinib koring.")
        return

    try:
        chat = await get_chat_safe(int(kanal_id))
        bot_member = await bot.get_chat_member(int(kanal_id), (await bot.me()).id)
        if bot_member.status not in ("administrator", "creator"):
            await message.answer(f"Bot {chat.title} kanalida admin emas. Avval botni kanalga admin qiling.")
            return
    except Exception as e:
        err_text = str(e)
        if "chat not found" in err_text:
            await message.answer(
                "Kanal topilmadi. Sabablari:\n"
                "1. Bot kanalga admin qilinmagan – avval botni kanalga admin qiling\n"
                "2. Kanal username yoki link notogri – @username yoki https://t.me/link shaklida yuboring\n"
                "3. Kanal ID notogri – ID ni tekshiring"
            )
        else:
            await message.answer(f"Xatolik: {html.escape(err_text)}")
        return
    finally:
        await state.clear()

    db.add_channel(kanal_id)
    await message.answer(f"Kanal qoshildi: {chat.title}")


@dp.message(F.text == "Kanallar royhati", IsBotAdminFilter(ADMINS), StateFilter("*"))
async def list_channels(message: Message, state: FSMContext):
    await state.clear()
    channels = db.get_channels()
    if not channels:
        await message.answer("Hozircha kanal qoshilmagan.")
        return

    text = "Botdagi kanallar:\n\n"
    keyboard = InlineKeyboardBuilder()
    for idx, ch in enumerate(channels, 1):
        try:
            chat = await get_chat_safe(int(ch))
            text += f"{idx}. {chat.title}\n"
        except Exception as e:
            logger.warning(f"Kanal {ch} topilmadi: {e}")
            text += f"{idx}. {ch} (topilmadi)\n"
        keyboard.add(InlineKeyboardButton(
            text=f"Ochirish {idx}",
            callback_data=f"del_channel_{ch}"
        ))
    keyboard.adjust(1)
    await message.answer(text, reply_markup=keyboard.as_markup())


@dp.callback_query(lambda c: c.data.startswith("del_channel_"))
async def delete_channel_callback(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        await callback.answer("Ruxsat yoq")
        return
    channel_id = callback.data.split("del_channel_")[1]
    db.delete_channel(channel_id)
    await callback.answer("Kanal ochirildi")
    await callback.message.delete()
