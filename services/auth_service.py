import re
from sqlalchemy.orm import Session
from werkzeug.security import generate_password_hash, check_password_hash
from database.models import User

# кастомное исключение для обработки ошибок доступа
class AuthError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class AuthService:
    # проверка формата почты через regex
    @staticmethod
    def _is_valid_email(email: str) -> bool:
        return re.match(r"[^@]+@[^@]+\.[^@]+", email) is not None

    # регистрация нового аккаунта
    @staticmethod
    def register_user(db: Session, email: str, password: str, name: str):
        # процесс регистрации включает нормализацию почты (приведение к нижнему регистру), 
        # проверку на дубликаты в базе данных и хеширование пароля перед сохранением. 
        # использование транзакции с rollback гарантирует, что база останется в консистентном состоянии при ошибках.
        if not email or not password:
            raise AuthError("Заполните все обязательные поля.")
        
        email_clean = email.strip().lower()
        
        if not AuthService._is_valid_email(email_clean):
            raise AuthError("Некорректный формат адреса электронной почты.")

        if len(password) < 6:
            raise AuthError("Пароль слишком короткий. Минимальная длина — 6 символов.")

        # проверка уникальности email
        if db.query(User).filter(User.email == email_clean).first():
            raise AuthError("Пользователь с такой почтой уже зарегистрирован.")
            
        new_user = User(
            email=email_clean,
            password_hash=generate_password_hash(password),
            first_name=name
        )
        
        try:
            db.add(new_user)
            db.commit()
            # принудительно обновляем объект из базы, чтобы подтянуть сгенерированный id
            # и избежать ошибок доступа к атрибутам после закрытия сессии.
            db.refresh(new_user)
            return new_user
        except Exception:
            db.rollback()
            raise AuthError("Ошибка при сохранении данных пользователя.")

    # проверка учетных данных
    @staticmethod
    def authenticate_user(db: Session, email: str, password: str):
        user = db.query(User).filter(User.email == email.lower()).first()
        
        if not user or not check_password_hash(user.password_hash, password):
            raise AuthError("Неверный адрес электронной почты или пароль.")
            
        return user