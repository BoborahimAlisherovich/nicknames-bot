import data.colors  # noqa: F401
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import json

language = InlineKeyboardMarkup(
    inline_keyboard=[
        [
        InlineKeyboardButton(text= "O'zbek 🇺🇿", callback_data="uz"),
        InlineKeyboardButton(text= "English 🇺🇸", callback_data="us"),
        InlineKeyboardButton(text= "Русский 🇷🇺", callback_data="ru")
        ]
    ]
)

# Markaziy matnlar moduli orqali yuklanadi
from data.texts import get_texts

texts = get_texts()

def create_menu_buttons(language):
    button_texts = texts[language]["menu"]

    menu_buttons = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=button_texts["menu_button_11"]), KeyboardButton(text=button_texts["menu_button_1"])],
            [KeyboardButton(text=button_texts["menu_button_2"]), KeyboardButton(text=button_texts["menu_button_8"])],
            [KeyboardButton(text=button_texts["menu_button_9"]), KeyboardButton(text=button_texts["menu_button_10"])],
            [KeyboardButton(text=button_texts["menu_button_4"]), KeyboardButton(text=button_texts["menu_button_5"])],
            [KeyboardButton(text="✨ AI Studio", style="primary"), KeyboardButton(text="🎲 AI O'yinlar", style="success")],
            [KeyboardButton(text="💝 Donat", style="danger"), KeyboardButton(text=button_texts["menu_button_3"])]
        ],
        resize_keyboard=True,
    )
    return menu_buttons

menu_button_uz = create_menu_buttons("uz")
menu_button_us = create_menu_buttons("us")
menu_button_ru = create_menu_buttons("ru")


admin_button = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Foydalanuvchilar soni"),
            KeyboardButton(text="Reklama yuborish"),
        ],
        [
            KeyboardButton(text="Kanal qoshish"),
            KeyboardButton(text="Kanallar royhati"),
        ],
        [
            KeyboardButton(text="🔑 Gemini API", style="primary"),
            KeyboardButton(text="💳 Kartalar", style="success"),
        ],
        [KeyboardButton(text="🔥 Stikerlarni to'ldirish")],
    ],
   resize_keyboard=True,
   input_field_placeholder="Menudan birini tanlang"
)

def create_back_button(language):
    back_text = texts[language]["back_button"]
    back_button = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=back_text),
            ]
        ],
        resize_keyboard=True
    )
    return back_button
