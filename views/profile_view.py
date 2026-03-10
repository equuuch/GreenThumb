import flet as ft
from database.session import SessionLocal
from services.plant_services import PlantService

def ProfileView(page: ft.Page, nav, user_state):
    view = ft.View()
    view.route = "/profile"
    view.bgcolor = "#F9F9F9"
    view.padding = 20

    user_name = user_state.get("name", "Шахзод")
    user_id = user_state.get("id", 1)

    # Получаем растения для списка
    db = SessionLocal()
    try:
        my_plants = PlantService.get_user_plants(db, user_id)
    except:
        my_plants = []
    finally:
        db.close()

    # --- ВЕРХНЯЯ ЧАСТЬ (ИНТЕРЕСНАЯ КАРТОЧКА) ---
    profile_header = ft.Container(
        content=ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        # Аватар (заглушка)
                        ft.Container(
                            width=70, height=70, border_radius=35, bgcolor="#009753",
                            content=ft.Icon(ft.Icons.PERSON, color="white", size=40)
                        ),
                        ft.Column(
                            controls=[
                                ft.Text(value=user_name, size=24, weight="bold", color="black"),
                                ft.Text(value="Мастер-садовод 🌿", size=14, color="#009753", weight="w500"),
                            ],
                            spacing=2
                        )
                    ],
                    spacing=20
                ),
                ft.Divider(height=20, color="transparent"),
                # Мини-статистика
                ft.Row(
                    controls=[
                        ft.Column([ft.Text("4", weight="bold", size=18, color="black"), ft.Text("Растения", size=12, color="gray")]),
                        ft.Column([ft.Text("12", weight="bold", size=18, color="black"), ft.Text("Дней серия", size=12, color="gray")]),
                        ft.Column([ft.Text("98%", weight="bold", size=18, color="black"), ft.Text("Здоровье", size=12, color="gray")]),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_AROUND
                )
            ]
        ),
        bgcolor="white",
        padding=25,
        border_radius=30,
        shadow=ft.BoxShadow(blur_radius=15, color=ft.Colors.BLACK12)
    )

    # --- СПИСОК РАСТЕНИЙ ---
    list_title = ft.Text(value="Ваша коллекция", size=20, weight="bold", color="black")
    
    plants_list = ft.Column(spacing=10)
    
    for p in my_plants:
        plants_list.controls.append(
            ft.Container(
                content=ft.Row(
                    controls=[
                        ft.Image(src=p.image_url or "/aloe.png", width=50, height=50, fit="cover", border_radius=10),
                        ft.Text(value=p.custom_name, size=16, weight="w500", color="black", expand=True),
                        ft.Icon(ft.Icons.ARROW_FORWARD_IOS, size=16, color="gray")
                    ],
                    spacing=15
                ),
                bgcolor="white",
                padding=15,
                border_radius=20,
                on_click=lambda _: nav("/analytics") # Клик ведет на график
            )
        )

    # Сборка
    lv = ft.ListView(expand=True)
    lv.controls.append(profile_header)
    lv.controls.append(ft.Container(height=30))
    lv.controls.append(list_title)
    lv.controls.append(ft.Container(height=10))
    lv.controls.append(plants_list)

    view.controls.append(lv)
    return view