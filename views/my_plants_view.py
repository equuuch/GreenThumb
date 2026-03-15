import flet as ft # основной фреймворк для построения кроссплатформенного интерфейса
from database.session import get_db # импорт генератора сессий для взаимодействия с базой данных
from database.models import Plant # импорт описания структуры таблицы растений
from services.plant_services import PlantService # импорт бизнес-логики управления коллекцией
from sqlalchemy.orm import joinedload # инструмент для выполнения sql join запросов (жадная загрузка)
from datetime import datetime # библиотека для работы с системным временем и расчетами дат
import os # модуль для выполнения проверок существования файлов в операционной системе

def MyPlantsView(page: ft.Page, nav, user_state):
    """
    функция-конструктор экрана личной коллекции растений пользователя
    реализует логику отображения сетки объектов с автоматическим расчетом их текущего состояния
    """
    view = ft.View() # инициализация объекта экрана flet
    view.route = "/my_plants" # привязка уникального адреса маршрута для навигации
    view.bgcolor = "#F9F9F9" # установка фонового цвета вьюхи в светло-серый оттенок
    view.padding = 0 # обнуление стандартных внутренних отступов контейнера вьюхи

    # идентификация текущего пользователя системы из глобального словаря состояния
    user_id = user_state.get("id") or 1

    # 1. этап загрузки и первичной обработки данных из реляционной базы данных
    with next(get_db()) as db: # инициализация защищенного соединения с бд через контекстный менеджер
        db.expire_all() # принудительный сброс объектов в памяти для получения актуальных данных с диска
        my_plants = (
            db.query(Plant) # формирование sql-запроса к таблице plants
            # оптимизация производительности: подгружаем данные из справочника одним запросом через join
            .options(joinedload(Plant.catalog_info))
            # фильтрация данных: только растения текущего владельца и только те что не в архиве
            .filter(Plant.user_id == user_id, Plant.is_active == 1)
            .all() # преобразование сырого ответа базы в список объектов python
        )
        # технический вывод путей к файлам в консоль разработчика для аудита целостности данных
        for p in my_plants:
            print(f"DEBUG: {p.custom_name} | Path in DB: {p.image_url}")

    def get_status_color(val):
        """
        логический маппер для цветовой индикации параметров жизнедеятельности растения
        реализует визуальную схему светофора на основе нормализованного значения от нуля до единицы
        """
        # если значение параметра выше пятидесяти процентов окрашиваем в зеленый цвет бренда
        if val > 0.5: 
            return "#009753" 
        # если значение находится в диапазоне от двадцати до пятидесяти процентов используем желтый цвет
        if val >= 0.2: 
            return "#FFC107" 
        # для критических значений ниже двадцати процентов возвращаем красный цвет опасности
        return "#FF5252" 

    # 2. построение верхней панели управления (шапка экрана)
    header = ft.Container(
        padding=ft.padding.only(left=20, right=20, top=40, bottom=10), # настройка отступов с учетом системной зоны
        content=ft.Row([ # горизонтальное размещение элементов управления
            ft.IconButton(
                ft.Icons.ARROW_BACK_IOS_NEW, # иконка возврата в стиле ios
                icon_size=20, 
                icon_color="black", 
                on_click=lambda _: nav("/user_home") # обработчик нажатия: возврат на домашний экран
            ),
            ft.Text(
                "Мои растения", # текстовый заголовок страницы
                size=22, 
                weight="bold", 
                color="black", 
                expand=True, # разрешение тексту занимать всё свободное пространство в ряду
                text_align="center", # центрирование текста внутри расширенной области
                font_family="Montserrat" # использование фирменной гарнитуры шрифта
            ),
            ft.IconButton(
                ft.Icons.ADD, # кнопка быстрого перехода к функционалу добавления
                icon_size=24, 
                icon_color="black", 
                on_click=lambda _: nav("/scanner") # перенаправление пользователя к ии-сканеру
            ),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN) # равномерное распределение кнопок по краям
    )

    # 3. описание фабричного метода сборки визуальной карточки растения
    def create_plant_card(plant_obj):
        """
        внутренний программный модуль формирования интерактивного компонента карточки
        включает препроцессинг путей к файлам и математический расчет метрик ухода
        """
        # блок обработки графического контента
        if plant_obj.image_url:
            # нормализация строкового пути: удаление системных префиксов и коррекция слешей под движок flet
            img_path = plant_obj.image_url.replace("assets/", "").replace("\\", "/")
            
            # верификация физического наличия медиафайла на диске устройства для предотвращения падения ui
            full_path_on_disk = os.path.normpath(os.path.join("assets", img_path))
            if not os.path.exists(full_path_on_disk):
                print(f"❌ ОШИБКА: Файл не найден по пути: {full_path_on_disk}")
        else:
            # установка внешней ссылки на изображение-заглушку если фото в базе отсутствует
            img_path = "https://images.unsplash.com/photo-1453904300235-0f2f60b15b5d?q=80&w=300"
        
        cat = plant_obj.catalog_info # доступ к эталонным ботаническим данным из связанной таблицы
        water_val = 0.0 # инициализация базового значения уровня увлажненности

        # алгоритм расчета индекса влажности на основе времени последнего полива и констант справочника
        if plant_obj.last_watered_at and cat and cat.default_watering_interval:
            # вычисление разницы во времени между текущим моментом и последней операцией ухода в секундах
            diff_seconds = (datetime.now() - plant_obj.last_watered_at).total_seconds()
            # конвертация интервала полива из дней в секунды для сопоставления масштабов
            interval_seconds = cat.default_watering_interval * 24 * 3600
            
            # если прошло меньше минуты считаем растение максимально увлажненным
            if diff_seconds < 60:
                water_val = 1.0
            else:
                # линейный расчет высыхания субстрата с ограничением в диапазоне от нуля до единицы
                water_val = max(0.0, min(1.0, 1.0 - (diff_seconds / interval_seconds)))
        elif plant_obj.last_watered_at:
            # статическая установка значения если интервал в справочнике не определен
            water_val = 0.8
        
        # определение уровня освещенности: приоритетное использование личных настроек пользователя
        light_val = plant_obj.user_light_level if plant_obj.user_light_level is not None else (cat.default_light_level if cat else 0.5)
        # расчет интегрального показателя здоровья экземпляра на основе порога влажности в двадцать процентов
        health_val = 1.0 if water_val > 0.2 else 0.4

        # сборка визуального контейнера карточки с применением теней и скруглений
        return ft.Container(
            bgcolor="white", 
            border_radius=25, # задание радиуса скругления углов для современного дизайна
            shadow=ft.BoxShadow( # настройка мягкой тени для визуального отделения карточки от фона
                blur_radius=15, 
                color=ft.Colors.with_opacity(0.1, "black"),
                offset=ft.Offset(0, 5) # смещение тени вниз для создания эффекта глубины
            ),
            # реализация адаптивности: количество карточек в ряд зависит от разрешения экрана (breakpoints)
            col={"xs": 6, "sm": 6, "md": 3, "lg": 2}, 
            on_click=lambda _: nav(f"/my_plant_details/{plant_obj.plant_id}"), # переход в детальную карточку
            content=ft.Column(
                spacing=0,
                controls=[
                    # верхний сегмент карточки: контейнер с фотографией растения
                    ft.Container(
                        aspect_ratio=1.0, # принудительное сохранение квадратных пропорций превью
                        content=ft.Image(
                            src=img_path, 
                            fit=ft.ImageFit.COVER, # заполнение всей области контейнера без искажения пропорций
                            border_radius=ft.border_radius.only(top_left=25, top_right=25), # скругление только верха
                            error_content=ft.Icon(ft.Icons.IMAGE_NOT_SUPPORTED, color="grey300") # заглушка при ошибке
                        )
                    ),
                    # нижний сегмент карточки: блок информационных индикаторов и названия
                    ft.Container(
                        padding=ft.padding.only(left=15, right=15, top=12, bottom=15),
                        content=ft.Column(
                            spacing=8,
                            controls=[
                                ft.Text(
                                    plant_obj.custom_name, # вывод имени данного растению владельцем
                                    weight="bold", 
                                    size=15, 
                                    color="black", 
                                    max_lines=1, # ограничение длины текста одной строкой
                                    overflow=ft.TextOverflow.ELLIPSIS, # добавление многоточия при переполнении
                                    font_family="Montserrat"
                                ),
                                # строка индикаторов состояния с динамическим изменением цвета иконок
                                ft.Row([
                                    ft.Icon(ft.Icons.WATER_DROP, size=18, color=get_status_color(water_val)),
                                    ft.Icon(ft.Icons.WB_SUNNY, size=18, color=get_status_color(light_val)),
                                    ft.Icon(ft.Icons.FAVORITE, size=18, color=get_status_color(health_val)),
                                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                            ]
                        )
                    )
                ]
            )
        )

    # инициализация контейнера адаптивной сетки элементов на базе responsiverow
    grid = ft.ResponsiveRow(spacing=15, run_spacing=15)
    
    # реализация логики отображения пустого состояния (empty state) если коллекция пользователя пуста
    if not my_plants:
        grid.controls.append(
            ft.Container(
                content=ft.Column([
                    ft.Container(height=50),
                    ft.Icon(ft.Icons.SEARCH_OFF, size=80, color="grey300"),
                    ft.Text(
                        "У вас пока нет растений\nНажмите +, чтобы добавить первое!", 
                        text_align="center", size=16, color="grey500", font_family="Montserrat"
                    )
                ], horizontal_alignment="center"),
                col=12 # растягивание сообщения на всю ширину сетки
            )
        )
    else:
        # итеративное наполнение сетки сгенерированными объектами карточек
        for p in my_plants:
            grid.controls.append(create_plant_card(p))

    # итоговая компоновка всех элементов вьюхи в единый прокручиваемый список
    view.controls.append(
        ft.ListView(
            controls=[
                header, # закрепление шапки в верхней части списка
                ft.Container(padding=ft.padding.all(20), content=grid) # размещение сетки с боковыми отступами
            ], 
            expand=True # разрешение списку занимать всю высоту доступного вьюпорта
        )
    )
    
    return view # возврат полностью сформированного объекта вьюхи для рендеринга роутером