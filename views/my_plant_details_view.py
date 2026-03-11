import flet as ft
from database.session import get_db
from database.models import Plant, CareCalendar
from sqlalchemy.orm import joinedload
from datetime import datetime
import time

def MyPlantDetailsView(page: ft.Page, nav, plant_id, user_state):
    view = ft.View()
    view.route = f"/my_plant_details/{plant_id}"
    view.bgcolor = "white"
    view.padding = 0

    # 1. ЗАГРУЗКА ДАННЫХ
    with next(get_db()) as db:
        db.expire_all() 
        plant = db.query(Plant).options(
            joinedload(Plant.catalog_info)
        ).filter(Plant.plant_id == plant_id).first()

        if not plant:
            return ft.View(controls=[ft.Text("Растение не найдено")])

        cat_info = plant.catalog_info
        
        # --- ИСПРАВЛЕННЫЙ РАСЧЕТ ВЛАГИ ---
        # Если в базе нет интервала, берем 3 дня как стандарт
        interval_days = cat_info.default_watering_interval if (cat_info and cat_info.default_watering_interval) else 3
        water_val = 0.5 # Значение "на всякий случай"
        
        if plant.last_watered_at:
            interval_sec = interval_days * 24 * 3600
            diff_sec = (datetime.now() - plant.last_watered_at).total_seconds()
            # Вычисляем процент: 1.0 (только что полили) до 0.0 (пора поливать)
            water_val = max(0.0, min(1.0, 1.0 - (diff_sec / interval_sec)))
            print(f"DEBUG MATH: Растение {plant.custom_name}, Процент влаги: {water_val:.2f}")

        light_val = cat_info.default_light_level if cat_info else 0.5
        health_val = 1.0 if water_val > 0.2 else 0.4

    # --- ЭЛЕМЕНТЫ ШКАЛЫ (100-балльная система для анимации) ---
    current_fill_weight = int(water_val * 100)
    
    water_bar_fill = ft.Container(
        bgcolor="#009753" if water_val > 0.6 else "#FFC107" if water_val > 0.3 else "#FF5252",
        height=10, 
        expand=max(1, current_fill_weight), 
        border_radius=5,
        animate=ft.animation.Animation(800, ft.AnimationCurve.DECELERATE)
    )
    water_bar_empty = ft.Container(
        expand=100 - max(1, current_fill_weight),
        animate=ft.animation.Animation(800, ft.AnimationCurve.DECELERATE)
    )

    # 2. ОБРАБОТЧИК ПОЛИВА
    def handle_watering(e):
        e.control.disabled = True
        e.control.content = ft.ProgressRing(width=20, height=20, color="white", stroke_width=2)
        page.update()

        with next(get_db()) as db:
            plant_db = db.query(Plant).filter(Plant.plant_id == plant_id).first()
            if plant_db:
                plant_db.last_watered_at = datetime.now()
                
                # Закрываем задачу в календаре
                task = db.query(CareCalendar).filter(
                    CareCalendar.plant_id == plant_id,
                    CareCalendar.task_type == "watering",
                    CareCalendar.is_completed == False
                ).first()
                
                if task:
                    task.is_completed = True
                    task.completion_date = datetime.now()
                
                db.commit()
            db.close()

        # Визуальный "буст" шкалы сразу после нажатия
        water_bar_fill.expand = 100
        water_bar_fill.bgcolor = "#009753"
        water_bar_empty.expand = 0
        
        snack = ft.SnackBar(ft.Text("Растение полито!"), bgcolor="#009753")
        page.overlay.append(snack)
        snack.open = True
        page.update()
        
        # Пауза, чтобы анимация успела дойти до конца
        time.sleep(1.2)
        nav("/my_plants")

    # Вспомогательная функция для отрисовки статов
    def create_stat(label, icon, val, custom_fill=None, custom_empty=None):
        color = "#009753" if val > 0.6 else "#FFC107" if val > 0.3 else "#FF5252"
        
        # Если переданы кастомные контейнеры (как для влаги), используем их
        if custom_fill:
            fill = custom_fill
            empty = custom_empty
        else:
            # Для остальных (Свет, Здоровье) создаем статику
            safe_val = max(1, int(val * 100))
            fill = ft.Container(bgcolor=color, height=10, expand=safe_val, border_radius=5)
            empty = ft.Container(expand=100 - safe_val)

        return ft.Column([
            ft.Row([
                ft.Icon(icon, size=18, color=color), 
                ft.Text(label, size=14, weight="w600", color="black")
            ], spacing=10),
            ft.Container(
                bgcolor="#EBEBEB", 
                height=10, 
                border_radius=5, 
                content=ft.Row([fill, empty], spacing=0)
            ),
            ft.Container(height=12)
        ])

    # 3. ВЕРСТКА ИНТЕРФЕЙСА
    img_src = f"assets/{plant.image_url}" if plant.image_url else "https://images.unsplash.com/photo-1453904300235-0f2f60b15b5d?q=80&w=300"

    header = ft.Stack([
        ft.Image(src=img_src, fit=ft.ImageFit.COVER, width=400, height=450),
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

    content = ft.Container(
        bgcolor="white", 
        padding=ft.padding.all(30),
        border_radius=ft.border_radius.only(top_left=35, top_right=35),
        margin=ft.margin.only(top=-40),
        expand=True,
        content=ft.Column([
            ft.Row([
                ft.Text(plant.custom_name, size=28, weight="bold", color="black"),
                ft.Container(width=12, height=12, bgcolor="#009753" if health_val > 0.5 else "red", border_radius=6)
            ], alignment="spaceBetween"),
            ft.Text(cat_info.species_name if cat_info else "Неизвестный вид", size=16, color="grey600"),
            ft.Container(height=25),
            
            # Рендер статов
            create_stat("Уровень влаги", ft.Icons.WATER_DROP_OUTLINED, water_val, water_bar_fill, water_bar_empty),
            create_stat("Требуемый свет", ft.Icons.WB_SUNNY_OUTLINED, light_val),
            create_stat("Здоровье", ft.Icons.FAVORITE_BORDER, health_val),
            
            ft.Container(height=25),
            
            # Кнопка полива
            ft.ElevatedButton(
                content=ft.Text("Отметить полив", size=16, weight="bold"),
                bgcolor="#009753", 
                color="white", 
                height=55, 
                width=float("inf"),
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=15)),
                on_click=handle_watering
            )
        ], scroll=ft.ScrollMode.ADAPTIVE)
    )

    view.controls.append(ft.ListView([header, content], expand=True, padding=0))
    return view