from sqlalchemy.orm import Session
from database.models import Plant, CareCalendar, GrowthLog
from datetime import datetime

class ReportService:
    @staticmethod
    def collect_plant_data(db: Session, plant_id: int):
        # основной алгоритм агрегации статистики, который собирает информацию из разных таблиц базы данных для формирования сводного отчета
        plant = db.query(Plant).get(plant_id)
        # проверка наличия записи в базе: если растение не найдено, процесс аналитики прерывается для предотвращения ошибок расчетов
        if not plant:
            return None

        # этап сбора данных о физическом развитии: извлекаем все записи из журнала роста, отсортированные по времени их фиксации
        logs = db.query(GrowthLog).filter(GrowthLog.plant_id == plant_id).order_by(GrowthLog.measured_at).all()
        
        # математический расчет прогресса: мы берем самый первый замер и сравниваем его с последним, чтобы понять чистую разницу в росте
        start_h = float(logs[0].height) if logs else 0
        current_h = float(logs[-1].height) if logs else 0
        growth_delta = current_h - start_h if logs else 0

        # этап анализа ответственности пользователя: загружаем все задачи из календаря ухода, которые были запланированы для этого растения
        tasks = db.query(CareCalendar).filter(CareCalendar.plant_id == plant_id).all()
        # вычисление индекса дисциплины: считаем процент выполненных задач от общего количества, чтобы оценить качество заботы о растении
        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t.is_completed])
        discipline_score = int((completed_tasks / total_tasks * 100)) if total_tasks > 0 else 100

        # логический блок автоматических выводов: программа анализирует цифры и выбирает подходящую текстовую подсказку для владельца
        advice = "Растение развивается стабильно."
        # если уровень выполнения задач ниже нормы, система выдает предупреждение о необходимости соблюдения графика
        if discipline_score < 70:
            advice = "Внимательнее соблюдайте график полива для лучшего роста."
        # если замеры показывают отсутствие роста при наличии нескольких записей, программа сигнализирует о возможной проблеме с почвой
        if growth_delta <= 0 and len(logs) > 1:
            advice = "Рост замедлился. Возможно, стоит обновить грунт или добавить удобрения."

        # итоговая сборка всех вычисленных параметров в единый структурированный словарь, который будет передан в сервис печати pdf
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