import re
from sqlalchemy.orm import Session
from werkzeug.security import generate_password_hash, check_password_hash
from database.models import User

# ошибка авторизации
class AuthError(Exception):
    pass

class AuthService:
    # проверка валидности email
    @staticmethod
    def _is_valid_email(email: str) -> bool:
        return re.match(r"[^@]+@[^@]+\.[^@]+", email) is not None

    # регистрация пользователя
    @staticmethod
    def register_user(db: Session, email: str, password: str, name: str):
        if not email or not password:
            raise AuthError("Заполните все обязательные поля.")
        
        if not AuthService._is_valid_email(email):
            raise AuthError("Некорректный формат адреса электронной почты.")

        if len(password) < 6:
            raise AuthError("Пароль слишком короткий. Минимальная длина — 6 символов.")

        if db.query(User).filter(User.email == email.lower()).first():
            raise AuthError("Пользователь с такой почтой уже зарегистрирован.")
            
        new_user = User(
            email=email.lower(),
            password_hash=generate_password_hash(password),
            first_name=name
        )
        
        db.add(new_user)
        db.commit()
        return new_user

    # аутентификация пользователя
    @staticmethod
    def authenticate_user(db: Session, email: str, password: str):
        user = db.query(User).filter(User.email == email.lower()).first()
        
        if not user or not check_password_hash(user.password_hash, password):
            raise AuthError("Неверный адрес электронной почты или пароль.")
            
        return user