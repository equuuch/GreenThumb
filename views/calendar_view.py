import flet as ft
from database.session import SessionLocal
from database.models import CareCalendar, Plant
from services.care_service import CareService  # импорт сервиса для реализации циклического планирования
from sqlalchemy.orm import joinedload
from sqlalchemy import select
from datetime import date

def CalendarView(page: ft.Page, nav, user_state):
    """
    модуль визуализации календаря ухода. 
    реализует группировку задач по датам и интерактивное управление жизненным циклом растений.
    """
    view = ft.View()
    view.route = "/calendar"
    view.bgcolor = "#F9F9F9"
    
    # проверка авторизации пользователя перед рендерингом защищенного контента.
    u_id = user_state.get("id")
    if not u_id:
        page.go("/")
        return view

    # --- блок обработки событий ---

    def handle_complete(e, task_id):
        """обработчик завершения задачи. инициирует пересчет всей сетки задач через careservice."""
        db = SessionLocal()
        try:
            # вызов логики бизнес-слоя для закрытия текущей и создания следующей задачи.
            CareService.complete_task(db, task_id)
            # принудительная навигация на текущий маршрут для реактивного обновления данных на экране.
            page.go("/calendar") 
        finally:
            db.close()

    # --- блок загрузки и трансформации данных ---

    db = SessionLocal()
    try:
        # выполнение sql-запроса с использованием «жадной загрузки» (joinedload).
        # это минимизирует количество обращений к бд (решение проблемы n+1 query).
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

    # алгоритм группировки плоского списка задач в словарь по строковому представлению даты.
    # необходимо для создания секционного интерфейса (хэдеры дат).
    tasks_by_date = {}
    for t in tasks:
        d_str = t.scheduled_date.strftime("%d.%m.%Y")
        if d_str not in tasks_by_date:
            tasks_by_date[d_str] = []
        tasks_by_date[d_str].append(t)

    # --- построение визуальной структуры (ui) ---

    # использование адаптивного скролла для корректного поведения на различных типах устройств.
    content = ft.Column(scroll=ft.ScrollMode.ADAPTIVE, expand=True, spacing=15)
    
    content.controls.append(
        ft.Text("График ухода", size=24, weight="bold", color="black")
    )

    # условный рендеринг: отображение заглушки при отсутствии запланированных действий.
    if not tasks:
        content.controls.append(ft.Text("Задач пока нет 🌿", color="grey"))
    else:
        # итерация по сгруппированным данным для формирования временной шкалы.
        for d_str, day_tasks in tasks_by_date.items():
            is_today = d_str == date.today().strftime("%d.%m.%Y")
            
            # визуальный заголовок группы задач (дата или маркер «сегодня»).
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
            
            # рендеринг карточек задач внутри конкретного дня.
            for t in day_tasks:
                content.controls.append(
                    ft.Container(
                        # динамическая стилизация фона: выделение активных и выполненных (серых) задач.
                        bgcolor="white" if not t.is_completed else "#F0F0F0",
                        padding=15, 
                        border_radius=15,
                        # применение теней только для актуальных задач для создания глубины интерфейса.
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
                            # реактивный элемент управления: кнопка подтверждения выполнения.
                            # отображается только для невыполненных задач.
                            ft.IconButton(
                                icon=ft.Icons.CHECK_CIRCLE_OUTLINE,
                                icon_color="#009753",
                                on_click=lambda e, tid=t.calendar_id: handle_complete(e, tid),
                                visible=not t.is_completed
                            ) if not t.is_completed else ft.Icon(ft.Icons.DONE_ALL, color="green", size=20)
                        ])
                    )
                )

    # финальная сборка иерархии компонентов вьюхи.
    view.controls.append(
        ft.AppBar(
            title=ft.Text("Календарь"), 
            bgcolor="white", 
            color="black",
            leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda _: page.go("/profile"))
        )
    )
    # оборачивание контента в контейнер с отступами для соблюдения визуальных гайдов.
    view.controls.append(ft.Container(content=content, padding=20, expand=True))
    
    return view