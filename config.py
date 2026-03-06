import os
from dotenv import load_dotenv

# загрузка переменных из .env
load_dotenv()

class Config:
    # сбер секретики
    # авторизационные данные для oauth (base64)
    GIGA_CREDS = os.getenv("GIGACHAT_CREDENTIALS")
    
    # область доступа 
    GIGA_SCOPE = os.getenv("GIGACHAT_SCOPE", "GIGACHAT_API_PERS")

    GIGA_MODEL_LITE = os.getenv("GIGACHAT_MODEL_LITE", "GigaChat")

    GIGA_MODEL_MAX = os.getenv("GIGACHAT_MODEL_MAX", "GigaChat-Max")

    # бд секретики
    # путь к файлу базы данных
    DB_URL = os.getenv("DATABASE_URL", "sqlite:///greenthumb.db")
    
    # логирование запросов к базе
    DB_ECHO = os.getenv("DB_ECHO", "False").lower() == "true"
    
    # ключ для шифрования данных
    SECRET_KEY = os.getenv("SECRET_KEY", "your_very_secret_key_here")

    # директория для локального сохранения изображений
    UPLOAD_DIR = os.path.join("assets", "uploads")