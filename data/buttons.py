"""Stilizatsiyalangan tugmalar yordamchisi.

Real hayotiy izoh: Telegram'da oddiy inline tugmalarni "bo'yash" mumkin emas -
rang faqat maxsus (premium) custom emoji ikonkalari orqali beriladi.
Bu modul:
  1) Har bir tugmaga vazifasiga qarab RANG va IKONKA belgilaydi;
  2) Siz o'z premium custom emoji set'ingizni yaratib, ID'larini
     CUSTOM_EMOJI_IDS ga yozsangiz - tugmalar rasmdagidek chiqadi;
  3) ID'lar bo'sh bo'lsa - fallback sifatida unicode emoji ishlatiladi
     (hech qanday xato bo'lmaydi).

Qanday to'ldiriladi:
  1. Telegram Premium akkaunt bilan @Stickers botida own set yaratishingiz kerak
     (masalan rangli kvadrat/yulduz emoji stikerlari).
  2. Set'dagi har bir stikerning custom_emoji_id sini olish uchun:
     bot API'da getCustomEmojiStickers yoki @RawDataBot'dan stikerni forward qilib
     "custom_emoji_id" ni ko'rish mumkin.
  3. Quyidagi CUSTOM_EMOJI_IDS lug'atiga kalit bo'yicha yozing.
"""
from aiogram.types import InlineKeyboardButton, MessageEntity

# ------------------------------------------------------------------
# Vazifa bo'yicha rang/ikonka xaritasi (fallback unicode emojilar)
# ------------------------------------------------------------------
STYLE_ICONS = {
    "main":     ("🟦", "Asosiy"),          # asosiy menyular
    "stickers": ("⭐", "Stikerlar"),        # umumiy stikerlar kolleksiyasi
    "packs":    ("🟩", "Paketlar"),         # bot paketlari
    "trend":    ("🟪", "Trend"),            # telegram trend paketlari
    "add":      ("🟩", "Qo'shish"),         # narsa qo'shish
    "delete":   ("🟥", "O'chirish"),        # narsa o'chirish
    "back":     ("🟨", "Orqaga"),           # orqaga qaytish
    "memorable":("🟦", "Eslab qoladigan"),  # parol: eslab qoladigan
    "speakable":("🟩", "Talaffuz"),         # parol: talaffuz qilinadigan
    "strong":   ("🟥", "Super kuchli"),     # parol: super kuchli
    "random":   ("🟪", "Tasodifiy"),        # parol/ tasodifiy
}

# ------------------------------------------------------------------
# Custom emoji ID'lari (bo'sh qoldirilsa unicode fallback ishlaydi).
# Kalitlar STYLE_ICONS bilan bir xil. Qiymat: "custom_emoji_id" string.
# ------------------------------------------------------------------
CUSTOM_EMOJI_IDS: dict[str, str] = {
    # "main":     "5468523682143113610",
    # "stickers": "...",
    # "packs":    "...",
    # "trend":    "...",
    # "add":      "...",
    # "delete":   "...",
    # "back":     "...",
    # "memorable":"...",
    # "speakable":"...",
    # "strong":   "...",
    # "random":   "...",
}


def _utf16_len(icon: str) -> int:
    """Telegram entity length UTF-16 code unitsda o'lchanadi.
    BMP tashqarisidagi emoji (masalan 🟦 U+1F7E6) = 2 birlik."""
    return len(icon.encode("utf-16-le")) // 2


def icon_button(
    text: str,
    callback_data: str | None = None,
    url: str | None = None,
    style_key: str | None = None,
    icon: str | None = None,
):
    """Stilizatsiyalangan inline tugma.

    - text: to'liq matn (ikonka yoki rang + label), masalan "⭐ Stikerlar"
    - style_key: STYLE_ICONS/CUSTOM_EMOJI_IDS kaliti (ikonka text boshida bo'lsa)
    - icon: aniq ikonka (text boshidagi) - style_key o'rniga ishlatiladi
    Custom emoji ID mavjud bo'lsa text_entities qo'shiladi, aks holda
    oddiy tugma (hech qanday xato yo'q).
    """
    emoji_id = None
    entity_icon = None
    if icon:
        entity_icon = icon
        emoji_id = CUSTOM_EMOJI_IDS.get(icon)
    elif style_key:
        entity_icon = (STYLE_ICONS.get(style_key) or ("", ""))[0]
        emoji_id = CUSTOM_EMOJI_IDS.get(style_key)

    kwargs = {}
    if emoji_id and entity_icon and text.startswith(entity_icon):
        kwargs["text_entities"] = [MessageEntity(
            type="custom_emoji",
            offset=0,
            length=_utf16_len(entity_icon),
            custom_emoji_id=emoji_id,
        )]

    if url:
        return InlineKeyboardButton(text=text, url=url, **kwargs)
    return InlineKeyboardButton(text=text, callback_data=callback_data, **kwargs)


def styled_text(style_key: str, label: str) -> str:
    """Rang ikonkasi + label qaytaradi (tugma matni sifatida)."""
    color, _ = STYLE_ICONS.get(style_key, ("⭐", ""))
    return f"{color} {label}"
