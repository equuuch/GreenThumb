from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import Config
from .models import Base

# Используем типизированный url из центрального конфига
engine = create_engine(
    Config.DB_URL, 
    echo=Config.DB_ECHO, 
    connect_args={"check_same_thread": False}
)

# ФАБРИКА СЕССИЙ: Добавил expire_on_commit=True
SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine, 
    expire_on_commit=True  # <--- Это заставит объекты обновляться после коммита
)

def init_db():
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"Ошибка инициализации базы данных: {e}")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()