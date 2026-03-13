from sqlalchemy.orm import Session
from database.models import User
# Добавляем необходимые инструменты для защиты
from werkzeug.security import generate_password_hash, check_password_hash

class AuthService:
    @staticmethod
    def login(db: Session, email: str, password: str):
        # 1. Приводим к нижнему регистру, чтобы не было проблем с регистром
        email = email.lower().strip()
        
        user = db.query(User).filter(User.email == email).first()
        
        # 2. ИСПОЛЬЗУЕМ БЕЗОПАСНУЮ ПРОВЕРКУ
        # Она берет хеш из базы и сравнивает с введенным паролем
        if user and check_password_hash(user.password_hash, password):
            return user
        return None

    @staticmethod
    def register(db: Session, email: str, password: str, name: str):
        # 1. Приводим почту к нижнему регистру
        email = email.lower().strip()
        
        # Проверка на существование
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            return None
        
        # 2. ГЕНЕРИРУЕМ ХЕШ ВМЕСТО ПАРОЛЯ
        hashed_password = generate_password_hash(password)
        
        new_user = User(
            email=email,
            password_hash=hashed_password, # Вот теперь в базу пойдет абракадабра
            first_name=name
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user