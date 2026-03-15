import os
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime, date, timedelta

from config import Config
from database.models import Plant, PlantCatalog, PlantAlias, CareCalendar, GrowthLog
from .file_service import FileService

class PlantService:
    @staticmethod
    def get_catalog_item_by_name(db: Session, name: str):
        # проверка входящего текста на пустоту чтобы не тратить ресурсы сервера на бессмысленные поисковые запросы
        if not name:
            return None
            
        # первый этап поиска: проверяем таблицу синонимов и народных названий чтобы понять что именно имел в виду пользователь
        alias = db.query(PlantAlias).filter(PlantAlias.user_input == name.lower()).first()
        if alias:
            # если в таблице синонимов есть совпадение мы переходим к официальной карточке растения через его уникальный номер
            return db.query(PlantCatalog).filter(PlantCatalog.catalog_id == alias.catalog_id).first()
        
        # второй этап поиска: если синонима нет пытаемся найти растение по его точному биологическому названию в главном реестре
        return db.query(PlantCatalog).filter(PlantCatalog.species_name == name).first()

    @staticmethod
    def get_or_create_catalog_item(db: Session, ai_service, user_id: int, query: str):
        # оптимизация работы: сначала ищем растение в нашей локальной базе данных чтобы не платить за запросы к нейросети и не ждать ответа
        item = PlantService.get_catalog_item_by_name(db, query)
        if item:
            # если нашли растение на диске сразу отдаем его программе без участия искусственного интеллекта
            return item, None

        # если в нашей базе данных пусто вызываем нейросеть чтобы она расшифровала ввод пользователя и исправила ошибки в названии
        norm_data, err = ai_service.identify_by_name(db, user_id, query)
        if err or not norm_data or not norm_data.get('is_plant'):
            # строгая проверка на случай если пользователь ввел в поиск название предмета или просто случайный набор букв
            return None, "Растение не найдено в базе и не опознано ассистентом."

        # извлекаем исправленное и официальное название которое нам прислал искусственный интеллект
        standard_name = norm_data['standard_name']
        
        # проверяем базу данных еще раз по официальному имени так как под другим синонимом это растение уже могло быть в списке
        item = db.query(PlantCatalog).filter_by(species_name=standard_name).first()
        if item:
            # если под стандартным именем растение нашлось отдаем его и прекращаем процесс создания
            return item, None

        # этап генерации справочных данных: просим ии составить полноценный технический паспорт растения с графиком полива и описанием
        passport, err = ai_service.get_passport_data(db, user_id, standard_name)
        if err:
            # обработка случая если нейросеть временно недоступна или прислала данные в непонятном формате
            return None, f"Ошибка при получении данных от ИИ: {err}."

        try:
            # создаем новую постоянную запись в общем каталоге системы на основе проверенных данных от искусственного интеллекта
            new_catalog_item = PlantCatalog(
                species_name=passport.get('species_name', standard_name),
                latin_name=passport.get('latin_name', 'Unknown'),
                description=passport.get('description', ''),
                default_watering_interval=int(passport.get('watering_interval', 7)),
                default_light_level=float(passport.get('light_level', 0.5))
            )
            db.add(new_catalog_item)
            # применяем изменения в памяти базы данных чтобы получить автоматический номер id для новой записи растения
            db.flush() 

            # сохраняем исходный запрос пользователя в таблицу связей чтобы в следующий раз поиск по этому слову работал моментально
            new_alias = PlantAlias(user_input=query.lower(), catalog_id=new_catalog_item.catalog_id)
            db.add(new_alias)
            # подтверждаем создание связи между народным названием и официальной карточкой в каталоге
            db.flush()
            
            # отдаем полностью готовую и сохраненную запись справочника обратно в программу
            return new_catalog_item, None
            
        except Exception as e:
            # важный механизм защиты: если при записи произошла любая техническая ошибка мы отменяем всё чтобы не повредить базу
            db.rollback()
            return None, f"Ошибка при обновлении справочника: {str(e)}."

    @staticmethod
    def confirm_and_create_plant(db: Session, user_id: int, catalog_data: dict, custom_name: str = None, image_bytes: bytes = None, height: float = 10.0):
        # проверяем существует ли этот вид растения в нашем основном списке перед тем как прописать его в саду пользователя
        species_name = catalog_data.get('species_name')
        catalog_item = db.query(PlantCatalog).filter_by(species_name=species_name).first()
        
        # если пользователь добавляет редкий вид который мы еще не знали создаем для него новую эталонную запись в справочнике
        if not catalog_item:
            try:
                # формируем карточку вида с параметрами ухода по умолчанию чтобы другие люди тоже могли найти это растение
                catalog_item = PlantCatalog(
                    species_name=species_name,
                    latin_name=catalog_data.get('latin_name'),
                    description=catalog_data.get('description'),
                    default_watering_interval=int(catalog_data.get('watering_interval', 7)),
                    default_light_level=float(catalog_data.get('light_level', 0.5))
                )
                db.add(catalog_item)
                db.flush() # фиксируем новый вид в глобальном списке
            except Exception:
                # откат изменений если не удалось создать новый вид в справочнике
                db.rollback()
                return None, "Ошибка при создании нового вида в справочнике."

        # подготовка и сохранение фотографии растения на жесткий диск с оптимизацией веса через специальный файловый сервис
        image_url = FileService.process_and_save(image_bytes, subfolder="plants")

        # создаем основной программный объект который представляет цветок конкретного пользователя в его личном виртуальном саду
        new_plant = Plant(
            user_id=user_id,
            catalog_id=catalog_item.catalog_id,
            custom_name=custom_name or catalog_item.species_name,
            image_url=image_url,
            last_watered_at=datetime.now(), # фиксируем время добавления как время последнего полива для старта отсчета
            user_light_level=catalog_data.get('light_level', 0.5),
            status_text=f"Рост: {height} см",
            is_active=True
        )
        
        try:
            # добавляем запись о растении в сессию и готовимся создать связанные с ним данные в других таблицах
            db.add(new_plant)
            db.flush() 

            # автоматическая фиксация самого первого замера роста в истории развития для будущего построения графиков прогресса
            new_log = GrowthLog(
                plant_id=new_plant.plant_id, 
                height=height, 
                note="Первоначальная посадка",
                measured_at=date.today()
            )
            db.add(new_log)

            # создание первой записи в календаре: система автоматически ставит полив на сегодня чтобы пользователь сразу начал уход
            db.add(CareCalendar(
                plant_id=new_plant.plant_id, 
                task_type="watering", 
                scheduled_date=date.today(),
                is_completed=False
            ))
            
            # финальное сохранение всей цепочки данных одной операцией чтобы гарантировать целостность личного сада пользователя
            db.commit() 
            db.refresh(new_plant) # подгружаем из базы все созданные системой данные включая автоматические номера
            
            return new_plant, None
        except Exception as e:
            # полная очистка базы данных от всех следов текущей попытки создания растения если на любом этапе произошел сбой
            db.rollback()
            return None, f"Ошибка при добавлении растения: {str(e)}."

    @staticmethod
    def add_measurement(db: Session, plant_id: int, height: float, note: str = "", image_bytes: bytes = None):
        # обработка и сохранение снимка замера роста в отдельную папку для журналов истории чтобы не путать их с главными фото
        image_path = FileService.process_and_save(image_bytes, subfolder="logs")
        
        # создание новой строчки в хронике развития растения для отслеживания динамики роста в сантиметрах
        new_log = GrowthLog(plant_id=plant_id, height=height, note=note, image_path=image_path)
        try:
            db.add(new_log)
            # обновление текущего текстового статуса в главной таблице растений для мгновенного отображения новой высоты в списке
            plant = db.query(Plant).get(plant_id)
            if plant:
                plant.status_text = f"Рост: {height} см"
            
            # сохранение изменений в истории и статусе растения в рамках одной транзакции
            db.commit()
            db.refresh(new_log)
            return new_log, None
        except Exception as e:
            # отмена записи лога если возникли проблемы с доступом к файлу базы данных
            db.rollback()
            return None, f"Ошибка сохранения данных прогресса: {str(e)}."

    @staticmethod
    def archive_plant(db: Session, plant_id: int, reason: str = "убрано"):
        # извлечение данных о растении из базы перед тем как изменить его логический статус
        plant = db.query(Plant).get(plant_id)
        if not plant: return None, "Растение не найдено."

        try:
            # логическое удаление: мы не стираем данные из базы а просто помечаем растение как неактивное для сохранения истории
            plant.is_active = False
            plant.status_text = f"В архиве ({reason})"
            
            # принудительная очистка календаря от всех запланированных в будущем задач которые пользователь уже не будет выполнять
            db.query(CareCalendar).filter(
                CareCalendar.plant_id == plant_id, 
                CareCalendar.is_completed == False
            ).delete()
            
            # сохранение обновленного статуса растения и очищенного календаря
            db.commit()
            return plant, None
        except Exception as e:
            # откат операции архивации при системном сбое
            db.rollback()
            return None, f"Ошибка при архивации: {str(e)}."

    @staticmethod
    def get_user_plants(db: Session, user_id: int):
        # формирование списка всех активных растений которыми в данный момент владеет конкретный человек
        return db.query(Plant).filter(Plant.user_id == user_id, Plant.is_active == True).all()

    @staticmethod
    def get_archived_plants(db: Session, user_id: int):
        # выборка только тех растений которые были перенесены в архив для просмотра истории прошлых посадок
        return db.query(Plant).filter(Plant.user_id == user_id, Plant.is_active == False).all()

    @staticmethod
    def delete_plant_permanently(db: Session, plant_id: int):
        # поиск объекта в базе вместе с путем к его фотографии перед полным физическим уничтожением
        plant = db.query(Plant).get(plant_id)
        if not plant: return False, "Растение не найдено."

        image_path = plant.image_url
        try:
            # полное удаление записи из базы: связанные задачи и логи исчезнут автоматически благодаря настройке cascade в моделях
            db.delete(plant)
            db.commit()
            
            # очистка физической памяти: находим файл фотографии на диске и стираем его чтобы не занимать место впустую
            if image_path:
                full_path = os.path.join(Config.UPLOAD_DIR, image_path)
                if os.path.exists(full_path):
                    os.remove(full_path)
            
            # подтверждение того что все данные стерты и место на диске освобождено
            return True, None
        except Exception as e:
            # отмена удаления из базы если не удалось завершить процесс очистки
            db.rollback()
            return False, f"Ошибка при полном удалении: {str(e)}."