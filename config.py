import os
from dotenv import load_dotenv

# загрузка переменных из .env
load_dotenv()

class Config:
    # сбер секретики
    # авторизационные данные для oauth (base64)
    GIGA_CREDS = os.getenv("GIGACHAT_CREDENTIALS")
    
    # идентификатор клиента для заголовков x-client-id
    GIGA_CLIENT_ID = os.getenv("GIGACHAT_CLIENT_ID")
    
    # область доступа (физлица по умолчанию)
    GIGA_SCOPE = os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS")

    # базовая модель для текстовых ответов
    GIGA_MODEL_LITE = os.getenv("GIGACHAT_MODEL_LITE", "GigaChat")

    # мощная модель для работы с фото
    GIGA_MODEL_MAX = os.getenv("GIGACHAT_MODEL_MAX", "GigaChat-Max")

    # бд секретики
    # полный путь к базе данных sqlite
    DB_URL = os.getenv("DATABASE_URL", "sqlite:///greenthumb.db")
    
    # включение вывода sql запросов в консоль
    DB_ECHO = os.getenv("DB_ECHO", "False").lower() == "true"
    
    # секретный ключ для защиты данных
    SECRET_KEY = os.getenv("SECRET_KEY", "gt_secret_fallback_777")

    # медиа и оптимизация
    # корневая папка для сохранения всех загрузок
    UPLOAD_DIR = os.path.join("assets", "uploads")

    # максимальный размер стороны фото в пикселях для pillow
    IMAGE_MAX_SIZE = 1024

    # качество сжатия для экономии токенов и места
    IMAGE_QUALITY = 75

    # директории для отчетов
    REPORTS_DIR = os.path.join("assets", "reports")
    
    # путь к шрифтам для поддержки русского языка в pdf
    FONTS_DIR = os.path.join("assets", "fonts")