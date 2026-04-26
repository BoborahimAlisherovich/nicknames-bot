from aiogram.types import Message, CallbackQuery
from loader import dp, db
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
import json

class PremiumStates(StatesGroup):
    KutingMatn = State()

from .premium_nicknames import get_premium_nicknames, get_all_categories
from .premium_fonts import transform_text_to_font, get_premium_font_styles, get_font_by_category, get_all_font_categories
from .premium_reactions import get_random_reaction

def load_texts():
    with open("languages.json", "r", encoding="utf-8") as f:
        return json.load(f)

texts = load_texts()

# Premium nickname categories handler
@dp.message(lambda message: message.text in ["👑 Premium Nicks", "👑 Premium Nicks", "👑 Премиум ники"])
async def premium_nicknames_handler(message: Message, state: FSMContext):
    # Clear all states before starting premium nicknames
    await state.clear()
    await state.set_data({})
    
    telegram_id = message.from_user.id
    user = db.select_user_by_id(telegram_id=telegram_id)
    language = user[2] if user else "uz"
    
    # Create category keyboard
    keyboard = InlineKeyboardBuilder()
    categories = get_all_categories()
    
    # Add category buttons (3 per row)
    for i in range(0, len(categories), 3):
        row = []
        for j in range(3):
            if i + j < len(categories):
                category = categories[i + j]
                # Capitalize first letter for display
                display_name = category.capitalize()
                row.append(InlineKeyboardButton(text=f"✨ {display_name}", callback_data=f"premium_nick_{category}"))
        if row:
            keyboard.row(*row)
    
    # Add back button
    back_text = texts.get(language, {}).get("back_button", "♻️ Orqaga")
    keyboard.row(InlineKeyboardButton(text=back_text, callback_data="back_to_menu"))
    
    welcome_text = {
        "uz": "👑 Premium nik kategoriyalarini tanlang:\n\nHar bir toifada eng zamonaviy va trend niklar mavjud!",
        "us": "👑 Choose premium nickname categories:\n\nEach category has the most modern and trending nicknames!",
        "ru": "👑 Выберите категории премиум ников:\n\nВ каждой категории есть самые современные и трендовые ники!"
    }
    
    await message.answer(
        text=welcome_text.get(language, welcome_text["us"]),
        reply_markup=keyboard.as_markup()
    )

# Premium font styles handler
@dp.message(lambda message: message.text in ["🎨 Stylish Fonts", "🎨 Stylish Fonts", "🎨 Стильные шрифты"])
async def premium_fonts_handler(message: Message, state: FSMContext):
    # Clear all states before starting premium fonts
    await state.clear()
    await state.set_data({})
    
    telegram_id = message.from_user.id
    user = db.select_user_by_id(telegram_id=telegram_id)
    language = user[2] if user else "uz"
    
    # Create font category keyboard
    keyboard = InlineKeyboardBuilder()
    font_categories = get_all_font_categories()
    
    # Add font category buttons (2 per row)
    for i in range(0, len(font_categories), 2):
        row = []
        for j in range(2):
            if i + j < len(font_categories):
                category = font_categories[i + j]
                # Capitalize and replace underscores for display
                display_name = category.replace("_", " ").title()
                row.append(InlineKeyboardButton(text=f"🎨 {display_name}", callback_data=f"premium_font_{category}"))
        if row:
            keyboard.row(*row)
    
    # Add custom text option
    custom_text = {
        "uz": "✍️ O'zingiz matn kiriting",
        "us": "✍️ Enter your text",
        "ru": "✍️ Введите свой текст"
    }
    keyboard.row(InlineKeyboardButton(text=custom_text.get(language, custom_text["us"]), callback_data="custom_font_text"))
    
    # Add back button
    back_text = texts.get(language, {}).get("back_button", "♻️ Orqaga")
    keyboard.row(InlineKeyboardButton(text=back_text, callback_data="back_to_menu"))
    
    welcome_text = {
        "uz": "🎨 Premium shrift uslublarini tanlang:\n\nMatnni chiroyli Unicode shriftlariga aylantiring!",
        "us": "🎨 Choose premium font styles:\n\nTransform text into beautiful Unicode fonts!",
        "ru": "🎨 Выберите стили премиум шрифтов:\n\nПреобразуйте текст в красивые Unicode шрифты!"
    }
    
    await message.answer(
        text=welcome_text.get(language, welcome_text["us"]),
        reply_markup=keyboard.as_markup()
    )

