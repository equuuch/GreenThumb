from sqlalchemy.orm import Session
from sqlalchemy import select, and_
from database.models import Plant, CareCalendar, GrowthLog

class ReportService:
    @staticmethod
    def collect_plant_data(db: Session, plant_id: int):
        # сбор всей доступной статистики по растению. 
        # метод агрегирует данные из трех разных таблиц: паспортные данные, 
        # история всех поливов и журнал замеров роста. 
        # на выходе формируется очищенный словарь, готовый для передачи в генератор pdf.
        
        plant = db.query(Plant).get(plant_id)
        if not plant:
            return None

        # 1. статистика роста
        logs = db.query(GrowthLog).filter(GrowthLog.plant_id == plant_id).order_by(GrowthLog.measured_at).all()
        start_h = logs[0].height if logs else 0
        end_h = logs[-1].height if logs else 0
        growth_total = end_h - start_h

        # 2. статистика ухода
        tasks = db.query(CareCalendar).filter(CareCalendar.plant_id == plant_id).all()
        completed = [t for t in tasks if t.is_completed]
        discipline = (len(completed) / len(tasks) * 100) if tasks else 0

        return {
            "name": plant.custom_name,
            "species": plant.catalog_item.species_name,
            "latin": plant.catalog_item.latin_name,
            "added_at": plant.added_at.strftime("%d.%m.%Y"),
            "last_water": plant.last_watered_at.strftime("%d.%m.%Y") if plant.last_watered_at else "нет",
            "growth_data": {
                "start": start_h,
                "current": end_h,
                "delta": round(growth_total, 2)
            },
            "care_data": {
                "total": len(tasks),
                "done": len(completed),
                "score": round(discipline, 1)
            },
            "history": logs # передаем объекты логов для таблицы
        }