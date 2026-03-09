import urllib3
import logging
import os
import json
from database.session import SessionLocal, engine
from services.ai_services import GigaChatService
from services.plant_services import PlantService
from services.care_service import CareService
from database.models import Plant, PlantCatalog, CareCalendar, GrowthLog, TokenUsage

# отключение лишних логов для чистоты вывода
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def print_banner(text):
    print(f"\n{'#'*70}")
    print(f"### {text.upper()}")
    print(f"{'#'*70}")

def run_full_plant_test():
    db = SessionLocal()
    ai = GigaChatService()
    user_id = 1
    test_img_path = "test_callisia.jpg" 

    print_banner("запуск полного цикла тестирования растений")

    try:
        # 1. тест умного поиска и самообучения справочника
        print(f"\n[1] тест умного поиска: ищем редкое растение...")
        query = "Каллизия розовая"
        # метод должен найти в базе или создать через ии
        catalog_item, err = PlantService.get_or_create_catalog_item(db, ai, user_id, query)
        
        if err or not catalog_item:
            print(f"❌ сбой поиска: {err}")
            return
        print(f"✅ успех: вид '{catalog_item.species_name}' теперь в справочнике")

        # 2. тест подтверждения и создания растения пользователя
        print(f"\n[2] тест регистрации растения пользователем...")
        # имитируем данные которые пользователь мог подправить в интерфейсе
        verified_data = {
            "species_name": catalog_item.species_name,
            "latin_name": catalog_item.latin_name,
            "description": catalog_item.description,
            "watering_interval": 4, # пользователь решил поливать чаще
            "light_level": 0.8
        }
        
        # читаем фото для теста
        img_bytes = None
        if os.path.exists(test_img_path):
            with open(test_img_path, "rb") as f: img_bytes = f.read()

        my_plant, err = PlantService.confirm_and_create_plant(
            db, user_id, verified_data, "Моя розовая прелесть", img_bytes
        )
        
        if err or not my_plant:
            print(f"❌ сбой создания: {err}")
            return
        print(f"✅ растение создано. ID: {my_plant.plant_id}, фото: {my_plant.image_url}")

        # 3. тест автоматического календаря
        print(f"\n[3] проверка инициализации календаря...")
        tasks = db.query(CareCalendar).filter_by(plant_id=my_plant.plant_id).all()
        if tasks:
            print(f"✅ создано задач: {len(tasks)}. ближайшая: {tasks[0].scheduled_date}")
        else:
            print("❌ ошибка: календарь пуст")

        # 4. тест журнала роста (физические замеры)
        print(f"\n[4] тест добавления замера роста...")
        log_entry, err = PlantService.add_measurement(db, my_plant.plant_id, 12.5, "растет хорошо", img_bytes)
        if not err:
            print(f"✅ замер добавлен: {log_entry.height} см. статус растения обновлен")
        else:
            print(f"❌ сбой замера: {err}")

        # 5. тест цикла ухода: выполнение задачи
        print(f"\n[5] тест выполнения задачи и перепланирования...")
        first_task = tasks[0]
        new_task, err = CareService.complete_task(db, first_task.calendar_id)
        if not err:
            print(f"✅ полив отмечен. новая задача создана на: {new_task.scheduled_date}")
        else:
            print(f"❌ сбой цикла ухода: {err}")

        # 6. тест архивации
        print(f"\n[6] тест отправки растения в архив...")
        archived, err = PlantService.archive_plant(db, my_plant.plant_id, "отдал другу")
        if not err:
            # проверяем что активных задач больше нет
            future_tasks = db.query(CareCalendar).filter_by(plant_id=my_plant.plant_id, is_completed=False).count()
            print(f"✅ растение в архиве. активных задач осталось: {future_tasks}")
        else:
            print(f"❌ сбой архивации: {err}")

        # 7. тест полного удаления (очистка базы и диска)
        print(f"\n[7] тест безвозвратного удаления...")
        img_to_delete = my_plant.image_url
        success, err = PlantService.delete_plant_permanently(db, my_plant.plant_id)
        if success:
            # проверяем файл на диске
            full_path = os.path.join("assets", "uploads", img_to_delete)
            if not os.path.exists(full_path):
                print("✅ запись удалена из БД, файл стерт с диска")
            else:
                print("⚠️ запись удалена, но файл остался на диске")
        else:
            print(f"❌ сбой удаления: {err}")

    except Exception as e:
        print(f"‼️ критическая ошибка теста: {e}")
    finally:
        db.close()
        print_banner("тестирование всех модулей завершено")

if __name__ == "__main__":
    run_full_plant_test()