import os
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime, date, timedelta

from config import Config
from database.models import Plant, PlantCatalog, PlantAlias, CareCalendar, GrowthLog
from .file_service import FileService

class PlantService:
    @staticmethod
    def get_catalog_item_by_name(db: Session, name: str):
        """
        Стандартный поиск вида в справочнике. 
        """
        if not name:
            return None
            
        alias = db.query(PlantAlias).filter(PlantAlias.user_input == name.lower()).first()
        if alias:
            return db.query(PlantCatalog).filter(PlantCatalog.catalog_id == alias.catalog_id).first()
        
        return db.query(PlantCatalog).filter(PlantCatalog.species_name == name).first()

    @staticmethod
    def get_or_create_catalog_item(db: Session, ai_service, user_id: int, query: str):
        """
        Алгоритм автоматического расширения справочника. 
        """
        item = PlantService.get_catalog_item_by_name(db, query)
        if item:
            return item, None

        norm_data, err = ai_service.identify_by_name(db, user_id, query)
        if err or not norm_data or not norm_data.get('is_plant'):
            return None, "Растение не найдено в базе и не опознано ассистентом."

        standard_name = norm_data['standard_name']
        
        item = db.query(PlantCatalog).filter_by(species_name=standard_name).first()
        if item:
            return item, None

        passport, err = ai_service.get_passport_data(db, user_id, standard_name)
        if err:
            return None, f"Ошибка при получении данных от ИИ: {err}."

        try:
            new_catalog_item = PlantCatalog(
                species_name=passport.get('species_name', standard_name),
                latin_name=passport.get('latin_name', 'Unknown'),
                description=passport.get('description', ''),
                default_watering_interval=int(passport.get('watering_interval', 7)),
                default_light_level=float(passport.get('light_level', 0.5))
            )
            db.add(new_catalog_item)
            db.flush() 

            new_alias = PlantAlias(user_input=query.lower(), catalog_id=new_catalog_item.catalog_id)
            db.add(new_alias)
            db.flush()
            
            # Мы не делаем здесь commit, так как обычно это часть большой транзакции создания растения
            return new_catalog_item, None
            
        except Exception as e:
            db.rollback()
            return None, f"Ошибка при обновлении справочника: {str(e)}."

    @staticmethod
    def confirm_and_create_plant(db: Session, user_id: int, catalog_data: dict, custom_name: str = None, image_bytes: bytes = None, height: float = 10.0):
        """
        Регистрация растения в коллекции. 
        """
        species_name = catalog_data.get('species_name')
        catalog_item = db.query(PlantCatalog).filter_by(species_name=species_name).first()
        
        if not catalog_item:
            try:
                catalog_item = PlantCatalog(
                    species_name=species_name,
                    latin_name=catalog_data.get('latin_name'),
                    description=catalog_data.get('description'),
                    default_watering_interval=int(catalog_data.get('watering_interval', 7)),
                    default_light_level=float(catalog_data.get('light_level', 0.5))
                )
                db.add(catalog_item)
                db.flush()
            except Exception:
                db.rollback()
                return None, "Ошибка при создании нового вида в справочнике."

        # Сохранение фото
        image_url = FileService.process_and_save(image_bytes, subfolder="plants")

        new_plant = Plant(
            user_id=user_id,
            catalog_id=catalog_item.catalog_id,
            custom_name=custom_name or catalog_item.species_name,
            image_url=image_url,
            last_watered_at=datetime.now(),
            user_light_level=catalog_data.get('light_level', 0.5),
            status_text=f"Рост: {height} см",
            is_active=True
        )
        
        try:
            db.add(new_plant)
            db.flush() 

            # 1. Запись в журнал роста
            new_log = GrowthLog(
                plant_id=new_plant.plant_id, 
                height=height, 
                note="Первоначальная посадка",
                measured_at=date.today()
            )
            db.add(new_log)

            # 2. Планирование первой задачи
            db.add(CareCalendar(
                plant_id=new_plant.plant_id, 
                task_type="watering", 
                scheduled_date=date.today(),
                is_completed=False
            ))
            
            # ФИНАЛЬНЫЙ КОММИТ
            db.commit() 
            db.refresh(new_plant)
            
            return new_plant, None
        except Exception as e:
            db.rollback()
            return None, f"Ошибка при добавлении растения: {str(e)}."

    @staticmethod
    def add_measurement(db: Session, plant_id: int, height: float, note: str = "", image_bytes: bytes = None):
        image_path = FileService.process_and_save(image_bytes, subfolder="logs")
        
        new_log = GrowthLog(plant_id=plant_id, height=height, note=note, image_path=image_path)
        try:
            db.add(new_log)
            plant = db.query(Plant).get(plant_id)
            if plant:
                plant.status_text = f"Рост: {height} см"
            
            db.commit()
            db.refresh(new_log)
            return new_log, None
        except Exception as e:
            db.rollback()
            return None, f"Ошибка сохранения данных прогресса: {str(e)}."

    @staticmethod
    def archive_plant(db: Session, plant_id: int, reason: str = "убрано"):
        plant = db.query(Plant).get(plant_id)
        if not plant: return None, "Растение не найдено."

        try:
            plant.is_active = False
            plant.status_text = f"В архиве ({reason})"
            
            db.query(CareCalendar).filter(
                CareCalendar.plant_id == plant_id, 
                CareCalendar.is_completed == False
            ).delete()
            
            db.commit()
            return plant, None
        except Exception as e:
            db.rollback()
            return None, f"Ошибка при архивации: {str(e)}."

    @staticmethod
    def get_user_plants(db: Session, user_id: int):
        return db.query(Plant).filter(Plant.user_id == user_id, Plant.is_active == True).all()

    @staticmethod
    def get_archived_plants(db: Session, user_id: int):
        return db.query(Plant).filter(Plant.user_id == user_id, Plant.is_active == False).all()

    @staticmethod
    def delete_plant_permanently(db: Session, plant_id: int):
        plant = db.query(Plant).get(plant_id)
        if not plant: return False, "Растение не найдено."

        image_path = plant.image_url
        try:
            db.delete(plant)
            db.commit()
            
            if image_path:
                full_path = os.path.join(Config.UPLOAD_DIR, image_path)
                if os.path.exists(full_path):
                    os.remove(full_path)
            
            return True, None
        except Exception as e:
            db.rollback()
            return False, f"Ошибка при полном удалении: {str(e)}."