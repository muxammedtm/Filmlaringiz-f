import os


class Config:
    # Token va owner faqat environment variable orqali (Bothost panelidan).
    BOT_TOKEN    = os.getenv("BOT_TOKEN", "")
    OWNER_ID     = int(os.getenv("OWNER_ID", "0"))

    # Baza repo ichidagi kinobot.db dan o'qiladi (DATA_DIR'ga BOG'LIQ EMAS).
    DB_PATH      = os.getenv("DB_PATH", "kinobot.db")

    POST_CHANNEL = os.getenv("POST_CHANNEL", "")
    BOT_USERNAME = os.getenv("BOT_USERNAME", "")
