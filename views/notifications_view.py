import flet as ft
from database.session import SessionLocal
from database.models import CareCalendar, Plant
from sqlalchemy import select
from datetime import date

def NotificationsView(page: ft.Page, nav, user_state):
    view = ft.View()
    view.route = "/notifications"
    view.bgcolor = "#F9F9F9"

    u_id = user_state.get("id")

    # --- ЗАГРУЗКА ДАННЫХ (Пример: ищем просроченные задачи) ---
    db = SessionLocal()
    alerts = []
    try:
        # Ищем задачи, которые должны были быть выполнены до сегодняшнего дня, но не сделаны
        query = (
            select(CareCalendar)
            .join(Plant)
            .where(
                Plant.user_id == u_id,
                CareCalendar.is_completed == False,
                CareCalendar.scheduled_date < date.today()
            )
        )
        overdue_tasks = db.scalars(query).all()
        
        for task in overdue_tasks:
            alerts.append({
                "title": "Пропущен полив!",
                "body": f"Ваше растение '{task.plant.custom_name}' очень хочет пить.",
                "type": "urgent",
                "time": "Сегодня"
            })
    finally:
        db.close()

    # --- UI ЭЛЕМЕНТЫ ---
    content = ft.Column(scroll=ft.ScrollMode.ADAPTIVE, expand=True, spacing=15)

    def create_notification_card(title, body, type, time):
        is_urgent = type == "urgent"
        return ft.Container(
            bgcolor="white",
            padding=15,
            border_radius=15,
            shadow=ft.BoxShadow(blur_radius=5, color="black12"),
            content=ft.Row([
                ft.Container(
                    width=10, height=10, 
                    bgcolor="red" if is_urgent else "#009753", 
                    border_radius=5
                ),
                ft.Column([
                    ft.Text(title, weight="bold", size=15, color="black"),
                    ft.Text(body, size=13, color="grey700"),
                    ft.Text(time, size=11, color="grey400"),
                ], expand=True, spacing=2)
            ], vertical_alignment=ft.CrossAxisAlignment.START)
        )

    # Заполнение контента
    if not alerts:
        content.controls.append(
            ft.Container(
                alignment=ft.alignment.center,
                padding=50,
                content=ft.Column([
                    ft.Icon(ft.Icons.NOTIFICATIONS_NONE_ROUNDED, size=50, color="grey300"),
                    ft.Text("Уведомлений пока нет", color="grey400")
                ], horizontal_alignment="center")
            )
        )
    else:
        content.controls.append(ft.Text("Новые", weight="bold", size=18))
        for a in alerts:
            content.controls.append(create_notification_card(a["title"], a["body"], a["type"], a["time"]))

    # Сборка View
    view.controls.append(
        ft.AppBar(
            title=ft.Text("Уведомления"),
            bgcolor="white",
            color="black",
            leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda _: page.go("/user_home"))
        )
    )
    view.controls.append(ft.Container(content=content, padding=20, expand=True))
    
    return view