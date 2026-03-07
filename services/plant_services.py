from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from database.models import Plant, PlantCatalog, PlantAlias, CareCalendar
from .file_service import FileService

class PlantService:
    @staticmethod
    def get_catalog_item_by_name(db: Session, name: str):
        alias = db.query(PlantAlias).filter(PlantAlias.user_input == name.lower()).first()
        if alias:
            return db.query(PlantCatalog).filter(PlantCatalog.catalog_id == alias.catalog_id).first()
        return db.query(PlantCatalog).filter(PlantCatalog.species_name == name).first()

    @staticmethod
    def create_user_plant(db: Session, user_id: int, catalog_id: int, custom_name: str = None, image_bytes: bytes = None):
        catalog_item = db.query(PlantCatalog).get(catalog_id)
        if not catalog_item:
            return None

        # сохраняем фото через наш новый сервис
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