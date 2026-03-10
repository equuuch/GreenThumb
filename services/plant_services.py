import os
from sqlalchemy.orm import Session
<<<<<<< HEAD
from database.models import Plant, PlantCatalog, CareCalendar

class PlantService:
    @staticmethod
    def get_user_plants(db: Session, user_id: int):
        # Получаем растения пользователя вместе с информацией из каталога
        return db.query(Plant).filter(Plant.user_id == user_id, Plant.is_active == True).all()

    @staticmethod
    def get_todays_tasks(db: Session, user_id: int):
        # Заглушка: возвращаем задачи для демонстрации
        # В будущем здесь будет выборка из CareCalendar по дате
        return [
            {"icon": "WATER_DROP", "text": "Полить Петрушку", "color": "#009753"},
            {"icon": "WB_SUNNY", "text": "Поставить на свет Алоэ", "color": "#E65100"}
        ]
=======
from datetime import datetime, timedelta
from config import Config
from database.models import Plant, PlantCatalog, PlantAlias, CareCalendar, GrowthLog
from .file_service import FileService

class PlantService:
    @staticmethod
    def get_catalog_item_by_name(db: Session, name: str):
        # стандартный поиск вида в справочнике. 
        # алгоритм сначала проверяет таблицу алиасов для нормализации народных названий, 
        # затем выполняет поиск по официальному реестру.
        alias = db.query(PlantAlias).filter(PlantAlias.user_input == name.lower()).first()
        if alias:
            return db.query(PlantCatalog).filter(PlantCatalog.catalog_id == alias.catalog_id).first()
        
        return db.query(PlantCatalog).filter(PlantCatalog.species_name == name).first()

    @staticmethod
    def get_or_create_catalog_item(db: Session, ai_service, user_id: int, query: str):
        # алгоритм автоматического расширения справочника. 
        # метод ищет растение локально; при отсутствии совпадений инициирует 
        # цепочку запросов к ии для нормализации имени и генерации технического паспорта. 
        # новый вид сохраняется в базу, становясь доступным для всех пользователей.
        
        # 1. попытка локального поиска
        item = PlantService.get_catalog_item_by_name(db, query)
        if item:
            return item, None

        # 2. нормализация названия через ии
        norm_data, err = ai_service.identify_by_name(db, user_id, query)
        if err or not norm_data.get('is_plant'):
            return None, "Растение не найдено в базе и не опознано ассистентом."

        standard_name = norm_data['standard_name']
        
        # проверка по стандартному имени (защита от дублей)
        item = db.query(PlantCatalog).filter_by(species_name=standard_name).first()
        if item:
            return item, None

        # 3. генерация паспорта для нового вида
        passport, err = ai_service.get_passport_data(db, user_id, standard_name)
        if err:
            return None, f"Ошибка при получении данных от ИИ: {err}."

        # 4. запись нового вида в глобальный каталог
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

            # фиксируем исходный ввод пользователя как алиас для будущего поиска
            new_alias = PlantAlias(user_input=query.lower(), catalog_id=new_catalog_item.catalog_id)
            db.add(new_alias)
            db.commit()
            db.refresh(new_catalog_item)
            return new_catalog_item, None
            
        except Exception as e:
            db.rollback()
            return None, f"Ошибка при обновлении справочника: {str(e)}."

    @staticmethod
    def confirm_and_create_plant(db: Session, user_id: int, catalog_data: dict, custom_name: str = None, image_bytes: bytes = None):
        # регистрация растения в коллекции с верификацией данных. 
        # если вид отсутствует в глобальном каталоге, он создается на основе 
        # одобренных пользователем данных. одновременно инициализируется 
        # календарь ухода, создавая первую задачу на полив.
        
        species_name = catalog_data.get('species_name')
        catalog_item = db.query(PlantCatalog).filter_by(species_name=species_name).first()
        
        if not catalog_item:
            try:
                catalog_item = PlantCatalog(
                    species_name=species_name,
                    latin_name=catalog_data.get('latin_name'),
                    description=catalog_data.get('description'),
                    default_watering_interval=catalog_data.get('watering_interval', 7),
                    default_light_level=catalog_data.get('light_level', 0.5)
                )
                db.add(catalog_item)
                db.flush()
            except Exception:
                db.rollback()
                return None, "Ошибка при создании нового вида в справочнике."

        # сохранение и оптимизация фото
        image_url = FileService.process_and_save(image_bytes, subfolder="plants")

        new_plant = Plant(
            user_id=user_id,
            catalog_id=catalog_item.catalog_id,
            custom_name=custom_name or catalog_item.species_name,
            image_url=image_url,
            last_watered_at=datetime.now(),
            status_text="healthy"
        )
        
        try:
            db.add(new_plant)
            db.flush() 

            # планирование первого полива
            next_watering = datetime.now() + timedelta(days=catalog_item.default_watering_interval)
            db.add(CareCalendar(plant_id=new_plant.plant_id, task_type="watering", scheduled_date=next_watering.date()))
            
            db.commit()
            db.refresh(new_plant)
            return new_plant, None
        except Exception as e:
            db.rollback()
            return None, f"Ошибка при добавлении растения: {str(e)}."

    @staticmethod
    def add_measurement(db: Session, plant_id: int, height: float, note: str = "", image_bytes: bytes = None):
        # запись данных о физическом развитии растения. 
        # ручной ввод высоты гарантирует точность журнала, а фотофиксация 
        # позволяет визуально отслеживать состояние здоровья. метод 
        # автоматически обновляет краткий статус в основной таблице растений.
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
    def archive_plant(db: Session, plant_id: int, reason: str = "died"):
        # перевод растения в неактивное состояние. 
        # флаг is_active устанавливается в false, что скрывает растение из 
        # основного списка и прекращает генерацию задач в календаре. 
        # история логов и консультаций при этом сохраняется в базе.
        plant = db.query(Plant).get(plant_id)
        if not plant: return None, "Растение не найдено."

        try:
            plant.is_active = False
            plant.status_text = f"Архив: {reason}"
            
            # удаление всех невыполненных задач из календаря
            from database.models import CareCalendar
            db.query(CareCalendar).filter(CareCalendar.plant_id == plant_id, CareCalendar.is_completed == False).delete()
            
            db.commit()
            return plant, None
        except Exception as e:
            db.rollback()
            return None, f"Ошибка при архивации: {str(e)}."

    @staticmethod
    def get_user_plants(db: Session, user_id: int):
        # получение списка активных растений пользователя
        return db.query(Plant).filter(Plant.user_id == user_id, Plant.is_active == True).all()

    @staticmethod
    def get_archived_plants(db: Session, user_id: int):
        # получение списка архивных растений пользователя
        return db.query(Plant).filter(Plant.user_id == user_id, Plant.is_active == False).all()

    @staticmethod
    def delete_plant_permanently(db: Session, plant_id: int):
        # полное физическое удаление данных о растении. 
        # метод удаляет запись из бд (с каскадным удалением зависимых таблиц) 
        # и физически стирает файл изображения с диска для очистки хранилища.
        plant = db.query(Plant).get(plant_id)
        if not plant: return False, "Растение не найдено."

        image_path = plant.image_url
        try:
            db.delete(plant)
            db.commit()

            # удаление файла с диска
            if image_path:
                full_path = os.path.join(Config.UPLOAD_DIR, image_path)
                if os.path.exists(full_path):
                    os.remove(full_path)
            
            return True, None
        except Exception as e:
            db.rollback()
            return False, f"Ошибка при полном удалении: {str(e)}."
>>>>>>> d777a2f229709411c4e04c16c9dd93f40cfaaf90
