from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, and_
from datetime import datetime, date, timedelta
from database.models import Plant, CareCalendar, PlantCatalog

class CareService:
    @staticmethod
    def get_today_tasks(db: Session, user_id: int):
        """
        Получает список невыполненных задач на сегодня и прошлые даты 
        для активных растений пользователя.
        """
        today = date.today()
        # Используем современный select вместо db.query
        query = (
            select(CareCalendar)
            .options(joinedload(CareCalendar.plant))
            .join(Plant)
            .where(
                and_(
                    Plant.user_id == user_id,
                    CareCalendar.is_completed == False,
                    CareCalendar.scheduled_date <= today,
                    Plant.is_active == True
                )
            )
            .order_by(CareCalendar.scheduled_date)
        )
        return db.scalars(query).all()

    @staticmethod
    def complete_task(db: Session, task_id: int):
        """
        Помечает задачу как выполненную, обновляет статус растения 
        и автоматически создает следующую задачу на основе интервала.
        """
        # Используем Session.get() — это стандарт SQLAlchemy 2.0
        # Он заменяет устаревший db.query(Model).get(id)
        task = db.get(
            CareCalendar, 
            task_id, 
            options=[joinedload(CareCalendar.plant)]
        )
        
        if not task:
            return None, "Задача не найдена."

        # 1. Помечаем текущую задачу выполненной
        task.is_completed = True
        task.completion_date = datetime.now()
        
        # 2. Если это полив — обновляем дату последнего полива у растения
        plant = task.plant
        if task.task_type == "watering":
            plant.last_watered_at = datetime.now()
        
        # 3. Планируем следующую задачу
        # Достаем интервал из каталога (если его нет, берем неделю по умолчанию)
        catalog_item = db.get(PlantCatalog, plant.catalog_id)
        interval = catalog_item.default_watering_interval if (catalog_item and catalog_item.default_watering_interval) else 7
        
        next_date = date.today() + timedelta(days=interval)
        
        new_task = CareCalendar(
            plant_id=plant.plant_id,
            task_type=task.task_type,
            scheduled_date=next_date,
            is_completed=False
        )
        
        try:
            db.add(new_task)
            db.commit()
            # Обновляем объект, чтобы подтянуть ID новой задачи
            db.refresh(new_task)
            return new_task, None 
        except Exception as e:
            db.rollback()
            return None, f"Ошибка при сохранении: {str(e)}"

    @staticmethod
    def get_plant_schedule(db: Session, plant_id: int):
        """
        Возвращает все будущие задачи для конкретного растения.
        """
        query = (
            select(CareCalendar)
            .where(
                and_(
                    CareCalendar.plant_id == plant_id,
                    CareCalendar.is_completed == False
                )
            )
            .order_by(CareCalendar.scheduled_date)
        )
        return db.scalars(query).all()