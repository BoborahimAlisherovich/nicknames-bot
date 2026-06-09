from aiogram import filters, Bot
from aiogram.types import Message


class IsCheckSubChannels(filters.Filter):

    async def __call__(self, message: Message, bot: Bot):
        from loader import db, ADMINS

        if message.from_user.id in ADMINS:
            return False

        channels = db.get_channels()
        if not channels:
            return False

        for channel in channels:
            try:
                result = await bot.get_chat_member(int(channel), message.from_user.id)
                if result.status not in ("member", "administrator", "creator"):
                    return True
            except:
                return True
        return False
