import flet as ft
from database.session import SessionLocal
from database.models import CareCalendar, Plant
from sqlalchemy import select
from datetime import date

def NotificationsView(page: ft.Page, nav, user_state):
    """
    модуль системы уведомлений. 
    отвечает за выявление критических событий (пропуски полива) и их визуализацию.
    """
    view = ft.View()
    view.route = "/notifications"
    view.bgcolor = "#F9F9F9"

    # получение идентификатора текущего пользователя для фильтрации персональных уведомлений.
    u_id = user_state.get("id")

    # --- блок аналитики и загрузки данных из бд ---
    db = SessionLocal()
    alerts = [] # временный массив для хранения трансформированных данных уведомлений.
    try:
        # построение sql-запроса для поиска просроченных (overdue) задач.
        # критерии: задача принадлежит пользователю, не выполнена и дата по графику меньше текущей.
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
        
        # цикл трансформации записей базы данных в формат, пригодный для отображения в ui.
        for task in overdue_tasks:
            alerts.append({
                "title": "Пропущен полив!",
                "body": f"Ваше растение '{task.plant.custom_name}' очень хочет пить.",
                "type": "urgent", # тип уведомления для задания визуального приоритета (цвет индикатора).
                "time": "Сегодня"
            })
    finally:
        db.close() # гарантированное закрытие соединения с базой данных.

    # --- логика построения визуальных компонентов ---

    # инициализация контейнера списка с поддержкой адаптивной прокрутки.
    content = ft.Column(scroll=ft.ScrollMode.ADAPTIVE, expand=True, spacing=15)

    def create_notification_card(title, body, type, time):
        """
        вспомогательная функция (фабрика) для рендеринга карточки уведомления.
        реализует визуальную дифференциацию по степени важности.
        """
        is_urgent = type == "urgent"
        return ft.Container(
            bgcolor="white",
            padding=15,
            border_radius=15,
            # применение эффекта тени для выделения элемента на общем фоне страницы.
            shadow=ft.BoxShadow(blur_radius=5, color="black12"),
            content=ft.Row([
                # цветовой индикатор критичности (красный для срочных, зеленый для информационных).
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

    # алгоритм наполнения контента: обработка пустого состояния (empty state).
    if not alerts:
        content.controls.append(
            ft.Container(
                alignment=ft.alignment.center,
                padding=50,
                content=ft.Column([
                    # визуальная заглушка при отсутствии актуальных уведомлений.
                    ft.Icon(ft.Icons.NOTIFICATIONS_NONE_ROUNDED, size=50, color="grey300"),
                    ft.Text("Уведомлений пока нет", color="grey400")
                ], horizontal_alignment="center")
            )
        )
    else:
        # рендеринг секции активных уведомлений.
        content.controls.append(ft.Text("Новые", weight="bold", size=18))
        for a in alerts:
            content.controls.append(create_notification_card(a["title"], a["body"], a["type"], a["time"]))

    # сборка результирующей вьюхи с системным AppBar и навигацией.
    view.controls.append(
        ft.AppBar(
            title=ft.Text("Уведомления"),
            bgcolor="white",
            color="black",
            leading=ft.IconButton(
                icon=ft.Icons.ARROW_BACK, 
                on_click=lambda _: page.go("/user_home") # возврат на домашний экран пользователя.
            )
        )
    )
    # размещение основного контента внутри контейнера с отступами (padding).
    view.controls.append(ft.Container(content=content, padding=20, expand=True))
    
    return view