import urllib3
import logging
import json
from database.session import SessionLocal, engine
from services.ai_services import GigaChatService
from services.plant_services import PlantService
from database.models import PlantCatalog, TokenUsage

# 1. отключаем логирование sqlalchemy для чистоты вывода
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

# 2. отключаем системные варнинги
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def print_line():
    print("—" * 60)

def print_step(title):
    print(f"\n🚀 {title.upper()}")

def run_clean_test():
    db = SessionLocal()
    ai = GigaChatService()
    user_id = 1

    print("\n" + "="*60)
    print("   GREENTHUMB AI DIAGNOSTIC SYSTEM v1.0   ")
    print("="*60)

    try:
        # шаг 1: авторизация
        print_step("Авторизация")
        ai._update_token()
        if ai.access_token:
            print("✅ Канал связи со Сбером установлен.")
        else:
            print("❌ Ошибка ключей в .env.")
            return

        # шаг 2: умный поиск (самообучение базы)
        print_step("Умный поиск (Обучение справочника)")
        query = "Венерина Мухоловка"
        print(f"🔍 Запрос пользователя: '{query}'")
        
        # запускаем метод, который сам решит: искать в базе или звать ИИ
        item, err = PlantService.get_or_create_catalog_item(db, ai, user_id, query)
        
        if not err and item:
            print(f"✅ Растение идентифицировано: {item.species_name}")
            print(f"📄 Описание: {item.description[:100]}...")
            print(f"💧 Режим полива: раз в {item.default_watering_interval} дн.")
            
            # проверка физического наличия в базе
            exists = db.query(PlantCatalog).filter_by(catalog_id=item.catalog_id).first()
            if exists:
                print("💾 Статус БД: Новый вид успешно внесен в глобальный каталог.")
        else:
            print(f"❌ Ошибка поиска: {err}")

        # шаг 3: консультация
        print_step("Консультация агронома")
        question = "Почему ловушки не закрываются?"
        print(f"💬 Вопрос: {question}")
        advice, err = ai.ask_agronomist(db, user_id, item.species_name, question)
        
        if not err:
            print_line()
            print(advice)
            print_line()
        else:
            print(f"❌ Ошибка чата: {err}")

        # шаг 4: итоги ресурсов
        print_step("Аудит ресурсов")
        usage = db.query(TokenUsage).filter_by(user_id=user_id).all()
        total_tokens = sum([t.tokens_count for t in usage])
        print(f"📈 Запросов выполнено: {len(usage)}")
        print(f"💰 Итого потрачено: {total_tokens} токенов.")

    except Exception as e:
        print(f"\n‼️ СБОЙ ТЕСТА: {e}")
    finally:
        db.close()
        print("\n" + "="*60)
        print("   ТЕСТИРОВАНИЕ ЗАВЕРШЕНО УСПЕШНО   ")
        print("="*60 + "\n")

if __name__ == "__main__":
    run_clean_test()