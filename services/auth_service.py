from sqlalchemy.orm import Session
from database.models import User
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta

# максимальное количество разрешенных ошибок ввода до срабатывания защиты от подбора пароля
MAX_ATTEMPTS = 5
# время в минутах на которое закрывается доступ к аккаунту при подозрении на взлом
LOCKOUT_MINUTES = 15

class AuthService:
    @staticmethod
    def login(db: Session, email: str, password: str):
        # приведение почты к нижнему регистру и удаление лишних пробелов для исключения ошибок ввода
        email_clean = email.lower().strip()
        # попытка найти запись о пользователе в таблице базы данных по уникальному адресу почты
        user = db.query(User).filter(User.email == email_clean).first()
        
        if not user:
            # возврат сообщения об ошибке если аккаунт с таким логином не зарегистрирован в системе
            return None, "Пользователь не найден"

        # 1. блок проверки временного ограничения доступа (account lockout)
        # проверяем существует ли метка времени блокировки и не наступило ли время разблокировки
        if user.locked_until and user.locked_until > datetime.now():
            # вычисление остатка времени ожидания для вывода понятного уведомления пользователю
            remaining = user.locked_until - datetime.now()
            mins = (remaining.seconds // 60) + 1
            return None, f"Доступ заблокирован. Попробуйте через {mins} мин."

        # 2. блок верификации личности через криптографическую проверку хеша
        # функция сравнивает введенный пароль с зашифрованной сигнатурой в базе данных
        if check_password_hash(user.password_hash, password):
            # при успешном входе обнуляем счетчик ошибок и снимаем все ограничения
            user.failed_login_attempts = 0
            user.locked_until = None
            db.commit() # сохранение обновленного состояния безопасности в бд
            return user, None
        else:
            # инкремент счетчика неудачных попыток при несовпадении пароля
            user.failed_login_attempts += 1
            
            # реализация триггера блокировки: если лимит попыток исчерпан — закрываем вход
            if user.failed_login_attempts >= MAX_ATTEMPTS:
                # установка времени до которого вход в систему будет запрещен
                user.locked_until = datetime.now() + timedelta(minutes=LOCKOUT_MINUTES)
                user.failed_login_attempts = 0  # сброс счетчика для чистого старта после разблокировки
                db.commit()
                return None, f"Слишком много попыток. Вход заблокирован на {LOCKOUT_MINUTES} мин."
            
            db.commit() # фиксация каждой неудачной попытки в базе для предотвращения обхода через перезапуск
            # информирование пользователя о количестве оставшихся попыток до активации бана
            attempts_left = MAX_ATTEMPTS - user.failed_login_attempts
            return None, f"Неверный пароль. Осталось попыток: {attempts_left}"

    @staticmethod
    def register(db: Session, email: str, password: str, name: str):
        # нормализация входных данных для обеспечения целостности реестра пользователей
        email_clean = email.lower().strip()
        
        # обязательная проверка на уникальность: один email может принадлежать только одному аккаунту
        existing = db.query(User).filter(User.email == email_clean).first()
        if existing:
            return None, "Этот Email уже зарегистрирован"
        
        try:
            # 3. блок безопасного создания учетной записи
            # генерация одностороннего хеша пароля: система никогда не хранит пароли в открытом виде
            new_user = User(
                email=email_clean,
                password_hash=generate_password_hash(password), # использование алгоритма scrypt/pbkdf2
                first_name=name.strip(),
                failed_login_attempts=0 # инициализация чистого счетчика для нового пользователя
            )
            db.add(new_user) # постановка объекта в очередь на запись
            db.commit() # выполнение транзакции по созданию записи в базе данных
            db.refresh(new_user) # получение сгенерированного id и других системных полей из бд
            return new_user, None
        except Exception as e:
            # механизм обеспечения отказоустойчивости: отмена всех изменений при возникновении ошибки бд
            db.rollback()
            return None, f"Ошибка базы данных: {str(e)}"