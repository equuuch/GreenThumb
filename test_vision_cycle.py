import urllib3
import logging
import os
from database.session import SessionLocal
from services.ai_services import GigaChatService
from services.plant_services import PlantService

# чистим консоль от мусора
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def run_vision_test():
    db = SessionLocal()
    ai = GigaChatService()
    user_id = 1
    image_path = "test_callisia.jpg"

    print("="*60)
    print("   GREENTHUMB VISION AI: ТЕСТ ИНТЕГРАЦИИ (CONFIRMATION FLOW)   ")
    print("="*60)

    if not os.path.exists(image_path):
        print(f"❌ Файл {image_path} не найден! Положи фото в папку проекта")
        return

    try:
        # 1. читаем фото
        with open(image_path, "rb") as f:
            img_bytes = f.read()

        # 2. распознавание вида через ии
        print("\n🧐 ШАГ 1: Анализ изображения...")
        plant_data, err = ai.identify_plant_photo(db, user_id, img_bytes)
        
        if err or not plant_data:
            print(f"❌ Ошибка распознавания: {err}")
            return

        print(f"✅ ИИ предложил вид: {plant_data.get('species_name')}")

        # 3. имитация подтверждения данных пользователем (Confirmation Step)
        # в реальном приложении здесь фронтенд покажет форму пользователю
        print("\n📝 ШАГ 2: Подтверждение данных и запись в базу...")
        
        # мы можем вручную подправить данные, если ии ошибся (как с каллизией)
        plant_data['species_name'] = "Каллизия ползучая" 
        
        my_plant, err = PlantService.confirm_and_create_plant(
            db, 
            user_id=user_id, 
            catalog_data=plant_data, 
            custom_name="Моя красавица на балконе",
            image_bytes=img_bytes
        )
        
        if not err and my_plant:
            print(f"🎉 Успех! Растение официально добавлено в систему")
            print(f"🆔 ID растения в базе: {my_plant.plant_id}")
            print(f"🧬 Вид в каталоге: {my_plant.catalog_info.species_name}")
            print(f"🖼 Путь к фото: assets/uploads/{my_plant.image_url}")
            
            # проверяем задачу в календаре
            from database.models import CareCalendar
            task = db.query(CareCalendar).filter_by(plant_id=my_plant.plant_id).first()
            if task:
                print(f"📅 Календарь: Запланирован {task.task_type} на {task.scheduled_date}")
        else:
            print(f"❌ Ошибка создания: {err}")

    except Exception as e:
        print(f"‼️ Сбой теста: {e}")
    finally:
        db.close()
        print("\n" + "="*60)

if __name__ == "__main__":
    run_vision_test()