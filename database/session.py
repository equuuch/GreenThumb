import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base
from config import Config

# 1. Определяем финальный URL базы данных
# Если в Config уже прописана логика для Android (как мы сделали ранее), 
# то просто берем Config.DB_URL.
db_url = Config.DB_URL

# 2. Создаем движок (Engine)
# check_same_thread=False обязателен для SQLite в многопоточных приложениях вроде Flet
engine = create_engine(
    db_url, 
    echo=Config.DB_ECHO, 
    connect_args={"check_same_thread": False}
)

# 3. Настраиваем фабрику сессий
# expire_on_commit=True гарантирует, что объекты (растения) будут подтягивать 
# свежие данные из базы после каждого сохранения/коммита.
SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine, 
    expire_on_commit=True
)

def init_db():
    """Создает все таблицы в базе данных при первом запуске"""
    try:
        Base.metadata.create_all(bind=engine)
        # Вывод пути в консоль поможет при отладке (через adb logcat на Android)
        print(f"✅ База данных инициализирована: {db_url}")
    except Exception as e:
        print(f"❌ Ошибка инициализации базы данных: {e}")

def get_db():
    """
    Генератор сессий для работы с БД.
    Используется так: with next(get_db()) as db: ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()