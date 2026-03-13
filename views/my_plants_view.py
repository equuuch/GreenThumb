import flet as ft
from database.session import get_db
from database.models import Plant
from services.plant_services import PlantService
from sqlalchemy.orm import joinedload
from datetime import datetime
import os

def MyPlantsView(page: ft.Page, nav, user_state):
    """
    модуль визуализации персональной коллекции растений пользователя.
    реализует логику отображения сетки объектов с динамическим расчетом статусов ухода.
    """
    view = ft.View()
    view.route = "/my_plants"
    view.bgcolor = "#F9F9F9"
    view.padding = 0 

    # идентификация текущего пользователя для фильтрации данных в sql-запросе.
    user_id = user_state.get("id") or 1

    # 1. блок синхронизации данных с базой данных.
    with next(get_db()) as db:
        # принудительный сброс локального кэша сессии для получения актуального состояния из бд.
        db.expire_all()
        my_plants = (
            db.query(Plant)
            # оптимизация производительности: загрузка связанных данных каталога через join за один запрос.
            .options(joinedload(Plant.catalog_info))
            .filter(Plant.user_id == user_id, Plant.is_active == 1)
            .all()
        )
        # технический аудит путей к медиафайлам в консоль разработчика.
        for p in my_plants:
            print(f"DEBUG: {p.custom_name} | Path in DB: {p.image_url}")

    def get_status_color(val):
        """
        логический маппер для цветовой индикации состояния параметров (вода/свет/здоровье).
        реализует классическую схему светофора на основе нормализованного значения [0..1].
        """
        if val > 0.5: 
            return "#009753"  # зеленый: состояние в норме.
        if val >= 0.2: 
            return "#FFC107"  # желтый: требуется внимание пользователя.
        return "#FF5252"      # красный: критический уровень.

    # 2. построение верхней панели навигации и управления.
    header = ft.Container(
        padding=ft.padding.only(left=20, right=20, top=40, bottom=10),
        content=ft.Row([
            ft.IconButton(
                ft.Icons.ARROW_BACK_IOS_NEW, 
                icon_size=20, 
                icon_color="black", 
                on_click=lambda _: nav("/user_home")
            ),
            ft.Text(
                "Мои растения", 
                size=22, 
                weight="bold", 
                color="black", 
                expand=True, 
                text_align="center", 
                font_family="Montserrat"
            ),
            ft.IconButton(
                ft.Icons.ADD, 
                icon_size=24, 
                icon_color="black", 
                on_click=lambda _: nav("/scanner")
            ),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
    )

    # 3. описание фабричного метода создания карточки растения.
    def create_plant_card(plant_obj):
        """
        модуль формирования интерактивного компонента карточки.
        включает препроцессинг путей и расчет метрик жизнедеятельности.
        """
        if plant_obj.image_url:
            # нормализация пути: удаление системного префикса и коррекция слешей для кроссплатформенности.
            img_path = plant_obj.image_url.replace("assets/", "").replace("\\", "/")
            
            # верификация физического наличия файла на диске перед попыткой рендеринга.
            full_path_on_disk = os.path.normpath(os.path.join("assets", img_path))
            if not os.path.exists(full_path_on_disk):
                print(f"❌ ОШИБКА: Файл не найден по пути: {full_path_on_disk}")
        else:
            # использование внешнего url-заглушки при отсутствии локального изображения.
            img_path = "https://images.unsplash.com/photo-1453904300235-0f2f60b15b5d?q=80&w=300"
        
        cat = plant_obj.catalog_info
        water_val = 0.0

        # расчет индекса влажности на основе даты последнего полива и интервала из справочника.
        if plant_obj.last_watered_at and cat and cat.default_watering_interval:
            diff_seconds = (datetime.now() - plant_obj.last_watered_at).total_seconds()
            interval_seconds = cat.default_watering_interval * 24 * 3600
            
            if diff_seconds < 60:
                water_val = 1.0 # состояние полной увлажненности сразу после действия.
            else:
                # линейная аппроксимация высыхания субстрата.
                water_val = max(0.0, min(1.0, 1.0 - (diff_seconds / interval_seconds)))
        elif plant_obj.last_watered_at:
            water_val = 0.8
        
        # определение уровня освещенности: кастомное значение пользователя имеет приоритет над эталонным.
        light_val = plant_obj.user_light_level if plant_obj.user_light_level is not None else (cat.default_light_level if cat else 0.5)
        
        # расчет интегрального показателя здоровья на основе порога влажности.
        health_val = 1.0 if water_val > 0.2 else 0.4

        # сборка визуального контейнера с применением теней и скруглений.
        return ft.Container(
            bgcolor="white", 
            border_radius=25,
            shadow=ft.BoxShadow(
                blur_radius=15, 
                color=ft.Colors.with_opacity(0.1, "black"),
                offset=ft.Offset(0, 5)
            ),
            # настройка адаптивности: количество колонок меняется в зависимости от ширины вьюпорта (breakpoints).
            col={"xs": 6, "sm": 6, "md": 3, "lg": 2}, 
            on_click=lambda _: nav(f"/my_plant_details/{plant_obj.plant_id}"),
            content=ft.Column(
                spacing=0,
                controls=[
                    # верхняя часть карточки: визуальный контент.
                    ft.Container(
                        aspect_ratio=1.0, # сохранение квадратных пропорций для симметрии сетки.
                        content=ft.Image(
                            src=img_path, 
                            fit=ft.ImageFit.COVER, 
                            border_radius=ft.border_radius.only(top_left=25, top_right=25),
                            error_content=ft.Icon(ft.Icons.IMAGE_NOT_SUPPORTED, color="grey300")
                        )
                    ),
                    # нижняя часть карточки: информационные индикаторы.
                    ft.Container(
                        padding=ft.padding.only(left=15, right=15, top=12, bottom=15),
                        content=ft.Column(
                            spacing=8,
                            controls=[
                                ft.Text(
                                    plant_obj.custom_name, 
                                    weight="bold", 
                                    size=15, 
                                    color="black", 
                                    max_lines=1, 
                                    overflow=ft.TextOverflow.ELLIPSIS,
                                    font_family="Montserrat"
                                ),
                                # строка статусных иконок с динамической сменой цвета.
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

    # инициализация адаптивной сетки на базе responsiverow.
    grid = ft.ResponsiveRow(spacing=15, run_spacing=15)
    
    # реализация логики отображения пустого состояния (empty state) при отсутствии данных в коллекции.
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
                col=12
            )
        )
    else:
        # наполнение сетки сгенерированными карточками.
        for p in my_plants:
            grid.controls.append(create_plant_card(p))

    # итоговая компоновка вьюхи в единый вертикальный список со скроллом.
    view.controls.append(
        ft.ListView(
            controls=[
                header, 
                ft.Container(padding=ft.padding.all(20), content=grid)
            ], 
            expand=True
        )
    )
    
    return view