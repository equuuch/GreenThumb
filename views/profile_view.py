import flet as ft
from database.session import SessionLocal
from database.models import User, Plant, CareCalendar
from services.care_service import CareService
from sqlalchemy import desc, asc
from sqlalchemy.orm import joinedload
from datetime import datetime, date

def ProfileView(page: ft.Page, nav, user_state):
    view = ft.View()
    view.route = "/profile"
    view.bgcolor = "#F9F9F9"
    view.padding = 0

    u_id = user_state.get("id", 1)

    # --- ОБРАБОТЧИКИ СОБЫТИЙ ---
    def handle_logout(e):
        user_state["id"] = None
        user_state["name"] = "Гость"
        page.go("/")

    def handle_complete_task(e, task_id):
        db = SessionLocal()
        try:
            new_task, error = CareService.complete_task(db, task_id)
            if not error:
                page.go("/profile") 
            else:
                print(f"Ошибка при выполнении задачи: {error}")
        finally:
            db.close()

    def restore_from_archive(e, plant_id):
        db = SessionLocal()
        try:
            plant = db.query(Plant).filter(Plant.plant_id == plant_id).first()
            if plant:
                plant.is_active = True
                db.commit()
                CareService.generate_full_schedule(db, plant_id)
                page.go("/user_home") 
        finally:
            db.close()

    # --- ЗАГРУЗКА ДАННЫХ ---
    db = SessionLocal()
    try:
        user_data = db.query(User).filter(User.user_id == u_id).first()
        user_name = user_data.first_name if user_data and user_data.first_name else "Пользователь"
        
        all_plants = db.query(Plant).filter(Plant.user_id == u_id).order_by(desc(Plant.added_at)).all()
        active_plants = [p for p in all_plants if p.is_active]
        archived_plants = [p for p in all_plants if not p.is_active]
        
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
        
        plants_count = len(active_plants)
        days_streak = (datetime.now() - user_data.created_at).days + 1 if user_data and user_data.created_at else 1
    finally:
        db.close()

    # --- UI: ШАПКА ПРОФИЛЯ ---
    def stat_column(label, value):
        return ft.Container(
            content=ft.Column([
                ft.Text(str(value), weight="bold", size=16, color="black"),
                ft.Text(label, size=12, color="grey")
            ], horizontal_alignment="center"),
            on_click=lambda _: nav("/analytics"),
            padding=10,
            border_radius=10,
            ink=True # Эффект нажатия
        )

    profile_header = ft.Container(
        padding=25, bgcolor="white",
        border_radius=ft.border_radius.only(bottom_left=30, bottom_right=30),
        shadow=ft.BoxShadow(blur_radius=15, color=ft.Colors.BLACK12),
        content=ft.Column([
            ft.Row([
                ft.Row([
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
            ft.Row([
                stat_column("Растения", plants_count),
                stat_column("Дней", days_streak),
                stat_column("Здоровье", "100%"),
            ], alignment=ft.MainAxisAlignment.SPACE_AROUND)
        ])
    )

    # --- UI: КАЛЕНДАРЬ УХОДА ---
    calendar_list = ft.Column(spacing=10)
    if not tasks:
        calendar_list.controls.append(ft.Text("На сегодня задач нет ✨", size=13, color="grey", italic=True))
    else:
        for t in tasks:
            is_today = t.scheduled_date <= date.today()
            p_name = t.plant.custom_name if t.plant else "Растение"
            calendar_list.controls.append(
                ft.Container(
                    bgcolor="#F0F4F8" if not is_today else "#E8F5E9",
                    padding=15, border_radius=20,
                    content=ft.Row([
                        ft.Icon(ft.Icons.WATER_DROP, color="#009753" if is_today else "grey700", size=20),
                        ft.Column([
                            ft.Text(p_name, weight="bold", size=14, color="black"),
                            ft.Text("Нужно полить" if is_today else f"Полив {t.scheduled_date.strftime('%d.%m')}", size=12, color="grey700")
                        ], expand=True, spacing=0),
                        ft.IconButton(
                            icon=ft.Icons.CHECK_CIRCLE_OUTLINE, 
                            icon_color="#009753",
                            on_click=lambda e, tid=t.calendar_id: handle_complete_task(e, tid)
                        )
                    ])
                )
            )

    # --- UI: СПИСКИ И АРХИВ ---
    active_list_col = ft.Column(spacing=12, visible=True)
    archive_list_col = ft.Column(spacing=12, visible=False)

    def create_plant_card(p, is_arc):
        p_img = p.image_url.replace("\\", "/") if p.image_url else None
        return ft.Container(
            bgcolor="white", padding=15, border_radius=22,
            shadow=ft.BoxShadow(blur_radius=5, color=ft.Colors.BLACK12),
            content=ft.Row([
                ft.Image(src=f"assets/{p_img}" if p_img else "assets/aloe.png", width=50, height=50, fit="cover", border_radius=12),
                ft.Column([
                    ft.Text(p.custom_name, weight="bold", color="black", size=15),
                    ft.Text("В архиве" if is_arc else (p.status_text or "Здорово"), size=12, color="grey")
                ], expand=True, spacing=2),
                ft.IconButton(ft.Icons.UNARCHIVE_ROUNDED, icon_color="#009753", on_click=lambda e: restore_from_archive(e, p.plant_id)) if is_arc else ft.Icon(ft.Icons.CHEVRON_RIGHT, color="grey400")
            ]),
            on_click=None if is_arc else lambda _: nav(f"/my_plant_details/{p.plant_id}")
        )

    for p in active_plants: active_list_col.controls.append(create_plant_card(p, False))
    for p in archived_plants: archive_list_col.controls.append(create_plant_card(p, True))

    def on_tab_change(e):
        active_list_col.visible = (e.control.selected_index == 0)
        archive_list_col.visible = (e.control.selected_index == 1)
        view.update()

    tabs = ft.Tabs(selected_index=0, on_change=on_tab_change, tabs=[ft.Tab(text="Мой сад"), ft.Tab(text="Архив")])

    # --- СБОРКА КОНТЕНТА ---
    main_content = ft.Column(
        scroll=ft.ScrollMode.ADAPTIVE,
        expand=True,
        controls=[
            profile_header,
            ft.Container(
                padding=20,
                content=ft.Column([
                    # ИСПРАВЛЕННЫЙ БЛОК АНАЛИТИКИ (Container вместо прямого ListTile)
                    ft.Container(
                        content=ft.ListTile(
                            leading=ft.Icon(ft.Icons.INSERT_CHART_ROUNDED, color="#009753"),
                            title=ft.Text("Аналитика и графики роста", weight="bold"),
                            subtitle=ft.Text("Посмотрите, как развиваются ваши растения"),
                            on_click=lambda _: nav("/analytics"),
                        ),
                        bgcolor="white",
                        border_radius=15,
                        shadow=ft.BoxShadow(blur_radius=5, color=ft.Colors.BLACK12),
                    ),
                    ft.Container(height=10),
                    ft.Row([
                        ft.Text("Календарь ухода", size=18, weight="bold", color="black"),
                        ft.TextButton("См. всё", on_click=lambda _: nav("/calendar"))
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    calendar_list,
                    ft.Container(height=10),
                    tabs,
                    active_list_col,
                    archive_list_col,
                    ft.Container(height=100) 
                ])
            )
        ]
    )

    view.controls.append(main_content)
    return view