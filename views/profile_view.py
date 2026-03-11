import flet as ft
from database.session import SessionLocal
from database.models import User, Plant
from services.plant_services import PlantService
from datetime import datetime

def ProfileView(page: ft.Page, nav, user_state):
    """
    Финальная версия ProfileView: реальные данные из БД, расчет стажа и здоровья.
    """
    view = ft.View()
    view.route = "/profile"
    view.bgcolor = "#F9F9F9"
    view.padding = 20

    # Получаем ID текущего пользователя
    u_id = user_state.get("id", 1)

    # --- ЗАГРУЗКА ДАННЫХ ИЗ БАЗЫ ---
    db = SessionLocal()
    try:
        # Получаем данные пользователя для шапки
        user_data = db.query(User).filter(User.id == u_id).first()
        user_name = user_data.username if user_data else "Садовод"
        
        # Получаем список растений через сервис
        my_plants = PlantService.get_user_plants(db, u_id)
        plants_count = len(my_plants)
        
        # Расчет "Дней в GreenThumb" (стаж)
        if user_data and hasattr(user_data, 'created_at') and user_data.created_at:
            delta = datetime.now() - user_data.created_at
            days_streak = max(delta.days, 1) # Минимум 1 день
        else:
            days_streak = 1

        # Расчет здоровья (имитация логики на основе статусов)
        # Если есть хоть одно растение со статусом "Нужен полив", здоровье падает
        bad_status_count = sum(1 for p in my_plants if p.status_text and "полив" in p.status_text.lower())
        if plants_count > 0:
            health_value = 100 - (bad_status_count * 20)
            health_score = f"{max(health_value, 0)}%"
        else:
            health_score = "—"

    except Exception as e:
        print(f"Profile Database Error: {e}")
        user_name = "User"
        my_plants = []
        plants_count = 0
        days_streak = 0
        health_score = "0%"
    finally:
        db.close()

    # --- UI: ШАПКА ПРОФИЛЯ ---
    profile_header = ft.Container(
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        # Аватар с инициалом
                        ft.Container(
                            width=70, height=70, border_radius=35, bgcolor="#009753",
                            content=ft.Text(
                                user_name[0].upper() if user_name else "U", 
                                color="white", size=28, weight="bold"
                            ),
                            alignment=ft.alignment.center
                        ),
                        ft.Column(
                            controls=[
                                ft.Text(value=user_name, size=22, weight="bold", color="black"),
                                ft.Text(value="Мастер-садовод 🌿", size=14, color="#009753", weight="w500"),
                            ],
                            spacing=2
                        )
                    ],
                    spacing=20
                ),
                ft.Divider(height=30, color="transparent"),
                # Сетка статистики
                ft.Row(
                    controls=[
                        ft.Column([
                            ft.Text(str(plants_count), weight="bold", size=18, color="black"), 
                            ft.Text("Растения", size=12, color="gray")
                        ], horizontal_alignment="center"),
                        ft.Column([
                            ft.Text(str(days_streak), weight="bold", size=18, color="black"), 
                            ft.Text("Дней в Green", size=12, color="gray")
                        ], horizontal_alignment="center"),
                        ft.Column([
                            ft.Text(health_score, weight="bold", size=18, color="black"), 
                            ft.Text("Здоровье", size=12, color="gray")
                        ], horizontal_alignment="center"),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_AROUND
                )
            ]
        ),
        bgcolor="white",
        padding=25,
        border_radius=30,
        shadow=ft.BoxShadow(blur_radius=15, color=ft.colors.BLACK12)
    )

    # --- UI: СПИСОК РАСТЕНИЙ ---
    list_title = ft.Row([
        ft.Text(value="Ваша коллекция", size=20, weight="bold", color="black"),
        ft.Text(value=f"({plants_count})", color="gray", size=16)
    ], alignment=ft.MainAxisAlignment.START, spacing=10)
    
    plants_list = ft.Column(spacing=12)
    
    if not my_plants:
        plants_list.controls.append(
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
            # Определяем иконку или изображение
            img_control = ft.Container(
                width=50, height=50, border_radius=12, bgcolor="#F0F4F8",
                content=ft.Image(src=p.image_url, fit="cover") if p.image_url else ft.Icon(ft.Icons.ECO, color="#009753")
            )
            
            plants_list.controls.append(
                ft.Container(
                    content=ft.Row(
                        controls=[
                            img_control,
                            ft.Column([
                                ft.Text(value=p.custom_name, size=16, weight="bold", color="black"),
                                ft.Text(value=p.status_text or "Всё хорошо", size=12, color="#009753" if not p.status_text else "orange700"),
                            ], expand=True, spacing=2),
                            ft.Icon(ft.Icons.CHEVRON_RIGHT, size=20, color="grey400")
                        ],
                        spacing=15
                    ),
                    bgcolor="white",
                    padding=16,
                    border_radius=22,
                    # Клик передает ID растения в параметры маршрута
                    on_click=lambda _, pid=p.id: nav(f"/analytics?id={pid}")
                )
            )

    # Финальная сборка через ListView для скролла на маленьких экранах
    main_content = ft.ListView(
        expand=True,
        padding=ft.padding.only(bottom=100), # Чтобы нижнее меню не перекрывало список
        controls=[
            profile_header,
            ft.Container(height=35),
            list_title,
            ft.Container(height=15),
            plants_list
        ]
    )

    view.controls.append(main_content)
    return view