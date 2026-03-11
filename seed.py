import sys
import os
import datetime
from datetime import datetime, timedelta 
from sqlalchemy.orm import Session
from database.session import init_db, SessionLocal
from database.models import User, PlantCatalog, Plant, PlantAlias # ДОБАВЛЯЕМ PLANTALIAS

# Настройка пути
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def seed_data():
    init_db()
    db = SessionLocal()

    # 1. Создаем пользователя
    user_email = "test@mail.ru"
    user = db.query(User).filter_by(email=user_email).first()
    
    if not user:
        user = User(email=user_email, password_hash="123", first_name="Илья")
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"✅ Пользователь создан: {user_email}")

    # 2. Наполняем Каталог (Справочник)
    catalog_items_data = [
        {
            "species_name": "Алоэ Вера",
            "latin_name": "Aloe barbadensis miller",
            "description": "Суккулент с целебными свойствами. Хранит запас влаги в толстых листьях.",
            "default_watering_interval": 14, # СИНХРОНИЗИРУЕМ С МОДЕЛЬЮ
            "default_light_level": 0.8,
            "aliases": ["алоэ", "столетник", "алое", "доктор"]
        },
        {
            "species_name": "Петрушка Кудрявая",
            "latin_name": "Petroselinum crispum",
            "description": "Пряное растение. Требует влажной почвы.",
            "default_watering_interval": 3,
            "default_light_level": 0.7,
            "aliases": ["петрушка", "зелень для салата"]
        },
        {
            "species_name": "Роза Комнатная",
            "latin_name": "Rosa chinensis",
            "description": "Миниатюрная роза. Требует внимательного ухода.",
            "default_watering_interval": 5,
            "default_light_level": 0.9,
            "aliases": ["роза", "красивый цветок"]
        },
        {
            "species_name": "Гибискус",
            "latin_name": "Hibiscus rosa-sinensis",
            "description": "Китайская роза. Любит тепло и свет.",
            "default_watering_interval": 4,
            "default_light_level": 0.8,
            "aliases": ["китайская роза", "гибискус"]
        }
    ]

    for item_data in catalog_items_data:
        exists = db.query(PlantCatalog).filter_by(species_name=item_data["species_name"]).first()
        if not exists:
            new_cat = PlantCatalog(
                species_name=item_data["species_name"],
                latin_name=item_data["latin_name"],
                description=item_data["description"],
                default_watering_interval=item_data["default_watering_interval"],
                default_light_level=item_data["default_light_level"]
            )
            db.add(new_cat)
            db.flush()
            
            # НОВЫЙ БЛОК: ДОБАВЛЕНИЕ АЛИАСОВ
            for alias_text in item_data.get("aliases", []):
                new_alias = PlantAlias(
                    user_input=alias_text.lower(),
                    catalog_id=new_cat.catalog_id
                )
                db.add(new_alias)

    db.commit()
    print("✅ Каталог и Алиасы наполнены")

    # 3. Добавляем растения пользователю (Адаптировано под новые поля)
    cats = {c.species_name: c.catalog_id for c in db.query(PlantCatalog).all()}
    
    if db.query(Plant).filter_by(user_id=user.user_id).count() == 0:
        my_plants = [
            Plant(
                user_id=user.user_id,
                catalog_id=cats.get("Алоэ Вера"),
                custom_name="Алоэ на подоконнике",
                image_url="/aloe.png",
                last_watered_at=datetime.now() - timedelta(days=2),
                status_text="Отличное состояние. Подарок от дедушки.",
                is_active=True
            ),
            Plant(
                user_id=user.user_id,
                catalog_id=cats.get("Петрушка Кудрявая"),
                custom_name="Зелень для салата",
                image_url="/petrushka.png",
                last_watered_at=datetime.now(),
                status_text="Стадия: Рассада. Посеяна в феврале.",
                is_active=True
            ),
            Plant(
                user_id=user.user_id,
                catalog_id=cats.get("Роза Комнатная"),
                custom_name="Красавица",
                image_url="/rose.png",
                last_watered_at=datetime.now() - timedelta(days=1),
                status_text="Требует внимания: опрыскивать листья.",
                is_active=True
            )
        ]
        db.add_all(my_plants)
        db.commit()
        print(f"✅ В сад добавлено {len(my_plants)} растений")

    db.close()

if __name__ == "__main__":
    seed_data()