# Handle premium nickname category selection
@dp.callback_query(lambda c: c.data.startswith("premium_nick_"))
async def handle_premium_nick_category(callback: CallbackQuery, state: FSMContext):
    # Clear any existing states
    await state.clear()
    await state.set_data({})
    
    category = callback.data.split("_", 2)[2]
    telegram_id = callback.from_user.id
    user = db.select_user_by_id(telegram_id=telegram_id)
    language = user[2] if user else "uz"
    
    # Get premium nicknames from selected category
    nicknames = get_premium_nicknames(category=category, count=15)
    
    # Format response
    category_name = category.replace("_", " ").title()
    header_text = {
        "uz": f"✨ {category_name} kategoriyasidagi premium niklar:\n\n",
        "us": f"✨ Premium nicknames from {category_name} category:\n\n",
        "ru": f"✨ Премиум ники из категории {category_name}:\n\n"
    }
    
    text = header_text.get(language, header_text["us"])
    for idx, nick in enumerate(nicknames, 1):
        text += f"{idx}. <code>{nick}</code>\n"
    
    # Create keyboard for more options
    keyboard = InlineKeyboardBuilder()
    
    # Add "More" button
    more_text = {
        "uz": "🔄 Boshqa niklar",
        "us": "🔄 More nicknames", 
        "ru": "🔄 Больше ников"
    }
    keyboard.row(InlineKeyboardButton(text=more_text.get(language, more_text["us"]), callback_data=f"premium_nick_{category}"))
    
    # Add back button
    back_text = texts.get(language, {}).get("back_button", "♻️ Orqaga")
    keyboard.row(InlineKeyboardButton(text=back_text, callback_data="premium_categories"))
    
    await callback.message.edit_text(
        text=text,
        reply_markup=keyboard.as_markup()
    )
    await callback.answer()

# Handle premium font category selection
@dp.callback_query(lambda c: c.data.startswith("premium_font_"))
async def handle_premium_font_category(callback: CallbackQuery, state: FSMContext):
    # Clear any existing states first
    await state.clear()
    
    category = callback.data.split("_", 2)[2]
    telegram_id = callback.from_user.id
    user = db.select_user_by_id(telegram_id=telegram_id)
    language = user[2] if user else "uz"
    
    # Store category in state for later use and set state
    await state.update_data(font_category=category)
    await state.set_state(PremiumStates.KutingMatn)
    
    # Ask for text input
    prompt_text = {
        "uz": f"🎨 {category.replace('_', ' ').title()} shrifti uchun matn kiriting:\n\nMatnni yuboring, men uni aylantirib beraman!",
        "us": f"🎨 Enter text for {category.replace('_', ' ').title()} font:\n\nSend your text and I'll transform it!",
        "ru": f"🎨 Введите текст для шрифта {category.replace('_', ' ').title()}:\n\nОтправьте ваш текст и я преобразую его!"
    }
    
    await callback.message.edit_text(
        text=prompt_text.get(language, prompt_text["us"]),
        reply_markup=None
    )
    await callback.answer()

