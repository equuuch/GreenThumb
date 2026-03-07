import urllib3
import logging
import os
from database.session import SessionLocal
from services.ai_services import GigaChatService
from services.plant_services import PlantService
from database.models import Plant, PlantCatalog

# чистим консоль от мусора
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def run_vision_test():
    db = SessionLocal()
    ai = GigaChatService()
    user_id = 1
    image_path = "test_callisia.jpg"

    print("="*60)
    print("   GREENTHUMB VISION AI: ТЕСТ РАСПОЗНАВАНИЯ   ")
    print("="*60)

    if not os.path.exists(image_path):
        print(f"❌ Файл {image_path} не найден! Положи фото в папку проекта.")
        return

    try:
        # 1. читаем фото в байты
        with open(image_path, "rb") as f:
            img_bytes = f.read()

        # 2. распознавание вида через ИИ (модель MAX)
        print("\n🧐 Анализируем изображение...")
        plant_data, err = ai.identify_plant_photo(db, user_id, img_bytes)
        
        if err or not plant_data:
            print(f"❌ Ошибка распознавания: {err}")
            return

        species_name = plant_data.get('species_name')
        print(f"✅ ИИ определил растение как: {species_name}")

        # 3. добавляем в справочник и создаем паспорт, если его еще нет
        print("\n📖 Проверяем справочник и создаем паспорт...")
        catalog_item, err = PlantService.get_or_create_catalog_item(db, ai, user_id, species_name)
        
        if not err and catalog_item:
            print(f"✅ Вид '{catalog_item.species_name}' готов в базе.")
            
            # 4. добавляем растение в ЛИЧНУЮ коллекцию пользователя
            print("\n🪴 Добавляем экземпляр в твой личный сад...")
            my_plant = PlantService.create_user_plant(
                db, 
                user_id=user_id, 
                catalog_id=catalog_item.catalog_id, 
                custom_name="Моя Каллизия на балконе",
                image_bytes=img_bytes # сохраняем и оригинал фото
            )
            
            if my_plant:
                print(f"🎉 Успех! Растение добавлено.")
                print(f"🆔 ID в твоем саду: {my_plant.plant_id}")
                print(f"🖼 Путь к фото: assets/uploads/{my_plant.image_url}")
                print(f"📅 Следующий полив: автоматически запланирован.")
        else:
            print(f"❌ Ошибка на этапе каталога: {err}")

    except Exception as e:
        print(f"‼️ Сбой теста: {e}")
    finally:
        db.close()
        print("\n" + "="*60)

if __name__ == "__main__":
    run_vision_test()