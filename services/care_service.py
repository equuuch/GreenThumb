from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from datetime import datetime, date, timedelta
from database.models import Plant, CareCalendar, PlantCatalog

class CareService:
    @staticmethod
    def get_today_tasks(db: Session, user_id: int):
        # получение списка всех невыполненных задач на сегодня и прошедшие даты. 
        # фильтрация по user_id через связь с таблицей растений гарантирует, 
        # что пользователь видит только свои уведомления. задачи сортируются 
        # по дате, чтобы просроченные дела всегда были в топе списка.
        
        today = date.today()
        query = (
            select(CareCalendar)
            .join(Plant)
            .where(
                and_(
                    Plant.user_id == user_id,
                    CareCalendar.is_completed == False,
                    CareCalendar.scheduled_date <= today
                )
            )
            .order_by(CareCalendar.scheduled_date)
        )
        return db.scalars(query).all()

    @staticmethod
    def complete_task(db: Session, task_id: int):
        # фиксация выполнения задачи и автоматическое планирование следующей. 
        # метод закрывает текущую задачу, обновляет дату последнего полива 
        # в паспорте растения и рассчитывает дату следующего обслуживания 
        # на основе default_watering_interval из каталога. это создает 
        # непрерывный цикл ухода без участия пользователя.
        
        # Используем .get() для получения актуального состояния задачи
        task = db.query(CareCalendar).get(task_id)
        if not task:
            return None, "Задача не найдена."

        # 1. отмечаем выполнение
        task.is_completed = True
        task.completion_date = datetime.now()
        
        # 2. обновляем статус растения
        plant = task.plant
        if task.task_type == "watering":
            plant.last_watered_at = datetime.now()
        
        # 3. планируем следующую задачу
        # берем интервал из каталога, связанного с растением
        catalog_item = db.query(PlantCatalog).get(plant.catalog_id)
        interval = catalog_item.default_watering_interval if catalog_item else 7
        
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
            
            # ВАЖНО: Обновляем объект растения из базы, чтобы Flet увидел новую дату полива
            db.refresh(plant) 
            
            return new_task, None 
        except Exception as e:
            db.rollback()
            return None, f"Ошибка при планировании: {str(e)}."

    @staticmethod
    def get_plant_schedule(db: Session, plant_id: int):
        # получение будущего графика для конкретного растения
        # используется фронтендом для отображения календаря в карточке растения
        return db.query(CareCalendar).filter(
            CareCalendar.plant_id == plant_id,
            CareCalendar.is_completed == False
        ).order_by(CareCalendar.scheduled_date).all()