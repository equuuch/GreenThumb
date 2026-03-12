import flet as ft
from database.session import SessionLocal
from database.models import CareCalendar, Plant
from services.care_service import CareService  # Добавили сервис для выполнения задач
from sqlalchemy.orm import joinedload
from sqlalchemy import select
from datetime import date

def CalendarView(page: ft.Page, nav, user_state):
    view = ft.View()
    view.route = "/calendar"
    view.bgcolor = "#F9F9F9"
    
    u_id = user_state.get("id")
    if not u_id:
        page.go("/")
        return view

    # --- ОБРАБОТЧИК ВЫПОЛНЕНИЯ ЗАДАЧИ ---
    def handle_complete(e, task_id):
        db = SessionLocal()
        try:
            # Используем твой CareService для циклического обновления задач
            CareService.complete_task(db, task_id)
            page.go("/calendar") # Перезагружаем страницу для обновления списка
        finally:
            db.close()

    # --- ЗАГРУЗКА ДАННЫХ ---
    db = SessionLocal()
    try:
        # Загружаем ВСЕ задачи (и выполненные, и нет) для истории и планов
        query = (
            select(CareCalendar)
            .options(joinedload(CareCalendar.plant))
            .join(Plant)
            .where(Plant.user_id == u_id, Plant.is_active == True)
            .order_by(CareCalendar.scheduled_date)
        )
        tasks = db.scalars(query).all()
    finally:
        db.close()

    # Группировка по датам
    tasks_by_date = {}
    for t in tasks:
        d_str = t.scheduled_date.strftime("%d.%m.%Y")
        if d_str not in tasks_by_date:
            tasks_by_date[d_str] = []
        tasks_by_date[d_str].append(t)

    # --- UI ---
    content = ft.Column(scroll=ft.ScrollMode.ADAPTIVE, expand=True, spacing=15)
    
    content.controls.append(
        ft.Text("График ухода", size=24, weight="bold", color="black")
    )

    if not tasks:
        content.controls.append(ft.Text("Задач пока нет 🌿", color="grey"))
    else:
        for d_str, day_tasks in tasks_by_date.items():
            is_today = d_str == date.today().strftime("%d.%m.%Y")
            
            # Заголовок даты
            content.controls.append(
                ft.Container(
                    content=ft.Text(
                        "Сегодня" if is_today else d_str, 
                        weight="bold", size=16, 
                        color="#009753" if is_today else "black54"
                    ),
                    margin=ft.margin.only(top=10)
                )
            )
            
            # Карточки задач
            for t in day_tasks:
                content.controls.append(
                    ft.Container(
                        bgcolor="white" if not t.is_completed else "#F0F0F0",
                        padding=15, 
                        border_radius=15,
                        shadow=ft.BoxShadow(blur_radius=5, color="black12") if not t.is_completed else None,
                        content=ft.Row([
                            ft.Icon(
                                ft.Icons.WATER_DROP if t.task_type == "watering" else ft.Icons.WB_SUNNY, 
                                color="#009753" if not t.is_completed else "grey"
                            ),
                            ft.Column([
                                ft.Text(
                                    t.plant.custom_name, 
                                    weight="bold",
                                    color="black" if not t.is_completed else "grey"
                                ),
                                ft.Text(
                                    "Полить" if t.task_type == "watering" else "Уход", 
                                    size=12, color="grey"
                                )
                            ], expand=True),
                            # Кнопка выполнения (только если задача не сделана)
                            ft.IconButton(
                                icon=ft.Icons.CHECK_CIRCLE_OUTLINE,
                                icon_color="#009753",
                                on_click=lambda e, tid=t.calendar_id: handle_complete(e, tid),
                                visible=not t.is_completed
                            ) if not t.is_completed else ft.Icon(ft.Icons.DONE_ALL, color="green", size=20)
                        ])
                    )
                )

    # Собираем View
    view.controls.append(
        ft.AppBar(
            title=ft.Text("Календарь"), 
            bgcolor="white", 
            color="black",
            leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda _: page.go("/profile"))
        )
    )
    view.controls.append(ft.Container(content=content, padding=20, expand=True))
    
    return view