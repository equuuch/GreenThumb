import json
from database.session import SessionLocal, init_db
from database.models import PlantCatalog, PlantAlias

INITIAL_PLANTS = [
    {
        "species_name": "Ландыш",
        "latin_name": "Convallaria majalis",
        "description": "Травянистое цветковое растение с ароматными белыми колокольчатыми цветками.",
        "default_watering_interval": 7,
        "default_light_level": 0.5,
        "aliases": ["ландыш", "конваллярия", "ландыш майский", "колокольчики", "лесной колокольчик"]
    },
    {
        "species_name": "Монстера Деликатесная",
        "latin_name": "Monstera deliciosa",
        "description": "Крупная лиана с характерными перфорированными листьями. Любит влажность.",
        "default_watering_interval": 10,
        "default_light_level": 0.6,
        "aliases": ["монстера", "монстера привлекательная", "дырявый цветок", "монстера деликатесная", "филодендрон дырявый"]
    },
    {
        "species_name": "Сансевиерия",
        "latin_name": "Sansevieria trifasciata",
        "description": "Неприхотливое растение, известное как 'Щучий хвост'. Выдерживает тень.",
        "default_watering_interval": 21,
        "default_light_level": 0.3,
        "aliases": ["тещин язык", "щучий хвост", "санса", "сансивьерия", "змеиная кожа", "меч", "индийский меч"]
    },
    {
        "species_name": "Томат Черри",
        "latin_name": "Solanum lycopersicum",
        "description": "Скороспелый сорт для домашнего и садового выращивания. Требует много света.",
        "default_watering_interval": 3,
        "default_light_level": 0.9,
        "aliases": ["помидорки", "черри", "томаты", "вишневидный томат", "черри на подоконнике", "помидорчики"]
    },
    {
        "species_name": "Фикус Бенджамина",
        "latin_name": "Ficus benjamina",
        "description": "Популярное комнатное дерево с мелкими листьями. Чувствителен к перестановке.",
        "default_watering_interval": 7,
        "default_light_level": 0.7,
        "aliases": ["фикус", "бенджамин", "фикус бенджамина", "плакучее дерево", "фикус мелколистный"]
    },
    {
        "species_name": "Алоэ Вера",
        "latin_name": "Aloe barbadensis",
        "description": "Суккулент с целебными свойствами. Хранит запас влаги в толстых листьях.",
        "default_watering_interval": 14,
        "default_light_level": 0.8,
        "aliases": ["алоэ", "столетник", "алое", "лекарственный алоэ", "алоэ вера", "доктор"]
    }
]

def seed_database():
    init_db()
    db = SessionLocal()
    
    try:
        for plant_data in INITIAL_PLANTS:
            exists = db.query(PlantCatalog).filter_by(species_name=plant_data["species_name"]).first()
            if not exists:
                new_plant = PlantCatalog(
                    species_name=plant_data["species_name"],
                    latin_name=plant_data["latin_name"],
                    description=plant_data["description"],
                    default_watering_interval=plant_data["default_watering_interval"],
                    default_light_level=plant_data["default_light_level"]
                )
                db.add(new_plant)
                db.flush()
                
                for alias_name in plant_data["aliases"]:
                    new_alias = PlantAlias(
                        user_input=alias_name.lower(),
                        catalog_id=new_plant.catalog_id
                    )
                    db.add(new_alias)
        
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()