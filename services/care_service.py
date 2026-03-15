from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, and_, delete
from datetime import datetime, date, timedelta
from database.models import Plant, CareCalendar, PlantCatalog

class CareService:
    """сервисный слой инкапсулирующий математическую и бизнес-логику управления жизненным циклом ухода за растениями"""

    @staticmethod
    def get_today_tasks(db: Session, user_id: int):
        """алгоритм выборки актуальных и просроченных задач из базы данных sqlite для формирования оперативного списка дел пользователя"""
        today = date.today()
        # построение запроса кdal через sqlalchemy select с применением фильтрации по статусу активности и дате
        query = (
            select(CareCalendar)
            # реализация стратегии жадной загрузки joinedload для оптимизации n+1 запросов и мгновенного доступа к атрибутам связанной модели plant
            .options(joinedload(CareCalendar.plant))
            .join(Plant)
            # комплексная фильтрация: исключение архивных растений и выборка только невыполненных задач с наступившим сроком исполнения
            .where(
                and_(
                    Plant.user_id == user_id,
                    Plant.is_active == True,
                    CareCalendar.is_completed == False,
                    CareCalendar.scheduled_date <= today
                )
            )
            # применение хронологической сортировки для обеспечения правильной последовательности отображения задач в интерфейсе
            .order_by(CareCalendar.scheduled_date)
        )
        return db.scalars(query).all()

    @staticmethod
    def generate_full_schedule(db: Session, plant_id: int, days_ahead: int = 30):
        """метод программной генерации циклической сетки задач на заданный горизонт планирования на основе ботанических констант"""
        plant = db.get(Plant, plant_id)
        # валидация состояния объекта: автоматическое планирование прекращается если растение переведено пользователем в архив
        if not plant or not plant.is_active:
            return

        # 1. блок управления консистентностью: деструктивное удаление будущих неактуальных задач для предотвращения наслоения графиков при пересчете
        db.execute(
            delete(CareCalendar).where(
                and_(
                    CareCalendar.plant_id == plant_id,
                    CareCalendar.is_completed == False
                )
            )
        )

        # 2. получение параметров интервальности: извлечение агротехнических данных из глобального каталога справочника
        catalog_item = db.get(PlantCatalog, plant.catalog_id)
        # установка динамического шага планирования с использованием безопасного значения по умолчанию при отсутствии данных в справочнике
        interval = (catalog_item.default_watering_interval 
                   if (catalog_item and catalog_item.default_watering_interval) 
                   else 7)
        
        # 3. вычисление точки отсчета: алгоритм определяет дату последнего полива из профиля растения или берет текущую системную дату
        last_date = plant.last_watered_at.date() if plant.last_watered_at else date.today()
        
        # 4. итеративный процесс генерации: циклическое создание объектов календаря до достижения границы в тридцать календарных дней
        current_date = last_date + timedelta(days=interval)
        end_date = date.today() + timedelta(days=days_ahead)

        new_tasks = []
        while current_date <= end_date:
            # инстанцирование новых записей care_calendar с привязкой к идентификатору конкретного экземпляра растения
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
            # пакетная вставка сгенерированного набора данных в одну транзакцию для обеспечения атомарности операции
            db.add_all(new_tasks)
        
        db.commit() # фиксация изменений и сохранение сформированного графика ухода в постоянное хранилище

    @staticmethod
    def complete_task(db: Session, task_id: int):
        """процедура фиксации факта ухода за растением и инициация реактивного обновления всей будущей сетки расписания"""
        # загрузка объекта задачи вместе с метаданными растения через механизм joinedload для последующего обновления статуса здоровья
        task = db.get(
            CareCalendar, 
            task_id, 
            options=[joinedload(CareCalendar.plant)]
        )
        
        if not task:
            return None, "задача не найдена"

        try:
            # 1. перевод задачи в финальный статус: сохранение метки времени фактического выполнения процедуры
            task.is_completed = True
            task.completion_date = datetime.now()
            
            # 2. обновление состояния родительского объекта: синхронизация даты последнего полива для корректной работы ии-ассистента
            if task.task_type == "watering":
                task.plant.last_watered_at = datetime.now()
            
            db.commit() # сохранение факта выполнения текущего этапа ухода
            
            # 3. триггер реактивности: вызов полной перегенерации расписания от текущего момента для адаптации графика под реальные действия пользователя
            CareService.generate_full_schedule(db, task.plant_id, days_ahead=30)
            
            return task, None
            
        except Exception as e:
            # реализация механизма отката транзакции (rollback) при возникновении исключений для сохранения целостности реляционных связей
            db.rollback()
            return None, f"ошибка при сохранении данных: {str(e)}"

    @staticmethod
    def get_plant_schedule(db: Session, plant_id: int):
        """метод агрегации будущих плановых работ для визуализации индивидуального графика в интерфейсе карточки растения"""
        query = (
            select(CareCalendar)
            # формирование упорядоченной выборки только актуальных невыполненных задач по конкретному идентификатору растения
            .where(
                and_(
                    CareCalendar.plant_id == plant_id,
                    CareCalendar.is_completed == False
                )
            )
            .order_by(CareCalendar.scheduled_date)
        )
        return db.scalars(query).all()