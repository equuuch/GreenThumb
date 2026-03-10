from sqlalchemy.orm import Session
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