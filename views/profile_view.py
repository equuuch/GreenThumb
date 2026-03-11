import flet as ft
from database.session import SessionLocal
from database.models import User, Plant
from sqlalchemy import desc
from datetime import datetime

def ProfileView(page: ft.Page, nav, user_state):
    view = ft.View()
    view.route = "/profile"
    view.bgcolor = "#F9F9F9"
    view.padding = 0 # Убираем общий паддинг, сделаем его внутри

    u_id = user_state.get("id", 1)

    # --- ФУНКЦИЯ ВОССТАНОВЛЕНИЯ ИЗ АРХИВА ---
    def restore_plant(e, plant_id):
        db = SessionLocal()
        try:
            plant = db.query(Plant).filter(Plant.plant_id == plant_id).first()
            if plant:
                plant.is_active = True
                db.commit()
                # Явный редирект для обновления данных
                page.go("/user_home") # Сначала на главную, чтобы увидеть результат
        finally:
            db.close()

    def handle_logout(e):
        user_state["id"] = None
        user_state["name"] = "Гость"
        page.go("/")

    # --- ЗАГРУЗКА ДАННЫХ ---
    db = SessionLocal()
    try:
        user_data = db.query(User).filter(User.user_id == u_id).first()
        user_name = user_data.first_name if user_data and user_data.first_name else "Илья"
        
        all_plants = db.query(Plant).filter(Plant.user_id == u_id).order_by(desc(Plant.added_at)).all()
        active_plants = [p for p in all_plants if p.is_active]
        archived_plants = [p for p in all_plants if not p.is_active]
        
        plants_count = len(active_plants)
        days_streak = (datetime.now() - user_data.created_at).days + 1 if user_data and user_data.created_at else 1
    finally:
        db.close()

    # --- UI ЭЛЕМЕНТЫ ---
    profile_header = ft.Container(
        padding=25,
        bgcolor="white",
        border_radius=ft.border_radius.only(bottom_left=30, bottom_right=30),
        shadow=ft.BoxShadow(blur_radius=15, color=ft.Colors.BLACK12),
        content=ft.Column([
            ft.Row([
                ft.Row([
                    ft.Container(
                        width=60, height=60, border_radius=30, bgcolor="#009753",
                        content=ft.Text(user_name[0].upper(), color="white", weight="bold"),
                        alignment=ft.alignment.center
                    ),
                    ft.Column([
                        ft.Text(user_name, size=20, weight="bold", color="black"),
                        ft.Text("Мастер-садовод 🌿", size=13, color="#009753"),
                    ], spacing=0)
                ], expand=True),
                ft.IconButton(ft.Icons.LOGOUT_ROUNDED, on_click=handle_logout)
            ]),
            ft.Divider(height=20, color="transparent"),
            ft.Row([
                ft.Column([ft.Text(str(plants_count), weight="bold"), ft.Text("Растения", size=12)], horizontal_alignment="center"),
                ft.Column([ft.Text(str(days_streak), weight="bold"), ft.Text("Дней", size=12)], horizontal_alignment="center"),
                ft.Column([ft.Text("100%", weight="bold"), ft.Text("Здоровье", size=12)], horizontal_alignment="center"),
            ], alignment=ft.MainAxisAlignment.SPACE_AROUND)
        ])
    )

    active_list = ft.Column(spacing=10)
    archive_list = ft.Column(spacing=10, visible=False)

    def create_row(p, is_arc):
        return ft.Container(
            bgcolor="white", padding=15, border_radius=20,
            content=ft.Row([
                ft.Image(src=f"assets/{p.image_url}" if p.image_url else None, width=50, height=50, fit="cover", border_radius=10),
                ft.Column([
                    ft.Text(p.custom_name, weight="bold"),
                    ft.Text("В архиве" if is_arc else "Активно", size=12, color="grey")
                ], expand=True),
                ft.IconButton(ft.Icons.UNARCHIVE, icon_color="#009753", on_click=lambda e: restore_plant(e, p.plant_id)) if is_arc 
                else ft.Icon(ft.Icons.CHEVRON_RIGHT, color="grey")
            ]),
            on_click=None if is_arc else lambda _: nav(f"/my_plant_details/{p.plant_id}")
        )

    for p in active_plants: active_list.controls.append(create_row(p, False))
    for p in archived_plants: archive_list.controls.append(create_row(p, True))

    def change_tab(e):
        active_list.visible = (e.control.selected_index == 0)
        archive_list.visible = (e.control.selected_index == 1)
        page.update()

    tabs = ft.Tabs(selected_index=0, on_change=change_tab, tabs=[ft.Tab(text="Активные"), ft.Tab(text="Архив")])

    # Основной контент скроллится здесь
    content_scroll = ft.Column(
        scroll=ft.ScrollMode.ADAPTIVE,
        expand=True,
        controls=[
            profile_header,
            ft.Container(padding=20, content=ft.Column([
                tabs,
                ft.Container(height=10),
                active_list,
                archive_list
            ]))
        ]
    )

    view.controls.append(content_scroll)
    return view