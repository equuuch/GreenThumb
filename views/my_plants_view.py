import flet as ft
from database.session import get_db
from services.plant_services import PlantService

def MyPlantsView(page: ft.Page, nav, user_state):
    view = ft.View()
    view.route = "/my_plants"
    view.bgcolor = "#F9F9F9"
    view.padding = 20

    user_id = user_state.get("id")

    # 1. ЗАГРУЗКА ВСЕХ РАСТЕНИЙ
    with next(get_db()) as db:
        my_plants = PlantService.get_user_plants(db, user_id)

    header = ft.Row(
        controls=[
            ft.IconButton(ft.Icons.ARROW_BACK_IOS_NEW, icon_size=20, icon_color="black", on_click=lambda _: nav("/user_home")),
            ft.Text(value="Мои растения", size=22, weight="bold", color="black", expand=True, text_align="center"),
            ft.IconButton(ft.Icons.ADD, icon_size=24, icon_color="black", on_click=lambda _: nav("/scanner")),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
    )

    def create_plant_card(plant_obj):
        img_path = f"uploads/{plant_obj.image_url}" if plant_obj.image_url else "/aloe.png"
        return ft.Container(
            bgcolor="white", padding=10, border_radius=20,
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.BLACK_12),
            col={"xs": 6, "sm": 6},
            on_click=lambda _: nav("/my_plant_details"),
            content=ft.Column([
                ft.Image(src=img_path, width=150, height=120, fit="cover", border_radius=15),
                ft.Text(value=plant_obj.custom_name, weight="bold", size=14, color="black", max_lines=1),
                ft.Row([
                    ft.Icon(ft.Icons.FAVORITE, size=14, color="#009753"),
                    ft.Text(plant_obj.status_text or "Healthy", size=12, color="gray"),
                ], spacing=5)
            ], spacing=5)
        )

    grid = ft.ResponsiveRow(spacing=15, run_spacing=15)
    
    if not my_plants:
        grid.controls.append(
            ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.SEARCH_OFF, size=50, color="gray"),
                    ft.Text("Список пуст\nНажмите +, чтобы добавить", text_align="center", color="gray")
                ], horizontal_alignment="center"),
                padding=100, col=12
            )
        )
    else:
        for p in my_plants:
            grid.controls.append(create_plant_card(p))

    view.controls.append(ft.ListView([header, ft.Container(height=20), grid], expand=True))
    return view