import sys
import os
from datetime import datetime, timedelta 
from sqlalchemy.orm import Session
from database.session import init_db, SessionLocal
from database.models import User, PlantCatalog, Plant, PlantAlias
from werkzeug.security import generate_password_hash

# Настройка пути для корректного импорта модулей
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def seed_data():
    # 1. Жесткая миграция: удаляем старый файл базы, чтобы применить новую схему User
    db_path = "greenthumb.db"
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
            print("🧹 Старая база данных удалена для обновления структуры")
        except Exception as e:
            print(f"⚠️ Не удалось удалить БД (возможно, она используется): {e}")

    # Инициализируем новую БД по обновленным моделям
    init_db()
    db = SessionLocal()

    # 2. Создание пользователя с поддержкой политики блокировки
    user_email = "test@mail.ru"
    hashed_password = generate_password_hash("123")
    
    user = User(
        email=user_email, 
        password_hash=hashed_password, 
        first_name="Илья",
        failed_login_attempts=0, # Инициализируем счетчик ошибок
        locked_until=None         # Аккаунт изначально разблокирован
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    print(f"✅ Пользователь создан: {user_email} (пароль: 123)")

    # 3. Наполнение глобального каталога (Твои данные без изменений)
    catalog_items_data = [
        {
            "species_name": "Алоэ Вера",
            "latin_name": "Aloe barbadensis miller",
            "description": "Популярный суккулент с мясистыми колючими листьями ценится за свои уникальные лечебные свойства. Растение эффективно очищает воздух в помещении и требует минимального внимания со стороны владельца. Оно отлично переносит засуху, но совершенно не терпит избыточного полива и застоя влаги у корней.",
            "default_watering_interval": 14,
            "default_light_level": 0.8,
            "aliases": ["алоэ", "столетник", "алое"]
        },
        {
            "species_name": "Петрушка",
            "latin_name": "Petroselinum crispum",
            "description": "Неприхотливая пряная трава является незаменимым источником витаминов и ярким украшением домашнего подоконника. Культура крайне нуждается в регулярном увлажнении почвы и хорошем освещении для быстрого роста зелени. Молодые листья можно употреблять в пищу уже через несколько недель после появления первых всходов.",
            "default_watering_interval": 3,
            "default_light_level": 0.7,
            "aliases": ["петрушка кудрявая", "зелень"]
        },
        {
            "species_name": "Роза",
            "latin_name": "Rosa chinensis",
            "description": "Элегантная миниатюрная роза была специально выведена для успешного выращивания в условиях обычных городских квартир. Это растение требует строгого соблюдения режима полива и очень чувствительно к уровню влажности воздуха. Для обильного и продолжительного цветения ей необходимо обеспечить яркий рассеянный солнечный свет.",
            "default_watering_interval": 5,
            "default_light_level": 0.9,
            "aliases": ["роза комнатная"]
        },
        {
            "species_name": "Гибискус",
            "latin_name": "Hibiscus rosa-sinensis",
            "description": "Красивое вечнозеленое дерево более известно среди цветоводов под поэтичным названием китайская роза. Крупные яркие бутоны живут всего один день, но при правильном уходе новые цветы появляются постоянно. Растение очень любит теплое пространство и активно развивается в просторных горшках с хорошим дренажем.",
            "default_watering_interval": 4,
            "default_light_level": 0.8,
            "aliases": ["китайская роза", "гибискус"]
        }
    ]

    for item_data in catalog_items_data:
        new_cat = PlantCatalog(
            species_name=item_data["species_name"],
            latin_name=item_data["latin_name"],
            description=item_data["description"],
            default_watering_interval=item_data["default_watering_interval"],
            default_light_level=item_data["default_light_level"]
        )
        db.add(new_cat)
        db.flush()
        
        for alias_text in item_data.get("aliases", []):
            new_alias = PlantAlias(
                user_input=alias_text.lower(),
                catalog_id=new_cat.catalog_id
            )
            db.add(new_alias)

    db.commit()
    print("✅ Каталог и Алиасы наполнены")

    # 4. Добавление растений пользователю (Твои пути к картинкам сохранены)
    cats = {c.species_name: c.catalog_id for c in db.query(PlantCatalog).all()}
    
    my_plants = [
        Plant(
            user_id=user.user_id,
            catalog_id=cats.get("Алоэ Вера"),
            custom_name="Алоэ Вера",
            image_url="plants/aloe.png",
            last_watered_at=datetime.now() - timedelta(days=2),
            user_light_level=0.9,  
            status_text="Рост: 15.0 см",
            is_active=True
        ),
        Plant(
            user_id=user.user_id,
            catalog_id=cats.get("Петрушка"),
            custom_name="Петрушка",
            image_url="plants/petrushka.png",
            last_watered_at=datetime.now(),
            user_light_level=0.4,  
            status_text="Рост: 10.5 см",
            is_active=True
        )
    ]
    db.add_all(my_plants)
    db.commit()
    print(f"✅ В личный сад добавлено {len(my_plants)} растений")

    db.close()

if __name__ == "__main__":
    seed_data()