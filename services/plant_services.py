from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from database.models import Plant, PlantCatalog, PlantAlias, CareCalendar, GrowthLog

class PlantService:
    # поиск вида растения в справочнике
    @staticmethod
    def get_catalog_item_by_name(db: Session, name: str):
        # алгоритм поиска сначала пытается найти точное совпадение во вспомогательной таблице алиасов 
        # (нормализованные народные названия), и только если совпадений нет — ищет в основном каталоге. 
        # это обеспечивает высокую точность распознавания пользовательского ввода.
        
        # поиск по алиасам (нормализация)
        alias = db.query(PlantAlias).filter(PlantAlias.user_input == name.lower()).first()
        if alias:
            return db.query(PlantCatalog).filter(PlantCatalog.catalog_id == alias.catalog_id).first()
        
        # поиск напрямую в каталоге
        return db.query(PlantCatalog).filter(PlantCatalog.species_name == name).first()

    # добавление растения пользователю
    @staticmethod
    def create_user_plant(db: Session, user_id: int, catalog_id: int, custom_name: str = None):
        # создание паспорта растения подразумевает копирование базовых настроек ухода (интервалы полива) 
        # из глобального справочника. одновременно с этим инициализируется календарь событий, 
        # создавая первую задачу на полив, чтобы пользователь сразу видел растение в расписании.
        catalog_item = db.query(PlantCatalog).get(catalog_id)
        if not catalog_item:
            return None

        # создание объекта растения
        new_plant = Plant(
            user_id=user_id,
            catalog_id=catalog_id,
            custom_name=custom_name or catalog_item.species_name,
            last_watered_at=datetime.now(),
            status_text="healthy"
        )
        
        try:
            db.add(new_plant)
            db.flush() # получаем id без завершения транзакции

            # расчет даты следующего полива
            next_watering = datetime.now() + timedelta(days=catalog_item.default_watering_interval)
            
            # создание первой задачи
            first_task = CareCalendar(
                plant_id=new_plant.plant_id,
                task_type="watering",
                scheduled_date=next_watering.date(),
                is_completed=False
            )
            db.add(first_task)
            db.commit()
            db.refresh(new_plant)
            return new_plant
        except Exception:
            db.rollback()
            return None

    # получение списка активных растений
    @staticmethod
    def get_user_plants(db: Session, user_id: int):
        return db.query(Plant).filter(Plant.user_id == user_id, Plant.is_active == True).all()

    # фиксация прогресса роста
    @staticmethod
    def add_growth_log(db: Session, plant_id: int, height: float):
        new_log = GrowthLog(
            plant_id=plant_id,
            height=height,
            measured_at=datetime.now().date()
        )
        try:
            db.add(new_log)
            db.commit()
            return new_log
        except Exception:
            db.rollback()
            return None