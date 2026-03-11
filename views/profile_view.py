import flet as ft
from database.session import SessionLocal
from database.models import User, Plant
from services.plant_services import PlantService
from datetime import datetime

def ProfileView(page: ft.Page, nav, user_state):
    view = ft.View()
    view.route = "/profile"
    view.bgcolor = "#F9F9F9"
    view.padding = 20

    u_id = user_state.get("id", 1)

    # --- ФУНКЦИЯ ВЫХОДА (ЛОГАУТ) ---
    def handle_logout(e):
        # 1. Сбрасываем стейт
        user_state["id"] = None
        user_state["name"] = "Гость"
        # 2. Улетаем на начальный экран (HomeView)
        nav("/")

    # --- ЗАГРУЗКА ДАННЫХ ИЗ БАЗЫ ---
    db = SessionLocal()
    try:
        user_data = db.query(User).filter(User.user_id == u_id).first()
        
        if user_data:
            user_name = user_data.first_name if user_data.first_name and user_data.first_name.strip() else "Илья"
        else:
            user_name = "Илья" 
        
        my_plants = PlantService.get_user_plants(db, u_id)
        plants_count = len(my_plants)
        
        if user_data and hasattr(user_data, 'created_at') and user_data.created_at:
            delta = datetime.now() - user_data.created_at
            days_streak = max(delta.days, 1)
        else:
            days_streak = 1

        bad_status_count = sum(1 for p in my_plants if p.status_text and "полив" in p.status_text.lower())
        health_score = f"{max(100 - (bad_status_count * 20), 0)}%" if plants_count > 0 else "100%"

    except Exception as e:
        print(f"Profile Database Error: {e}")
        user_name = "Илья"
        my_plants, plants_count, days_streak, health_score = [], 0, 1, "—"
    finally:
        db.close()

    # --- UI: ШАПКА ПРОФИЛЯ С КНОПКОЙ ВЫХОДА ---
    profile_header = ft.Container(
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Row([
                            ft.Container(
                                width=70, height=70, border_radius=35, bgcolor="#009753",
                                content=ft.Text(user_name[0].upper(), color="white", size=28, weight="bold"),
                                alignment=ft.alignment.center
                            ),
                            ft.Column([
                                ft.Text(value=user_name, size=22, weight="bold", color="black"),
                                ft.Text(value="Мастер-садовод 🌿", size=14, color="#009753", weight="w500"),
                            ], spacing=2)
                        ], expand=True),
                        # Илья, вот она — кнопка выхода
                        ft.IconButton(
                            icon=ft.Icons.LOGOUT_ROUNDED,
                            icon_color="grey500",
                            tooltip="Выйти из аккаунта",
                            on_click=handle_logout
                        )
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                ),
                ft.Divider(height=30, color="transparent"),
                # Статистика (Растения, Дни, Здоровье)
                ft.Row(
                    controls=[
                        ft.Column([ft.Text(str(plants_count), weight="bold", size=18, color="black"), ft.Text("Растения", size=12, color="gray")], horizontal_alignment="center"),
                        ft.Column([ft.Text(str(days_streak), weight="bold", size=18, color="black"), ft.Text("Дней в Green", size=12, color="gray")], horizontal_alignment="center"),
                        ft.Column([ft.Text(health_score, weight="bold", size=18, color="black"), ft.Text("Здоровье", size=12, color="gray")], horizontal_alignment="center"),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_AROUND
                )
            ]
        ),
        bgcolor="white", padding=25, border_radius=30,
        shadow=ft.BoxShadow(blur_radius=15, color=ft.colors.BLACK12)
    )

    # --- СПИСОК РАСТЕНИЙ (ListView) ---
    plants_list_container = ft.Column(spacing=12)
    if not my_plants:
        plants_list_container.controls.append(
            ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.ENERGY_SAVINGS_LEAF_OUTLINED, size=50, color="grey300"),
                    ft.Text("Тут пока пусто. Добавьте первое растение!", color="grey400", size=14)
                ], horizontal_alignment="center"),
                padding=40, alignment=ft.alignment.center
            )
        )
    else:
        for p in my_plants:
            plants_list_container.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Container(width=50, height=50, border_radius=12, bgcolor="#F0F4F8", 
                                     content=ft.Image(src=p.image_url, fit="cover") if p.image_url else ft.Icon(ft.Icons.ECO, color="#009753")),
                        ft.Column([
                            ft.Text(value=p.custom_name, size=16, weight="bold", color="black"),
                            ft.Text(value=p.status_text or "Всё хорошо", size=12, color="orange700" if p.status_text else "#009753"),
                        ], expand=True, spacing=2),
                        ft.Icon(ft.Icons.CHEVRON_RIGHT, size=20, color="grey400")
                    ], spacing=15),
                    bgcolor="white", padding=16, border_radius=22,
                    on_click=lambda _, pid=p.plant_id: nav(f"/my_plant_details/{pid}")
                )
            )

    view.controls.append(
        ft.ListView(
            expand=True,
            padding=ft.padding.only(bottom=100),
            controls=[
                profile_header,
                ft.Container(height=35),
                ft.Row([ft.Text("Ваша коллекция", size=20, weight="bold", color="black"), ft.Text(f"({plants_count})", color="gray", size=16)], spacing=10),
                ft.Container(height=15),
                plants_list_container
            ]
        )
    )
    return view