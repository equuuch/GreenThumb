from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, and_, delete
from datetime import datetime, date, timedelta
from database.models import Plant, CareCalendar, PlantCatalog

class CareService:
    @staticmethod
    def get_today_tasks(db: Session, user_id: int):
        """
        Получает список невыполненных задач на сегодня и просроченные 
        только для активных растений.
        """
        today = date.today()
        query = (
            select(CareCalendar)
            .options(joinedload(CareCalendar.plant))
            .join(Plant)
            .where(
                and_(
                    Plant.user_id == user_id,
                    Plant.is_active == True,
                    CareCalendar.is_completed == False,
                    CareCalendar.scheduled_date <= today
                )
            )
            .order_by(CareCalendar.scheduled_date)
        )
        return db.scalars(query).all()

    @staticmethod
    def generate_full_schedule(db: Session, plant_id: int, days_ahead: int = 30):
        """
        Создает сетку задач на месяц вперед. 
        Старые невыполненные задачи удаляются, чтобы график всегда был актуальным.
        """
        plant = db.get(Plant, plant_id)
        if not plant or not plant.is_active:
            return

        # 1. Очищаем будущие задачи, чтобы перестроить график
        db.execute(
            delete(CareCalendar).where(
                and_(
                    CareCalendar.plant_id == plant_id,
                    CareCalendar.is_completed == False
                )
            )
        )

        # 2. Получаем интервал из каталога
        catalog_item = db.get(PlantCatalog, plant.catalog_id)
        interval = (catalog_item.default_watering_interval 
                   if (catalog_item and catalog_item.default_watering_interval) 
                   else 7)
        
        # 3. Точка отсчета: последний полив или сегодня
        last_date = plant.last_watered_at.date() if plant.last_watered_at else date.today()
        
        # 4. Генерируем задачи циклами
        current_date = last_date + timedelta(days=interval)
        end_date = date.today() + timedelta(days=days_ahead)

        new_tasks = []
        while current_date <= end_date:
            new_tasks.append(
                CareCalendar(
                    plant_id=plant_id,
                    task_type="watering",
                    scheduled_date=current_date,
                    is_completed=False
                )
            )
            current_date += timedelta(days=interval)
        
        if new_tasks:
            db.add_all(new_tasks)
        
        db.commit()

    @staticmethod
    def complete_task(db: Session, task_id: int):
        """
        Помечает конкретную задачу как выполненную и ПЕРЕСЧИТЫВАЕТ весь график,
        так как дата реального полива могла сдвинуть будущие циклы.
        """
        task = db.get(
            CareCalendar, 
            task_id, 
            options=[joinedload(CareCalendar.plant)]
        )
        
        if not task:
            return None, "Задача не найдена."

        try:
            # 1. Завершаем текущую задачу
            task.is_completed = True
            task.completion_date = datetime.now()
            
            # 2. Обновляем статус растения (точка отсчета для новых задач)
            if task.task_type == "watering":
                task.plant.last_watered_at = datetime.now()
            
            db.commit() # Сохраняем завершение
            
            # 3. Перестраиваем календарь на 30 дней вперед от новой даты
            CareService.generate_full_schedule(db, task.plant_id, days_ahead=30)
            
            return task, None
            
        except Exception as e:
            db.rollback()
            return None, f"Ошибка при сохранении: {str(e)}"

    @staticmethod
    def get_plant_schedule(db: Session, plant_id: int):
        """
        Возвращает весь будущий график для конкретного растения 
        (для отображения в карточке растения).
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