import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Дальше твои старые импорты
from database.session import init_db, SessionLocal
# ... и так далее
from database.session import init_db, SessionLocal
from database.models import User, PlantCatalog, Plant
import datetime

def seed_data():
    init_db()
    db = SessionLocal()

    # 1. Создаем пользователя
    if not db.query(User).filter_by(email="test@mail.ru").first():
        user = User(
            email="test@mail.ru",
            password_hash="123", # Простой пароль
            first_name="Шахзод"
        )
        db.add(user)
        db.commit()
        print("✅ Пользователь создан (test@mail.ru / 123)")
    
    user = db.query(User).filter_by(email="test@mail.ru").first()

    # 2. Создаем Каталог (Справочник)
    catalog_data = [
        {"name": "Алоэ", "img": "/aloe.png", "water": 7},
        {"name": "Петрушка", "img": "/petrushka.png", "water": 3},
        {"name": "Роза", "img": "/rose.png", "water": 5},
        {"name": "Гибискус", "img": "/hibiscus.png", "water": 4},
    ]

    for item in catalog_data:
        if not db.query(PlantCatalog).filter_by(species_name=item["name"]).first():
            cat = PlantCatalog(
                species_name=item["name"],
                latin_name="Latin Name",
                description="Test description",
                default_watering_interval=item["water"],
                default_light_level=0.5
            )
            db.add(cat)
    db.commit()
    print("✅ Каталог наполнен")

    # 3. Добавляем растения пользователю
    # Находим ID каталога
    aloe_cat = db.query(PlantCatalog).filter_by(species_name="Алоэ").first()
    petr_cat = db.query(PlantCatalog).filter_by(species_name="Петрушка").first()

    if not db.query(Plant).filter_by(user_id=user.user_id).first():
        p1 = Plant(
            user_id=user.user_id,
            catalog_id=aloe_cat.catalog_id,
            custom_name="Алоэ",
            image_url="/aloe.png", # Используем твои ассеты
            last_watered_at=datetime.datetime.now()
        )
        p2 = Plant(
            user_id=user.user_id,
            catalog_id=petr_cat.catalog_id,
            custom_name="Петрушка",
            image_url="/petrushka.png",
            last_watered_at=datetime.datetime.now()
        )
        db.add_all([p1, p2])
        db.commit()
        print("✅ Растения добавлены в сад")

    db.close()

if __name__ == "__main__":
    seed_data()