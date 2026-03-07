from sqlalchemy.orm import Session
from datetime import datetime, timedelta
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
    def confirm_and_create_plant(db: Session, user_id: int, catalog_data: dict, custom_name: str = None, image_bytes: bytes = None):
        # процесс окончательной регистрации растения с верификацией данных. 
        # метод получает проверенные или отредактированные пользователем данные, 
        # проверяет наличие вида в справочнике и, если вид новый, вносит его в каталог. 
        # после этого создается личный экземпляр растения и планируется календарь.
        
        species_name = catalog_data.get('species_name')
        
        # 1. проверка наличия вида в глобальном каталоге
        catalog_item = db.query(PlantCatalog).filter_by(species_name=species_name).first()
        
        if not catalog_item:
            # создание новой записи в справочнике на основе одобренных данных
            try:
                catalog_item = PlantCatalog(
                    species_name=species_name,
                    latin_name=catalog_data.get('latin_name'),
                    description=catalog_data.get('description'),
                    default_watering_interval=catalog_data.get('watering_interval', 7),
                    default_light_level=catalog_data.get('light_level', 0.5)
                )
                db.add(catalog_item)
                db.flush() # получаем id для связей
            except Exception:
                db.rollback()
                return None, "Ошибка при создании нового вида в справочнике."

        # 2. создание персонального экземпляра растения
        # оптимизация и сохранение фото происходит через FileService
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

            # автоматическая инициализация цикла ухода
            next_watering = datetime.now() + timedelta(days=catalog_item.default_watering_interval)
            
            first_task = CareCalendar(
                plant_id=new_plant.plant_id,
                task_type="watering",
                scheduled_date=next_watering.date(),
                is_completed=False
            )
            db.add(first_task)
            db.commit()
            db.refresh(new_plant)
            return new_plant, None
        except Exception as e:
            db.rollback()
            return None, f"Ошибка при добавлении растения: {str(e)}."

    @staticmethod
    def add_measurement(db: Session, plant_id: int, height: float, note: str = "", image_bytes: bytes = None):
        # фиксация прогресса развития растения. 
        # ручной ввод высоты пользователем обеспечивает точность технических данных. 
        # фотофиксация (опционально) сохраняется в папку logs для визуального мониторинга.
        image_path = FileService.process_and_save(image_bytes, subfolder="logs")
        
        new_log = GrowthLog(
            plant_id=plant_id,
            height=height,
            note=note,
            image_path=image_path
        )
        try:
            db.add(new_log)
            # обновление статуса в основной таблице для быстрого доступа
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
    def get_user_plants(db: Session, user_id: int):
        # получение списка всех активных растений из коллекции пользователя
        return db.query(Plant).filter(Plant.user_id == user_id, Plant.is_active == True).all()