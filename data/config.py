from environs import Env

# environs kutubxonasidan foydalanish
env = Env()
env.read_env()

# .env fayl ichidan quyidagilarni o'qiymiz
BOT_TOKEN = env.str("BOT_TOKEN")  # Bot Token
ADMINS = list(map(int,env.list("ADMINS")))  # adminlar ro'yxati
CHANNELS = list(map(int,env.list("CHANNELS")))

# AI nick generator uchun (ixtiyoriy - bo'lmasa lokal generator ishlaydi)
GEMINI_API_KEY = env.str("GEMINI_API_KEY", default="")
# Bir nechta model vergul bilan: birinchisi ishlamasa keyingisi sinaladi
GEMINI_MODELS = [m.strip() for m in env.list("GEMINI_MODEL", default=["gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-flash-lite-latest"]) if m.strip()]
GEMINI_MODEL = GEMINI_MODELS[0]

# Karta orqali donat: CARDS=8600 1234 5678 9012,9860 1234 5678 9012
CARDS = [c.strip() for c in env.list("CARDS", default=[]) if c.strip()]
CARD_OWNER = env.str("CARD_OWNER", default="")
