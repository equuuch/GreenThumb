import flet as ft
from database.session import SessionLocal
from services.plant_services import PlantService

def UserHomeView(page: ft.Page, nav, user_state):
    view = ft.View()
    view.route = "/user_home"
    view.bgcolor = "#F9F9F9"
    view.padding = 20

    user_name = user_state.get("name", "Шахзод")
    user_id = user_state.get("id", 1)

    db = SessionLocal()
    try:
        my_plants = PlantService.get_user_plants(db, user_id)
    except:
        my_plants = []
    finally:
        db.close()

    header = ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        controls=[
            ft.Column([
                ft.Text(f"Здравствуйте, {user_name}!", size=12, color="#6E6E6E"),
                ft.Text("Ваш сад", size=26, weight="bold", color="black"),
            ], spacing=2),
            ft.IconButton(icon=ft.Icons.NOTIFICATIONS_OUTLINED, icon_color="black")
        ]
    )

    def create_card(p):
        container = ft.Container(
            bgcolor="white", padding=10, border_radius=20,
            col={"xs": 6, "sm": 6},
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.BLACK12),
            # ПЕРЕХОД НА ВКЛАДКУ РАСТЕНИЙ ПО ТВОЕМУ ЗАПРОСУ
            on_click=lambda _: nav("/my_plants") 
        )
        col = ft.Column(spacing=8)
        col.controls.append(ft.Image(src=p.image_url or "/aloe.png", width=150, height=130, fit="cover", border_radius=15))
        col.controls.append(ft.Text(p.custom_name, weight="bold", size=16, color="black"))
        
        h_row = ft.Row(spacing=10)
        h_row.controls.append(ft.Icon(ft.Icons.FAVORITE_BORDER, color="#009753", size=20))
        h_row.controls.append(ft.Container(bgcolor="#009753", height=8, expand=7, border_radius=4))
        h_row.controls.append(ft.Container(bgcolor="#E0E0E0", height=8, expand=3, border_radius=4))
        
        col.controls.append(h_row)
        container.content = col
        return container

    grid = ft.ResponsiveRow(spacing=15)
    for p in my_plants:
        grid.controls.append(create_card(p))

    tasks = ft.Container(
        bgcolor="white", padding=20, border_radius=20,
        shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.BLACK12),
        content=ft.Column([
            ft.Text("Сегодняшние задачи", size=18, weight="bold", color="black"),
            ft.Row([ft.Icon(ft.Icons.WATER_DROP_OUTLINED, color="#009753"), ft.Text("Полить Петрушку", color="black")]),
            ft.Row([ft.Icon(ft.Icons.WB_SUNNY_OUTLINED, color="#009753"), ft.Text("Поставить на свет Алоэ", color="black")]),
        ])
    )

    lv = ft.ListView(expand=True)
    lv.controls.append(header)
    lv.controls.append(ft.Container(height=20))
    lv.controls.append(grid)
    lv.controls.append(ft.Container(height=20))
    lv.controls.append(tasks)

    view.controls.append(lv)
    return view