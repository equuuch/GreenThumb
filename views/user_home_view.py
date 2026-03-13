import flet as ft
from database.session import get_db
from services.plant_services import PlantService
from services.care_service import CareService
from datetime import date
from database.models import CareCalendar, Plant
from sqlalchemy import select

def UserHomeView(page: ft.Page, nav, user_state):
    """
    модуль главного экрана авторизованного пользователя (дашборд).
    реализует сводную информацию о состоянии сада, текущих задачах и системных уведомлениях.
    """
    view = ft.View()
    view.route = "/user_home"
    view.bgcolor = "#F9F9F9"
    view.padding = 20

    # извлечение данных текущей сессии пользователя.
    user_id = user_state.get("id")
    user_name = user_state.get("name", "Садовод")

    # 1. блок консолидации данных из нескольких источников (dal).
    with next(get_db()) as db:
        # получение списка активных растений через специализированный сервис.
        my_plants = PlantService.get_user_plants(db, user_id)
        # извлечение оперативного списка задач на текущую дату.
        today_tasks = CareService.get_today_tasks(db, user_id)
        
        # выполнение предиктивной проверки на наличие просроченных задач (alerts).
        # результат используется для управления видимостью красного индикатора (бейджа) в шапке.
        has_alerts = db.scalar(
            select(CareCalendar)
            .join(Plant)
            .where(
                Plant.user_id == user_id,
                CareCalendar.is_completed == False,
                CareCalendar.scheduled_date < date.today()
            )
        ) is not None

    # --- описание компонентов навигации и уведомлений ---

    # построение иконки уведомлений с использованием стека (stack) для наложения индикатора события.
    notification_icon = ft.Stack([
        ft.IconButton(
            icon=ft.Icons.NOTIFICATIONS_OUTLINED,
            icon_color="black",
            on_click=lambda _: nav("/notifications")
        ),
        # визуальный маркер (красная точка), реагирующий на наличие просроченных задач.
        ft.Container(
            content=ft.CircleAvatar(bgcolor="red", radius=4),
            alignment=ft.alignment.top_right,
            right=5,
            top=5,
            visible=has_alerts
        )
    ])

    # кнопка быстрого перехода к глобальному ботаническому справочнику.
    catalog_button = ft.IconButton(
        icon=ft.Icons.MENU_BOOK_OUTLINED,
        icon_color="black",
        on_click=lambda _: nav("/catalog")
    )

    # горизонтальная компоновка заголовка с приветствием и функциональными кнопками.
    header = ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        controls=[
            ft.Column([
                ft.Text(f"Здравствуйте, {user_name}!", size=12, color="#6E6E6E"),
                ft.Text("Ваш сад", size=26, weight="bold", color="black"),
            ], spacing=2),
            ft.Row([catalog_button, notification_icon], spacing=0)
        ]
    )

    # --- формирование сетки превью растений ---
    grid = ft.ResponsiveRow(spacing=15)
    
    if not my_plants:
        # обработка состояния отсутствия данных в коллекции.
        grid.controls.append(
            ft.Container(
                content=ft.Text("В саду пока пусто...", size=14, color="gray", italic=True),
                padding=20
            )
        )
    else:
        # алгоритм отображения сокращенного списка (limit 4) для главного экрана.
        for p in my_plants[:4]:
            # нормализация путей к медиафайлам: удаление ведущих слешей для корректной работы движка flet.
            raw_path = p.image_url if p.image_url else "plants/default.png"
            img_path = f"/{raw_path.lstrip('/')}"

            # генерация интерактивной карточки-превью.
            grid.controls.append(
                ft.Container(
                    bgcolor="white", 
                    padding=10, 
                    border_radius=20, 
                    col={"xs": 6, "sm": 6}, # адаптивное распределение: по 2 элемента в ряд.
                    shadow=ft.BoxShadow(blur_radius=10, color="black12"),
                    on_click=lambda e, plant_id=p.plant_id: nav(f"/my_plant_details/{plant_id}"),
                    content=ft.Column([
                        ft.Image(
                            src=img_path, 
                            width=200, 
                            height=120, 
                            fit=ft.ImageFit.COVER, 
                            border_radius=15,
                            error_content=ft.Icon(ft.Icons.IMAGE_NOT_SUPPORTED_OUTLINED, color="grey")
                        ),
                        ft.Container(
                            padding=ft.padding.only(left=5, top=5, right=5),
                            content=ft.Text(
                                p.custom_name, 
                                weight="bold", 
                                size=14, 
                                color="black", 
                                max_lines=1, 
                                overflow=ft.TextOverflow.ELLIPSIS
                            )
                        ),
                    ], spacing=0)
                )
            )

    # --- модуль оперативного планирования ухода ---
    task_list = ft.Column(spacing=12)
    if not today_tasks:
        # уведомление об отсутствии запланированных действий на текущие сутки.
        task_list.controls.append(ft.Text("На сегодня задач нет! ✨", color="gray", size=14))
    else:
        # итеративная сборка списка актуальных задач с иконками типов ухода.
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

    # основной контейнер секции задач с акцентным оформлением.
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

    # итоговая сборка вьюхи в вертикальный прокручиваемый список.
    lv = ft.ListView(expand=True, spacing=25)
    lv.controls.extend([header, grid, tasks_container])

    view.controls.append(lv)
    return view