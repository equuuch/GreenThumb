from sqlalchemy.orm import Session
from database.models import User

class AuthService:
    @staticmethod
    def login(db: Session, email: str, password: str):
        # В реальном проекте здесь нужно хеширование паролей!
        # Пока делаем простую проверку для прототипа
        user = db.query(User).filter(User.email == email).first()
        if user and user.password_hash == password:
            return user
        return None

    @staticmethod
    def register(db: Session, email: str, password: str, name: str):
        # Проверка на существование
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            return None
        
        new_user = User(
            email=email,
            password_hash=password, # Тут надо бы хешировать
            first_name=name
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user