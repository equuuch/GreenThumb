import flet as ft
from database.session import get_db
from services.plant_services import PlantService
from services.care_service import CareService
from datetime import date

def UserHomeView(page: ft.Page, nav, user_state):
    view = ft.View()
    view.route = "/user_home"
    view.bgcolor = "#F9F9F9"
    view.padding = 20

    user_name = user_state.get("name", "Садовод")
    user_id = user_state.get("id")

    # 1. ЗАГРУЗКА ДАННЫХ ИЗ БАЗЫ
    with next(get_db()) as db:
        # Получаем активные растения
        my_plants = PlantService.get_user_plants(db, user_id)
        # Получаем задачи на сегодня
        today_tasks = CareService.get_today_tasks(db, user_id)
        
        # Проверка на наличие просроченных задач для индикатора уведомлений
        # Мы просто смотрим, есть ли в базе задачи с датой < сегодня, которые не выполнены
        from database.models import CareCalendar, Plant
        from sqlalchemy import select
        
        has_alerts = db.scalar(
            select(CareCalendar)
            .join(Plant)
            .where(
                Plant.user_id == user_id,
                CareCalendar.is_completed == False,
                CareCalendar.scheduled_date < date.today()
            )
        ) is not None

    # --- ШАПКА ---
    # Создаем иконку уведомлений с индикатором или без
    notification_icon = ft.Stack([
        ft.IconButton(
            icon=ft.Icons.NOTIFICATIONS_OUTLINED,
            icon_color="black",
            on_click=lambda _: nav("/notifications") # Переход на новый экран
        ),
        # Если есть алерты — рисуем красную точку
        ft.Container(
            content=ft.CircleAvatar(bgcolor="red", radius=4),
            alignment=ft.alignment.top_right,
            right=5,
            top=5,
            visible=has_alerts # Точка видна только если есть просроченные задачи
        )
    ])

    header = ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        controls=[
            ft.Column([
                ft.Text(f"Здравствуйте, {user_name}!", size=12, color="#6E6E6E"),
                ft.Text("Ваш сад", size=26, weight="bold", color="black"),
            ], spacing=2),
            notification_icon
        ]
    )

    # --- ПРЕВЬЮ РАСТЕНИЙ (Grid) ---
    grid = ft.ResponsiveRow(spacing=15)
    if not my_plants:
        grid.controls.append(ft.Text("В саду пока пусто...", size=14, color="gray", italic=True))
    else:
        # Показываем только первые 2 для главного экрана
        for p in my_plants[:2]:
            # Исправляем путь: если в БД только имя файла, добавляем путь к ассетам
            img_path = f"uploads/{p.image_url}" if p.image_url else "/aloe.png"
            grid.controls.append(
                ft.Container(
                    bgcolor="white", padding=10, border_radius=20, col=6,
                    shadow=ft.BoxShadow(blur_radius=10, color="black12"),
                    on_click=lambda _: nav("/my_plants"),
                    content=ft.Column([
                        ft.Image(src=img_path, width=150, height=110, fit="cover", border_radius=15),
                        ft.Text(p.custom_name, weight="bold", size=14, color="black", max_lines=1),
                    ])
                )
            )

    # --- СПИСОК ЗАДАЧ ---
    task_list = ft.Column(spacing=12)
    if not today_tasks:
        task_list.controls.append(ft.Text("На сегодня задач нет! Отдыхайте ✨", color="gray", size=14))
    else:
        for task in today_tasks:
            task_list.controls.append(
                ft.Row([
                    ft.Icon(
                        ft.Icons.WATER_DROP_OUTLINED if task.task_type == "watering" else ft.Icons.WB_SUNNY, 
                        color="#009753", size=20
                    ),
                    ft.Text(f"{task.plant.custom_name}: Полить", color="black", size=14, weight="w500"),
                ], spacing=10)
            )

    tasks_container = ft.Container(
        bgcolor="white", padding=20, border_radius=25,
        shadow=ft.BoxShadow(blur_radius=15, color="black12"),
        content=ft.Column([
            ft.Text("Сегодняшние задачи", size=18, weight="bold", color="black"),
            ft.Divider(height=1, color="#EEEEEE"),
            ft.Container(height=5),
            task_list
        ])
    )

    # Сборка экрана
    lv = ft.ListView(expand=True, spacing=25)
    lv.controls.extend([header, grid, tasks_container])

    view.controls.append(lv)
    return view