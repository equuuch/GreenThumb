import os
import sys
from dotenv import load_dotenv

# Загрузка переменных из .env (актуально для разработки на ПК)
load_dotenv()

class Config:
    # --- СБЕР СЕКРЕТИКИ ---
    GIGA_CREDS = os.getenv("GIGACHAT_CREDENTIALS")
    GIGA_CLIENT_ID = os.getenv("GIGACHAT_CLIENT_ID")
    GIGA_SCOPE = os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS")
    GIGA_MODEL_LITE = os.getenv("GIGACHAT_MODEL_LITE", "GigaChat")
    GIGA_MODEL_MAX = os.getenv("GIGACHAT_MODEL_MAX", "GigaChat-Max")

    # --- БД ЛОГИКА ДЛЯ APK ---
    # Проверяем, запущены ли мы на Android
    IS_ANDROID = os.getenv("FLET_PLATFORM") == "android" or hasattr(sys, "getandroidapilevel")

    if IS_ANDROID:
        # На Android используем внутреннюю директорию приложения для записи
        # Переменная окружения FILESDIR устанавливается Flet автоматически
        base_path = os.getenv("FILESDIR", os.getcwd())
        DB_URL = f"sqlite:///{os.path.join(base_path, 'greenthumb.db')}"
    else:
        # На ПК берем из .env или используем дефолт
        DB_URL = os.getenv("DATABASE_URL", "sqlite:///greenthumb.db")
    
    DB_ECHO = os.getenv("DB_ECHO", "False").lower() == "true"
    SECRET_KEY = os.getenv("SECRET_KEY", "gt_secret_fallback_777")

    # --- МЕДИА И ПУТИ ---
    # Для ассетов на Android используем относительные пути, чтобы Flet их нашел
    UPLOAD_DIR = "assets"
    REPORTS_DIR = os.path.join("assets", "reports")
    FONTS_DIR = os.path.join("assets", "fonts")

    IMAGE_MAX_SIZE = 1024
    IMAGE_QUALITY = 75