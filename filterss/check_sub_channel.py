import time
import logging

from aiogram import filters, Bot
from aiogram.types import Message

logger = logging.getLogger(__name__)


class IsCheckSubChannels(filters.Filter):
    """Kanal azoligini tekshiradi.

    PERFORMANCE: natijalar 10 daqiqa keshlanadi. Ilgari foydalanuvchining HAR
    BIR xabari uchun har bir kanalga get_chat_member so'rovi yuborilardi —
    5 kanal x 1000 foydalanuvchi = 5000 ta API so'rov/daqiqada bo'lishi mumkin
    edi va Telegram FloodWait bilan botni bloklar edi. Endi bir foydalanuvchi
    uchun 10 daqiqada faqat BIR marta tekshiriladi.
    """

    # user_id -> tekshirilgan vaqt (barcha filter nusxalari uchun umumiy)
    _verified: dict[int, float] = {}
    CHECK_INTERVAL = 600  # 10 daqiqa

    async def __call__(self, message: Message, bot: Bot):
        from loader import db, ADMINS

        user_id = message.from_user.id

        if user_id in ADMINS:
            return False

        channels = db.get_channels()
        if not channels:
            return False

        # Yaqinda tekshirilgan bo'lsa - qayta tekshirmaymiz
        last_check = self._verified.get(user_id)
        if last_check and time.time() - last_check < self.CHECK_INTERVAL:
            return False

        for channel in channels:
            try:
                result = await bot.get_chat_member(int(channel), user_id)
                if result.status not in ("member", "administrator", "creator"):
                    return True  # hali azo emas
            except Exception as e:
                logger.warning(f"Kanal {channel} azolik tekshiruvi xatosi: {e}")
                return True  # xato bo'lsa ham xavfsizlik uchun tekshirish talab qilamiz

        # Barcha kanallarga azo ekan - keshlaymiz
        self._verified[user_id] = time.time()
        return False

    @classmethod
    def mark_verified(cls, user_id: int):
        """Foydalanuvchi azoligini tasdiqlagandan keyin chaqiriladi."""
        cls._verified[user_id] = time.time()