# Handle custom font text input
@dp.callback_query(lambda c: c.data == "custom_font_text")
async def handle_custom_font_text(callback: CallbackQuery, state: FSMContext):
    # Clear any existing states
    await state.clear()
    
    telegram_id = callback.from_user.id
    user = db.select_user_by_id(telegram_id=telegram_id)
    language = user[2] if user else "uz"
    
    # Set pure text state for any font processing
    await state.set_state(PremiumStates.KutingMatn)
    await state.update_data(font_category=None)
    
    prompt_text = {
        "uz": "✍️ Iltimos, shriftga aylantirmoqchi bo'lgan matningizni kiriting:",
        "us": "✍️ Please enter the text you want to convert to font:",
        "ru": "✍️ Пожалуйста, введите текст, который вы хотите преобразовать в шрифт:"
    }
    
    await callback.message.edit_text(
        text=prompt_text.get(language, prompt_text["us"]),
        reply_markup=None
    )
    await callback.answer()

# Handle text input for font transformation
@dp.message(PremiumStates.KutingMatn)
async def handle_font_text_input(message: Message, state: FSMContext):
    user_data = await state.get_data()
    
    # Check if we have a font category in state
    if "font_category" in user_data:
        category = user_data["font_category"]
        telegram_id = message.from_user.id
        user = db.select_user_by_id(telegram_id=telegram_id)
        language = user[2] if user else "uz"
        
        # Transform text using selected font category
        font_styles = get_font_by_category(message.text, category, count=5)
        
        if font_styles:
            category_name = category.replace("_", " ").title()
            header_text = {
                "uz": f"🎨 {category_name} shriftidagi natijalar:\n\n",
                "us": f"🎨 Results in {category_name} font:\n\n",
                "ru": f"🎨 Результаты в шрифте {category_name}:\n\n"
            }
            
            text = header_text.get(language, header_text["us"])
            for idx, style in enumerate(font_styles, 1):
                text += f"{idx}. <code>{style}</code>\n\n"
        else:
            error_text = {
                "uz": "❌ Xatolik yuz berdi. Iltimos, qayta urinib ko'ring.",
                "us": "❌ An error occurred. Please try again.",
                "ru": "❌ Произошла ошибка. Пожалуйста, попробуйте еще раз."
            }
            text = error_text.get(language, error_text["us"])
        
        # Create keyboard
        keyboard = InlineKeyboardBuilder()
        
        # Add "Transform Another" button
        another_text = {
            "uz": "🔄 Boshqa matn",
            "us": "🔄 Transform Another",
            "ru": "🔄 Преобразовать другой"
        }
        keyboard.row(InlineKeyboardButton(text=another_text.get(language, another_text["us"]), callback_data=f"premium_font_{category}"))
        
        # Add "All Styles" button
        all_styles_text = {
            "uz": "🎨 Barcha uslublar",
            "us": "🎨 All Styles",
            "ru": "🎨 Все стили"
        }
        keyboard.row(InlineKeyboardButton(text=all_styles_text.get(language, all_styles_text["us"]), callback_data="custom_font_text"))
        
        # Add back button
        back_text = texts.get(language, {}).get("back_button", "♻️ Orqaga")
        keyboard.row(InlineKeyboardButton(text=back_text, callback_data="premium_fonts_menu"))
        
        await message.answer(
            text=text,
            reply_markup=keyboard.as_markup()
        )
        
        # Clear state
        await state.clear()
    else:
        # If no font category in state, check if user wants all font styles
        if len(message.text) < 50:  # Reasonable length check
            telegram_id = message.from_user.id
            user = db.select_user_by_id(telegram_id=telegram_id)
            language = user[2] if user else "uz"
            
            # Get all font styles for the text
            all_styles = get_premium_font_styles(message.text, count=10)
            
            header_text = {
                "uz": "🎨 Barcha premium shrift uslublari:\n\n",
                "us": "🎨 All premium font styles:\n\n",
                "ru": "🎨 Все стили премиум шрифтов:\n\n"
            }
            
            text = header_text.get(language, header_text["us"])
            for idx, style in enumerate(all_styles, 1):
                text += f"{idx}. <code>{style}</code>\n\n"
            
            # Create keyboard
            keyboard = InlineKeyboardBuilder()
            
            # Add "Transform Another" button
            another_text = {
                "uz": "🔄 Boshqa matn",
                "us": "🔄 Transform Another",
                "ru": "🔄 Преобразовать другой"
            }
            keyboard.row(InlineKeyboardButton(text=another_text.get(language, another_text["us"]), callback_data="custom_font_text"))
            
            # Add back button
            back_text = texts.get(language, {}).get("back_button", "♻️ Orqaga")
            keyboard.row(InlineKeyboardButton(text=back_text, callback_data="premium_fonts_menu"))
            
            await message.answer(
                text=text,
                reply_markup=keyboard.as_markup()
            )

