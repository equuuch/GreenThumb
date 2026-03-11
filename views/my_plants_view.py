import flet as ft
from database.session import get_db
from database.models import Plant
from services.plant_services import PlantService
from sqlalchemy.orm import joinedload
from datetime import datetime

def MyPlantsView(page: ft.Page, nav, user_state):
    view = ft.View()
    view.route = "/my_plants"
    view.bgcolor = "#F9F9F9"
    view.padding = 0 

    user_id = user_state.get("id") or 1

    # 1. ЗАГРУЗКА ДАННЫХ С ЖАДНОЙ ЗАГРУЗКОЙ (Eager Loading)
    with next(get_db()) as db:
        my_plants = (
            db.query(Plant)
            .options(joinedload(Plant.catalog_info))
            .filter(Plant.user_id == user_id, Plant.is_active == 1)
            .all()
        )

    # Вспомогательная функция для выбора цвета индикаторов
    def get_status_color(val):
        if val > 0.6: return "#009753"  # Зеленый
        if val > 0.3: return "#FFC107"  # Желтый
        return "#FF5252"               # Красный

    # 2. ШАПКА ЭКРАНА
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

    # 3. ФУНКЦИЯ КАРТОЧКИ
    def create_plant_card(plant_obj):
        # ИСПРАВЛЕНИЕ ПУТИ:
        # В AddPlantView мы сохраняем как "/plants/filename.jpg"
        # Flet ищет в папке assets. Убираем ведущий слэш, чтобы получилось "plants/filename.jpg"
        if plant_obj.image_url:
            img_path = plant_obj.image_url.lstrip("/") 
        else:
            img_path = "https://images.unsplash.com/photo-1453904300235-0f2f60b15b5d?q=80&w=300"
        
        # Теперь catalog_info доступен благодаря joinedload
        cat = plant_obj.catalog_info

        # РАСЧЕТ ПАРАМЕТРОВ
        # Влага
        water_val = 0.5
        if plant_obj.last_watered_at and cat and cat.default_watering_interval:
            days_since = (datetime.now() - plant_obj.last_watered_at).days
            water_val = max(0.0, min(1.0, 1.0 - (days_since / cat.default_watering_interval)))
        
        # Свет
        light_val = cat.default_light_level if cat else 0.5
        
        # Здоровье (базируется на влаге)
        health_val = 1.0 if water_val > 0.2 else 0.4

        return ft.Container(
            bgcolor="white", 
            border_radius=25,
            shadow=ft.BoxShadow(
                blur_radius=15, 
                color=ft.Colors.with_opacity(0.1, "black"),
                offset=ft.Offset(0, 5)
            ),
            col={"xs": 6, "sm": 6, "md": 3, "lg": 2}, 
            on_click=lambda _: nav(f"/my_plant_details/{plant_obj.plant_id}"),
            content=ft.Column(
                spacing=0,
                controls=[
                    # КАРТИНКА (AspectRatio 1:1)
                    ft.Container(
                        aspect_ratio=1.0,
                        content=ft.Image(
                            src=img_path, 
                            fit=ft.ImageFit.COVER, 
                            border_radius=ft.border_radius.only(top_left=25, top_right=25)
                        )
                    ),
                    # ИНФО-БЛОК
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
                                # Ряд динамических иконок
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

    # 4. СЕТКА (Grid)
    grid = ft.ResponsiveRow(spacing=15, run_spacing=15)
    
    if not my_plants:
        grid.controls.append(
            ft.Container(
                content=ft.Column([
                    ft.Container(height=50),
                    ft.Icon(ft.Icons.SEARCH_OFF, size=80, color="grey300"),
                    ft.Text(
                        "У вас пока нет растений\nНажмите +, чтобы добавить первое!", 
                        text_align="center", 
                        size=16,
                        color="grey500", 
                        font_family="Montserrat"
                    )
                ], horizontal_alignment="center"),
                col=12
            )
        )
    else:
        for p in my_plants:
            grid.controls.append(create_plant_card(p))

    # СБОРКА ФИНАЛЬНОГО ВИДА
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