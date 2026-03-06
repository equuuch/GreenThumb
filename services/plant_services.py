from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from database.models import Plant, PlantCatalog, PlantAlias, CareCalendar, GrowthLog

class PlantService:
    @staticmethod
    def get_catalog_item_by_name(db: Session, name: str):
        # 1. поиск через таблицу алиасов (нормализация)
        alias = db.query(PlantAlias).filter(PlantAlias.user_input == name.lower()).first()
        if alias:
            return db.query(PlantCatalog).filter(PlantCatalog.catalog_id == alias.catalog_id).first()
        
        # 2. поиск напрямую в справочнике
        return db.query(PlantCatalog).filter(PlantCatalog.species_name == name).first()

    @staticmethod
    def create_user_plant(db: Session, user_id: int, catalog_id: int, custom_name: str = None):
        catalog_item = db.query(PlantCatalog).get(catalog_id)
        if not catalog_item:
            return None

        # создание паспорта растения (копирование интервалов из справочника)
        new_plant = Plant(
            user_id=user_id,
            catalog_id=catalog_id,
            custom_name=custom_name or catalog_item.species_name,
            last_watered_at=datetime.now(),
            status_text="healthy"
        )
        db.add(new_plant)
        db.flush() 

        # автоматическое создание первой задачи в календаре
        next_watering = datetime.now() + timedelta(days=catalog_item.default_watering_interval)
        first_task = CareCalendar(
            plant_id=new_plant.plant_id,
            task_type="watering",
            scheduled_date=next_watering.date(),
            is_completed=False
        )
        db.add(first_task)
        db.commit()
        return new_plant

    @staticmethod
    def get_user_plants(db: Session, user_id: int):
        return db.query(Plant).filter(Plant.user_id == user_id, Plant.is_active == True).all()

    @staticmethod
    def add_growth_log(db: Session, plant_id: int, height: float):
        new_log = GrowthLog(
            plant_id=plant_id,
            height=height,
            measured_at=datetime.now().date()
        )
        db.add(new_log)
        db.commit()
        return new_log