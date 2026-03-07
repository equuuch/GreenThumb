import os
import urllib3
from database.session import SessionLocal, init_db
from services.auth_service import AuthService, AuthError
from services.ai_services import GigaChatService
from services.plant_services import PlantService
from services.care_service import CareService
from services.report_services import ReportService
from services.export_services import ExportService
from database.models import PlantCatalog, PlantAlias, CareCalendar

# отключаем предупреждения о небезопасном соединении (сбер скотина)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def run_tests():
    # 1. инициализация инфраструктуры
    print("--- старт тестирования бэкенда ---")
    init_db()
    db = SessionLocal()
    ai = GigaChatService()
    
    # 2. тест регистрации и входа
    print("\n[1] тест auth_service...")
    try:
        user = AuthService.register_user(db, "test@test.ru", "password123", "Иван")
        print(f"пользователь создан: {user.email}")
    except AuthError as e:
        print(f"инфо: {e.message}")
    
    user = AuthService.authenticate_user(db, "test@test.ru", "password123")
    if user:
        print("авторизация успешна.")
    else:
        print("Ошибка авторизации.")
        return

    # 3. тест каталога (поиск монстеры по алиасу)
    print("\n[2] тест поиска в каталоге...")
    item = PlantService.get_catalog_item_by_name(db, "монстера")
    if item:
        print(f"найдено в каталоге: {item.species_name} (id: {item.catalog_id})")
    else:
        print("Растение не найдено. Проверьте запуск seed.py.")

    # 4. тест ии (генерация паспорта для нового вида)
    print("\n[3] тест giga_chat_service (текстовый паспорт)...")
    passport, err = ai.get_passport_data(db, user.user_id, "Кактус Опунция")
    if not err:
        print(f"ии сгенерировал паспорт: {passport['species_name']}")
        print(f"совет по поливу: {passport['watering_interval']} дней")
    else:
        print(f"Ошибка ии: {err}")

    # 5. тест создания растения и автоматического календаря
    print("\n[4] тест plant_service + care_service...")
    if item:
        new_plant = PlantService.create_user_plant(
            db, user.user_id, item.catalog_id, custom_name="Мой любимый монстрик"
        )
        print(f"растение добавлено пользователю. id: {new_plant.plant_id}")
        
        # проверяем наличие задач в календаре (любых будущих)
        # мы ищем все задачи для этого конкретного растения
        plant_tasks = db.query(CareCalendar).filter(CareCalendar.plant_id == new_plant.plant_id).all()
        
        if plant_tasks:
            print(f"авто-календарь работает. создано задач: {len(plant_tasks)}")
            for t in plant_tasks:
                print(f" - запланировано: {t.task_type} на {t.scheduled_date}")
        else:
            print("Ошибка: задачи в календаре не созданы.")

    # 6. тест генерации pdf отчета
    print("\n[5] тест генерации отчета...")
    if item and new_plant:
        # сбор нормализованных данных через report_service
        data = ReportService.collect_plant_data(db, new_plant.plant_id)
        if data:
            # создание физического файла через export_service
            pdf_path = ExportService.create_plant_pdf(data)
            if pdf_path and os.path.exists(pdf_path):
                print(f"pdf отчет успешно создан: {pdf_path}")
            else:
                print("Ошибка генерации pdf. Проверьте наличие шрифтов.")
        else:
            print("Ошибка сбора данных для отчета.")

    db.close()
    print("\n--- тестирование завершено ---")

if __name__ == "__main__":
    run_tests()