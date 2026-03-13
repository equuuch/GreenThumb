import flet as ft
from database.session import SessionLocal
from database.models import User, Plant, CareCalendar
from services.care_service import CareService
from services.report_services import ReportService
from services.export_services import ExportService
from sqlalchemy import desc, asc
from sqlalchemy.orm import joinedload
from datetime import datetime, date
import time

def ProfileView(page: ft.Page, nav, user_state):
    """
    модуль личного кабинета пользователя.
    реализует агрегацию статистики, управление календарем и генерацию технической документации (pdf).
    """
    view = ft.View()
    view.route = "/profile"
    view.bgcolor = "#F9F9F9"
    view.padding = 0

    # извлечение id текущего пользователя из глобального состояния приложения.
    u_id = user_state.get("id", 1)

    # --- блок обработчиков бизнес-событий ---
    
    def handle_logout(e):
        """процедура сброса авторизационных данных и перенаправления на главный экран."""
        user_state["id"] = None
        user_state["name"] = "Гость"
        page.go("/")

    def handle_report_request(e, plant_id):
        """
        комплексный процесс формирования отчетности.
        включает сбор аналитики через reportservice и бинарный рендеринг через exportservice.
        """
        # визуальное подтверждение начала фоновой задачи (замена контента кнопки на спиннер).
        e.control.disabled = True
        e.control.content = ft.ProgressRing(width=16, height=16, stroke_width=2, color="#009753")
        page.update()

        try:
            with SessionLocal() as db:
                # этап 1: сбор и консолидация данных о росте и дисциплине полива.
                data = ReportService.collect_plant_data(db, plant_id)
                if data:
                    # этап 2: программное построение pdf-файла на основе собранного словаря данных.
                    pdf_path = ExportService.create_plant_pdf(data)
                    page.snack_bar = ft.SnackBar(
                        ft.Text(f"Отчет успешно создан в папке reports"), 
                        bgcolor="#009753"
                    )
                else:
                    page.snack_bar = ft.SnackBar(ft.Text("Ошибка: данные растения не найдены"), bgcolor="red")
        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"Ошибка генерации: {str(ex)}"), bgcolor="red")
        
        # возврат визуального состояния элемента управления в исходное положение.
        e.control.disabled = False
        e.control.content = None 
        page.snack_bar.open = True
        page.update()

    def handle_complete_task(e, task_id):
        """метод фиксации выполнения задачи по уходу и инициации пересчета сетки графика."""
        db = SessionLocal()
        try:
            # выполнение транзакции по закрытию текущей задачи.
            new_task, error = CareService.complete_task(db, task_id)
            if not error:
                # принудительное обновление текущей вьюхи для актуализации списка задач.
                nav("/profile") 
            else:
                print(f"Ошибка при выполнении задачи: {error}")
        finally:
            db.close()

    def restore_from_archive(e, plant_id):
        """логика восстановления объекта из архива с восстановлением цикла ухода."""
        db = SessionLocal()
        try:
            plant = db.query(Plant).filter(Plant.plant_id == plant_id).first()
            if plant:
                plant.is_active = True # смена флага активности.
                db.commit()
                # генерация нового расписания на 30 дней вперед для восстановленного растения.
                CareService.generate_full_schedule(db, plant_id)
                nav("/profile") 
        finally:
            db.close()

    # --- блок извлечения данных для рендеринга профиля ---
    db = SessionLocal()
    try:
        # получение персональной информации пользователя.
        user_data = db.query(User).filter(User.user_id == u_id).first()
        user_name = user_data.first_name if user_data and user_data.first_name else "Пользователь"
        
        # разделение коллекции растений на активный сад и архивный фонд.
        all_plants = db.query(Plant).filter(Plant.user_id == u_id).order_by(desc(Plant.added_at)).all()
        active_plants = [p for p in all_plants if p.is_active]
        archived_plants = [p for p in all_plants if not p.is_active]
        
        # выборка ближайших 3 невыполненных задач для краткого обзора в календаре.
        active_ids = [p.plant_id for p in active_plants]
        tasks = []
        if active_ids:
            tasks = (
                db.query(CareCalendar)
                .options(joinedload(CareCalendar.plant)) 
                .filter(CareCalendar.plant_id.in_(active_ids), CareCalendar.is_completed == False)
                .order_by(asc(CareCalendar.scheduled_date))
                .limit(3).all()
            )
        
        # расчет агрегированных показателей статистики.
        plants_count = len(active_plants)
        days_streak = (datetime.now() - user_data.created_at).days + 1 if user_data and user_data.created_at else 1
    finally:
        db.close()

    # --- вспомогательные методы верстки компонентов ---
    
    def stat_column(label, value):
        """хелпер для формирования визуальных колонок статистики в заголовке профиля."""
        return ft.Container(
            content=ft.Column([
                ft.Text(str(value), weight="bold", size=16, color="black"),
                ft.Text(label, size=12, color="grey")
            ], horizontal_alignment="center"),
            on_click=lambda _: nav("/analytics"), # быстрый переход к расширенной аналитике.
            padding=10, border_radius=10, ink=True
        )

    # построение хедера профиля с использованием эффекта тени и скругления нижней части.
    profile_header = ft.Container(
        padding=25, bgcolor="white",
        border_radius=ft.border_radius.only(bottom_left=30, bottom_right=30),
        shadow=ft.BoxShadow(blur_radius=15, color=ft.Colors.BLACK12),
        content=ft.Column([
            ft.Row([
                ft.Row([
                    # аватар пользователя, генерируемый на основе первой буквы имени.
                    ft.Container(
                        width=60, height=60, border_radius=30, bgcolor="#009753",
                        content=ft.Text(user_name[0].upper() if user_name else "U", color="white", weight="bold", size=20),
                        alignment=ft.alignment.center
                    ),
                    ft.Column([
                        ft.Text(user_name, size=20, weight="bold", color="black"),
                        ft.Text("Мастер-садовод 🌿", size=13, color="#009753"),
                    ], spacing=0)
                ], expand=True),
                ft.IconButton(ft.Icons.LOGOUT_ROUNDED, icon_color="grey500", on_click=handle_logout)
            ]),
            ft.Divider(height=20, color="transparent"),
            # рендеринг строки статистических показателей.
            ft.Row([
                stat_column("Растения", plants_count),
                stat_column("Дней", days_streak),
                stat_column("Здоровье", "100%"),
            ], alignment=ft.MainAxisAlignment.SPACE_AROUND)
        ])
    )

    def create_plant_card(p, is_arc):
        """фабричный метод создания карточки растения для списков сада и архива."""
        p_img = p.image_url.replace("\\", "/") if p.image_url else None
        
        # формирование набора функциональных кнопок в зависимости от контекста (архив/активно).
        actions = ft.Row(spacing=0)
        if is_arc:
            actions.controls.append(
                ft.IconButton(
                    ft.Icons.UNARCHIVE_ROUNDED, 
                    icon_color="#009753", 
                    on_click=lambda e: restore_from_archive(e, p.plant_id)
                )
            )
        else:
            # интеграция кнопки выгрузки персонального отчета.
            actions.controls.append(
                ft.IconButton(
                    icon=ft.Icons.PICTURE_AS_PDF_ROUNDED,
                    icon_color="grey500",
                    icon_size=20,
                    tooltip="Скачать PDF отчет",
                    on_click=lambda e: handle_report_request(e, p.plant_id)
                )
            )
            actions.controls.append(ft.Icon(ft.Icons.CHEVRON_RIGHT, color="grey400"))

        return ft.Container(
            bgcolor="white", padding=15, border_radius=22,
            shadow=ft.BoxShadow(blur_radius=5, color=ft.Colors.BLACK12),
            content=ft.Row([
                ft.Image(
                    src=f"assets/{p_img}" if p_img else "assets/aloe.png", 
                    width=50, height=50, fit="cover", border_radius=12
                ),
                ft.Column([
                    ft.Text(p.custom_name, weight="bold", color="black", size=15),
                    ft.Text("В архиве" if is_arc else (p.status_text or "Здорово"), size=12, color="grey")
                ], expand=True, spacing=2),
                actions
            ]),
            on_click=None if is_arc else lambda _: nav(f"/my_plant_details/{p.plant_id}")
        )

    # --- инициализация коллекций списков с механизмом переключения видимости ---
    active_list_col = ft.Column(spacing=12, visible=True)
    archive_list_col = ft.Column(spacing=12, visible=False)

    for p in active_plants: active_list_col.controls.append(create_plant_card(p, False))
    for p in archived_plants: archive_list_col.controls.append(create_plant_card(p, True))

    def on_tab_change(e):
        """реактивное переключение между вкладками 'мой сад' и 'архив'."""
        active_list_col.visible = (e.control.selected_index == 0)
        archive_list_col.visible = (e.control.selected_index == 1)
        view.update()

    # настройка визуального стиля вкладок в соответствии с цветовой схемой бренда.
    tabs = ft.Tabs(
        selected_index=0, 
        on_change=on_tab_change,
        label_color="#009753",
        unselected_label_color="grey500",
        indicator_color="#009753",
        tabs=[ft.Tab(text="Мой сад"), ft.Tab(text="Архив")]
    )

    # --- формирование блока оперативного календаря ухода ---
    calendar_list = ft.Column(spacing=10)
    if not tasks:
        calendar_list.controls.append(ft.Text("На сегодня задач нет ✨", size=13, color="grey", italic=True))
    else:
        for t in tasks:
            is_today = t.scheduled_date <= date.today()
            p_name = t.plant.custom_name if t.plant else "Растение"
            calendar_list.controls.append(
                ft.Container(
                    # динамическая смена фона для визуального выделения просроченных или текущих задач.
                    bgcolor="#F0F4F8" if not is_today else "#E8F5E9",
                    padding=15, border_radius=20,
                    content=ft.Row([
                        ft.Icon(ft.Icons.WATER_DROP, color="#009753" if is_today else "grey700", size=20),
                        ft.Column([
                            ft.Text(p_name, weight="bold", size=14, color="black"),
                            ft.Text("Нужно полить" if is_today else f"Полив {t.scheduled_date.strftime('%d.%m')}", size=12, color="grey700")
                        ], expand=True, spacing=0),
                        # интерактивная кнопка быстрого подтверждения полива из профиля.
                        ft.IconButton(
                            icon=ft.Icons.CHECK_CIRCLE_OUTLINE, 
                            icon_color="#009753",
                            on_click=lambda e, tid=t.calendar_id: handle_complete_task(e, tid)
                        )
                    ])
                )
            )

    # --- финальная сборка композиции экрана ---
    main_content = ft.Column(
        scroll=ft.ScrollMode.ADAPTIVE, # использование адаптивной прокрутки для плавности ui.
        expand=True,
        controls=[
            profile_header,
            ft.Container(
                padding=20,
                content=ft.Column([
                    # баннер быстрого доступа к графическим отчетам и аналитике.
                    ft.Container(
                        content=ft.ListTile(
                            leading=ft.Icon(ft.Icons.INSERT_CHART_ROUNDED, color="#009753"),
                            title=ft.Text("Аналитика и графики роста", weight="bold"),
                            subtitle=ft.Text("Посмотрите, как развиваются ваши растения"),
                            on_click=lambda _: nav("/analytics"),
                        ),
                        bgcolor="white", border_radius=15,
                        shadow=ft.BoxShadow(blur_radius=5, color=ft.Colors.BLACK12),
                    ),
                    ft.Container(height=10),
                    # секция календаря с переходом к расширенному представлению.
                    ft.Row([
                        ft.Text("Календарь ухода", size=18, weight="bold", color="black"),
                        ft.TextButton(
                            "См. всё", 
                            style=ft.ButtonStyle(color="#009753"),
                            on_click=lambda _: nav("/calendar")
                        )
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    calendar_list,
                    ft.Container(height=10),
                    tabs,
                    active_list_col,
                    archive_list_col,
                    ft.Container(height=100) # технический отступ для корректного отображения за navbar.
                ])
            )
        ]
    )

    view.controls.append(main_content)
    return view