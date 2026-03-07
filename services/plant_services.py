from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from database.models import Plant, PlantCatalog, PlantAlias, CareCalendar, GrowthLog
from .file_service import FileService
import json

class PlantService:
    @staticmethod
    def get_catalog_item_by_name(db: Session, name: str):
        # стандартный поиск по базе через алиасы и официальные названия.
        alias = db.query(PlantAlias).filter(PlantAlias.user_input == name.lower()).first()
        if alias:
            return db.query(PlantCatalog).filter(PlantCatalog.catalog_id == alias.catalog_id).first()
        return db.query(PlantCatalog).filter(PlantCatalog.species_name == name).first()

    @staticmethod
    def get_or_create_catalog_item(db: Session, ai_service, user_id: int, query: str):
        # алгоритм автоматического расширения справочника. 
        # 1. ищем в локальной базе. 
        # 2. если не нашли — просим ии нормализовать имя. 
        # 3. если это растение — генерируем паспорт и сохраняем в каталог. 
        # это позволяет приложению бесконечно расширять список доступных видов.
        
        # 1. попытка локального поиска
        item = PlantService.get_catalog_item_by_name(db, query)
        if item:
            return item, None

        # 2. если в базе нет, идем в ИИ для нормализации
        norm_data, err = ai_service.identify_by_name(db, user_id, query)
        if err or not norm_data.get('is_plant'):
            return None, "Растение не найдено в базе и не опознано ассистентом."

        standard_name = norm_data['standard_name']
        
        # проверяем, может под стандартным именем оно уже есть в базе
        item = db.query(PlantCatalog).filter(PlantCatalog.species_name == standard_name).first()
        if item:
            return item, None

        # 3. генерируем паспорт через ИИ для нового вида
        passport, err = ai_service.get_passport_data(db, user_id, standard_name)
        if err:
            return None, f"Ошибка при получении данных от ИИ: {err}"

        # 4. сохраняем новый вид в глобальный справочник
        try:
            new_catalog_item = PlantCatalog(
                species_name=passport['species_name'],
                latin_name=passport['latin_name'],
                description=passport['description'],
                default_watering_interval=passport['watering_interval'],
                default_light_level=passport['light_level']
            )
            db.add(new_catalog_item)
            db.flush()

            # добавляем исходный запрос пользователя как алиас для будущего поиска
            new_alias = PlantAlias(
                user_input=query.lower(),
                catalog_id=new_catalog_item.catalog_id
            )
            db.add(new_alias)
            db.commit()
            db.refresh(new_catalog_item)
            return new_catalog_item, None
            
        except Exception as e:
            db.rollback()
            return None, f"Ошибка при обновлении справочника: {str(e)}."

    @staticmethod
    def create_user_plant(db: Session, user_id: int, catalog_id: int, custom_name: str = None, image_bytes: bytes = None):
        # логика регистрации растения остается прежней
        catalog_item = db.query(PlantCatalog).get(catalog_id)
        if not catalog_item: return None
        
        image_url = FileService.process_and_save(image_bytes, subfolder="plants")
        
        new_plant = Plant(
            user_id=user_id,
            catalog_id=catalog_id,
            custom_name=custom_name or catalog_item.species_name,
            image_url=image_url,
            last_watered_at=datetime.now(),
            status_text="healthy"
        )
        try:
            db.add(new_plant)
            db.flush() 
            next_watering = datetime.now() + timedelta(days=catalog_item.default_watering_interval)
            db.add(CareCalendar(plant_id=new_plant.plant_id, task_type="watering", scheduled_date=next_watering.date()))
            db.commit()
            db.refresh(new_plant)
            return new_plant
        except Exception:
            db.rollback()
            return None