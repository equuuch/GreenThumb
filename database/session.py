from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import Config
from .models import Base

# используем типизированный url из центрального конфига
engine = create_engine(
    Config.DB_URL, 
    echo=Config.DB_ECHO, # здесь уже гарантированно bool благодаря config.py
    connect_args={"check_same_thread": False}
)

# фабрика сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    # автоматическое создание таблиц при старте
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"Ошибка инициализации базы данных: {e}")

def get_db():
    # генератор сессии для управления жизненным циклом соединений с бд
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()