# Handle back to premium categories
@dp.callback_query(lambda c: c.data == "premium_categories")
async def back_to_premium_categories(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    
    telegram_id = callback.from_user.id
    user = db.select_user_by_id(telegram_id=telegram_id)
    language = user[2] if user else "uz"
    
    # Recreate categories keyboard
    keyboard = InlineKeyboardBuilder()
    categories = get_all_categories()
    
    for i in range(0, len(categories), 3):
        row = []
        for j in range(3):
            if i + j < len(categories):
                category = categories[i + j]
                display_name = category.capitalize()
                row.append(InlineKeyboardButton(text=f"✨ {display_name}", callback_data=f"premium_nick_{category}"))
        if row:
            keyboard.row(*row)
    
    back_text = texts.get(language, {}).get("back_button", "♻️ Orqaga")
    keyboard.row(InlineKeyboardButton(text=back_text, callback_data="back_to_menu"))
    
    welcome_text = {
        "uz": "👑 Premium nik kategoriyalarini tanlang:\n\nHar bir toifada eng zamonaviy va trend niklar mavjud!",
        "us": "👑 Choose premium nickname categories:\n\nEach category has the most modern and trending nicknames!",
        "ru": "👑 Выберите категории премиум ников:\n\nВ каждой категории есть самые современные и трендовые ники!"
    }
    
    await callback.message.edit_text(
        text=welcome_text.get(language, welcome_text["us"]),
        reply_markup=keyboard.as_markup()
    )
    await callback.answer()

# Handle back to premium fonts menu
@dp.callback_query(lambda c: c.data == "premium_fonts_menu")
async def back_to_premium_fonts_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    
    telegram_id = callback.from_user.id
    user = db.select_user_by_id(telegram_id=telegram_id)
    language = user[2] if user else "uz"
    
    # Recreate font categories keyboard
    keyboard = InlineKeyboardBuilder()
    font_categories = get_all_font_categories()
    
    for i in range(0, len(font_categories), 2):
        row = []
        for j in range(2):
            if i + j < len(font_categories):
                category = font_categories[i + j]
                display_name = category.replace("_", " ").title()
                row.append(InlineKeyboardButton(text=f"🎨 {display_name}", callback_data=f"premium_font_{category}"))
        if row:
            keyboard.row(*row)
    
    custom_text = {
        "uz": "✍️ O'zingiz matn kiriting",
        "us": "✍️ Enter your text",
        "ru": "✍️ Введите свой текст"
    }
    keyboard.row(InlineKeyboardButton(text=custom_text.get(language, custom_text["us"]), callback_data="custom_font_text"))
    
    back_text = texts.get(language, {}).get("back_button", "♻️ Orqaga")
    keyboard.row(InlineKeyboardButton(text=back_text, callback_data="back_to_menu"))
    
    welcome_text = {
        "uz": "🎨 Premium shrift uslublarini tanlang:\n\nMatnni chiroyli Unicode shriftlariga aylantiring!",
        "us": "🎨 Choose premium font styles:\n\nTransform text into beautiful Unicode fonts!",
        "ru": "🎨 Выберите стили премиум шрифтов:\n\nПреобразуйте текст в красивые Unicode шрифты!"
    }
    
    await callback.message.edit_text(
        text=welcome_text.get(language, welcome_text["us"]),
        reply_markup=keyboard.as_markup()
    )
    await callback.answer()
