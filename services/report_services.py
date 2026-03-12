from sqlalchemy.orm import Session
from database.models import Plant, CareCalendar, GrowthLog
from datetime import datetime

class ReportService:
    @staticmethod
    def collect_plant_data(db: Session, plant_id: int):
        plant = db.query(Plant).get(plant_id)
        if not plant:
            return None

        # Собираем логи роста
        logs = db.query(GrowthLog).filter(GrowthLog.plant_id == plant_id).order_by(GrowthLog.measured_at).all()
        
        start_h = float(logs[0].height) if logs else 0
        current_h = float(logs[-1].height) if logs else 0
        growth_delta = current_h - start_h if logs else 0

        # Считаем дисциплину ухода (за все время)
        tasks = db.query(CareCalendar).filter(CareCalendar.plant_id == plant_id).all()
        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t.is_completed])
        discipline_score = int((completed_tasks / total_tasks * 100)) if total_tasks > 0 else 100

        # Формируем авто-рекомендацию
        advice = "Растение развивается стабильно."
        if discipline_score < 70:
            advice = "Внимательнее соблюдайте график полива для лучшего роста."
        if growth_delta <= 0 and len(logs) > 1:
            advice = "Рост замедлился. Возможно, стоит обновить грунт или добавить удобрения."

        return {
            "name": plant.custom_name,
            "species": plant.catalog_info.species_name if plant.catalog_info else "Не определено",
            "latin": plant.catalog_info.latin_name if plant.catalog_info else "-",
            "added_at": plant.added_at.strftime("%d.%m.%Y"),
            "current_height": f"{current_h} см",
            "growth_delta": f"+{growth_delta} см" if growth_delta > 0 else f"{growth_delta} см",
            "discipline_score": f"{discipline_score}%",
            "total_tasks": total_tasks,
            "advice": advice,
            "report_date": datetime.now().strftime("%d.%m.%Y %H:%M")
        }