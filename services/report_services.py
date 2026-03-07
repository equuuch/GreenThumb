from sqlalchemy.orm import Session
from database.models import Plant, CareCalendar, GrowthLog

class ReportService:
    @staticmethod
    def collect_plant_data(db: Session, plant_id: int):
        # сбор данных для генератора pdf. 
        # исправлено обращение к связи catalog_info согласно модели.
        plant = db.query(Plant).get(plant_id)
        if not plant:
            return None

        logs = db.query(GrowthLog).filter(GrowthLog.plant_id == plant_id).order_by(GrowthLog.measured_at).all()
        start_h = float(logs[0].height) if logs else 0
        end_h = float(logs[-1].height) if logs else 0

        tasks = db.query(CareCalendar).filter(CareCalendar.plant_id == plant_id).all()
        completed = [t for t in tasks if t.is_completed]
        discipline = (len(completed) / len(tasks) * 100) if tasks else 0

        return {
            "name": plant.custom_name,
            "species": plant.catalog_info.species_name, # исправлено
            "latin": plant.catalog_info.latin_name,    # исправлено
            "added_at": plant.added_at.strftime("%d.%m.%Y"),
            "last_water": plant.last_watered_at.strftime("%d.%m.%Y") if plant.last_watered_at else "нет",
            "growth_data": {"start": start_h, "current": end_h, "delta": round(end_h - start_h, 2)},
            "care_data": {"total": len(tasks), "done": len(completed), "score": round(discipline, 1)},
            "history": logs 
        }