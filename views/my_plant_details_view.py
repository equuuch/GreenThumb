import flet as ft
from database.session import get_db
from database.models import Plant, CareCalendar
from services.care_service import CareService 
from sqlalchemy.orm import joinedload
from datetime import datetime

def MyPlantDetailsView(page: ft.Page, nav, plant_id, user_state):
    view = ft.View()
    view.route = f"/my_plant_details/{plant_id}"
    view.bgcolor = "white"
    view.padding = 0

    # 1. ЗАГРУЗКА ДАННЫХ ИЗ БД
    with next(get_db()) as db:
        plant = db.query(Plant).options(
            joinedload(Plant.catalog_info)
        ).filter(Plant.plant_id == plant_id).first()

        if not plant:
            return ft.View(controls=[
                ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda _: nav("/my_plants")), 
                ft.Text("Растение не найдено")
            ])

        cat_info = plant.catalog_info
        light_val = cat_info.default_light_level if cat_info else 0.5
        
        if plant.last_watered_at and cat_info and cat_info.default_watering_interval:
            days_since = (datetime.now() - plant.last_watered_at).days
            water_val = max(0.0, min(1.0, 1.0 - (days_since / cat_info.default_watering_interval)))
        else:
            water_val = 0.5

        health_val = 1.0 if water_val > 0.2 else 0.4

    # --- РЕАКТИВНЫЕ ЭЛЕМЕНТЫ ШКАЛЫ ---
    # Создаем их здесь, чтобы handle_watering мог до них дотянуться
    water_bar_fill = ft.Container(
        bgcolor="#009753" if water_val > 0.6 else "#FFC107" if water_val > 0.3 else "#FF5252",
        height=10,
        expand=max(1, int(water_val * 10)),
        border_radius=5,
        animate=ft.animation.Animation(800, ft.AnimationCurve.DECELERATE) # Плавный запуск
    )
    water_bar_empty = ft.Container(expand=10 - water_bar_fill.expand)

    def handle_watering(e):
        with next(get_db()) as db:
            task = db.query(CareCalendar).filter(
                CareCalendar.plant_id == plant_id,
                CareCalendar.task_type == "watering",
                CareCalendar.is_completed == False
            ).first()

            if task:
                CareService.complete_task(db, task.calendar_id)
            else:
                plant_obj = db.get(Plant, plant_id)
                if plant_obj:
                    plant_obj.last_watered_at = datetime.now()
                    db.commit()

        # МЕНЯЕМ ШКАЛУ БЕЗ ПЕРЕЗАГРУЗКИ (page.go)
        water_bar_fill.expand = 10
        water_bar_fill.bgcolor = "#009753"
        water_bar_empty.expand = 0
        
        snack = ft.SnackBar(
            ft.Text("Растение полито! Шкалы обновлены."),
            bgcolor="#009753"
        )
        page.overlay.append(snack)
        snack.open = True
        page.update()

    # --- КОНСТРУКТОР ШКАЛ ---
    def create_stat(label, icon, val, custom_fill=None, custom_empty=None):
        color = "#009753" if val > 0.6 else "#FFC107" if val > 0.3 else "#FF5252"
        safe_val = max(1, int(val * 10))
        
        # Используем либо кастомный (реактивный) филл, либо обычный статический
        fill = custom_fill if custom_fill else ft.Container(
            bgcolor=color, height=10, expand=safe_val, border_radius=5
        )
        empty = custom_empty if custom_empty else ft.Container(expand=10 - safe_val)

        return ft.Column([
            ft.Row([
                ft.Icon(icon, size=18, color=color), 
                ft.Text(label, size=14, weight="w600", color="black", font_family="Montserrat")
            ], spacing=10),
            ft.Container(
                bgcolor="#EBEBEB", 
                height=10, 
                border_radius=5,
                content=ft.Row([fill, empty], spacing=0)
            ),
            ft.Container(height=12)
        ])

    # --- ПОСТРОЕНИЕ ИНТЕРФЕЙСА ---
    img_path = f"uploads/{plant.image_url}" if plant.image_url else "https://images.unsplash.com/photo-1453904300235-0f2f60b15b5d?q=80&w=300"

    # Шапка с фото (твой Stack)
    header = ft.Stack([
        ft.Image(
            src=img_path,
            fit=ft.ImageFit.COVER,
            width=400, # Используем фиксированную ширину для стабильности
            height=450
        ),
        ft.Container(
            padding=ft.padding.only(top=40, left=15, right=15),
            content=ft.Row([
                ft.IconButton(
                    ft.Icons.ARROW_BACK_IOS_NEW, 
                    icon_color="black", 
                    bgcolor="white70",
                    on_click=lambda _: nav("/my_plants")
                ),
                ft.Text("Детали", weight="bold", size=18, color="black"),
                ft.IconButton(ft.Icons.EDIT_OUTLINED, icon_color="black", bgcolor="white70")
            ], alignment="spaceBetween")
        )
    ])

    # Контентная часть (твоя белая плашка)
    content = ft.Container(
        bgcolor="#F4F4F4",
        padding=ft.padding.all(30),
        border_radius=ft.border_radius.only(top_left=35, top_right=35),
        margin=ft.margin.only(top=-40),
        expand=True,
        content=ft.Column([
            ft.Row([
                ft.Text(plant.custom_name, size=28, weight="bold", color="black"),
                ft.Container(
                    width=12, height=12, 
                    bgcolor="#009753" if health_val > 0.5 else "red", 
                    border_radius=6
                )
            ], alignment="spaceBetween"),
            
            ft.Text(
                cat_info.species_name if cat_info else "Неизвестный вид", 
                size=16, color="grey600"
            ),
            
            ft.Container(height=25),
            
            # ОТРИСОВКА ШКАЛ (Уровень влаги теперь реактивный)
            create_stat("Уровень влаги", ft.Icons.WATER_DROP_OUTLINED, water_val, water_bar_fill, water_bar_empty),
            create_stat("Требуемый свет", ft.Icons.WB_SUNNY_OUTLINED, light_val),
            create_stat("Здоровье", ft.Icons.FAVORITE_BORDER, health_val),
            
            ft.Container(height=25),
            
            # Кнопка действия
            ft.ElevatedButton(
                "Отметить полив",
                bgcolor="#009753",
                color="white",
                height=55,
                width=float("inf"),
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=15)),
                on_click=handle_watering
            )
        ], scroll=ft.ScrollMode.ADAPTIVE)
    )

    # Финальный ListView
    view.controls.append(
        ft.ListView([
            header,
            content
        ], expand=True, padding=0)
    )

    return view