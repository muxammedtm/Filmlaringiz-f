import os


class Config:
    # ⚠️ TOKEN HECH QACHON KODGA YOZILMAYDI.
    # Faqat environment variable orqali beriladi (BOT_TOKEN).
    BOT_TOKEN    = os.getenv("BOT_TOKEN", "")
    OWNER_ID     = int(os.getenv("OWNER_ID", "0"))

    # Ma'lumotlar bazasi yo'li. Docker'da volume sifatida /app/data ulanadi —
    # shuning uchun DATA_DIR bo'lsa, baza o'sha yerga yoziladi (restartda saqlanadi).
    _data_dir    = os.getenv("DATA_DIR", "")
    _db_name     = os.getenv("DB_PATH", "kinobot.db")
    DB_PATH      = os.path.join(_data_dir, _db_name) if _data_dir else _db_name

    # Quyidagilar majburiy emas — admin paneldan ham o'rnatish mumkin.
    POST_CHANNEL = os.getenv("POST_CHANNEL", "")
    BOT_USERNAME = os.getenv("BOT_USERNAME", "")
