from sqlalchemy.orm import Session
from database.models import User
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta

# Константы политики безопасности
MAX_ATTEMPTS = 5
LOCKOUT_MINUTES = 15

class AuthService:
    @staticmethod
    def login(db: Session, email: str, password: str):
        email_clean = email.lower().strip()
        user = db.query(User).filter(User.email == email_clean).first()
        
        if not user:
            return None, "Пользователь не найден"

        # 1. Проверка активной блокировки
        if user.locked_until and user.locked_until > datetime.now():
            remaining = user.locked_until - datetime.now()
            mins = (remaining.seconds // 60) + 1
            return None, f"Доступ заблокирован. Попробуйте через {mins} мин."

        # 2. Проверка соответствия хеша пароля
        if check_password_hash(user.password_hash, password):
            # Успешный вход: сброс счетчика ошибок и блокировки
            user.failed_login_attempts = 0
            user.locked_until = None
            db.commit()
            return user, None
        else:
            # Ошибка входа: инкремент счетчика неудачных попыток
            user.failed_login_attempts += 1
            
            # Если лимит попыток исчерпан — устанавливаем блокировку
            if user.failed_login_attempts >= MAX_ATTEMPTS:
                user.locked_until = datetime.now() + timedelta(minutes=LOCKOUT_MINUTES)
                user.failed_login_attempts = 0  # Сброс для возможности входа после LOCKOUT
                db.commit()
                return None, f"Слишком много попыток. Вход заблокирован на {LOCKOUT_MINUTES} мин."
            
            db.commit()
            attempts_left = MAX_ATTEMPTS - user.failed_login_attempts
            return None, f"Неверный пароль. Осталось попыток: {attempts_left}"

    @staticmethod
    def register(db: Session, email: str, password: str, name: str):
        email_clean = email.lower().strip()
        
        # Проверка на уникальность почты
        existing = db.query(User).filter(User.email == email_clean).first()
        if existing:
            return None, "Этот Email уже зарегистрирован"
        
        try:
            # Создание нового пользователя с хешированным паролем
            new_user = User(
                email=email_clean,
                password_hash=generate_password_hash(password),
                first_name=name.strip(),
                failed_login_attempts=0
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            return new_user, None
        except Exception as e:
            db.rollback()
            return None, f"Ошибка базы данных: {str(e)}"