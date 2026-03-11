import flet as ft
from database.session import get_db
from services.plant_services import PlantService

def MyPlantsView(page: ft.Page, nav, user_state):
    view = ft.View()
    view.route = "/my_plants"
    view.bgcolor = "#F9F9F9"
    view.padding = 0 

    user_id = user_state.get("id") or 1

    # 1. ЗАГРУЗКА ДАННЫХ
    with next(get_db()) as db:
        my_plants = PlantService.get_user_plants(db, user_id)

    # 2. ШАПКА ЭКРАНА
    header = ft.Container(
        padding=ft.padding.only(left=20, right=20, top=40, bottom=10),
        content=ft.Row([
            ft.IconButton(
                ft.Icons.ARROW_BACK_IOS_NEW, 
                icon_size=20, 
                icon_color="black", 
                on_click=lambda _: nav("/user_home")
            ),
            ft.Text(
                "Мои растения", 
                size=22, 
                weight="bold", 
                color="black", 
                expand=True, 
                text_align="center", 
                font_family="Montserrat"
            ),
            ft.IconButton(
                ft.Icons.ADD, 
                icon_size=24, 
                icon_color="black", 
                on_click=lambda _: nav("/scanner")
            ),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
    )

    # 3. ФУНКЦИЯ КАРТОЧКИ (С полными параметрами)
    def create_plant_card(plant_obj):
        img_path = f"uploads/{plant_obj.image_url}" if plant_obj.image_url else "https://images.unsplash.com/photo-1453904300235-0f2f60b15b5d?q=80&w=300"
        
        # Цвет капли: зеленый если все ок, красный если засуха
        water_color = "#009753" if plant_obj.status_text == "healthy" else "#D32F2F"

        return ft.Container(
            bgcolor="white", 
            border_radius=25,
            shadow=ft.BoxShadow(
                blur_radius=15, 
                color=ft.Colors.with_opacity(0.1, "black"),
                offset=ft.Offset(0, 5)
            ),
            col={"xs": 6, "sm": 6, "md": 3, "lg": 2}, # Тянется от 2 до 6 в ряд
            on_click=lambda _: nav(f"/my_plant_details/{plant_obj.plant_id}"),
            content=ft.Column(
                spacing=0,
                controls=[
                    # КАРТИНКА (Квадратная через aspect_ratio)
                    ft.Container(
                        aspect_ratio=1.0,
                        content=ft.Image(
                            src=img_path, 
                            fit=ft.ImageFit.COVER, 
                            border_radius=ft.border_radius.only(top_left=25, top_right=25)
                        )
                    ),
                    # ИНФО-БЛОК
                    ft.Container(
                        padding=ft.padding.only(left=15, right=15, top=12, bottom=15),
                        content=ft.Column(
                            spacing=8,
                            controls=[
                                ft.Text(
                                    plant_obj.custom_name, 
                                    weight="bold", 
                                    size=15, 
                                    color="black", 
                                    max_lines=1, 
                                    overflow=ft.TextOverflow.ELLIPSIS,
                                    font_family="Montserrat"
                                ),
                                ft.Row([
                                    ft.Icon(ft.Icons.WATER_DROP_OUTLINED, size=18, color=water_color),
                                    ft.Icon(ft.Icons.WB_SUNNY_OUTLINED, size=18, color="#6E6E6E"),
                                    ft.Icon(ft.Icons.FAVORITE_BORDER, size=18, color="#D32F2F"),
                                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                            ]
                        )
                    )
                ]
            )
        )

    # 4. СЕТКА
    grid = ft.ResponsiveRow(spacing=15, run_spacing=15)
    
    if not my_plants:
        grid.controls.append(
            ft.Container(
                content=ft.Column([
                    ft.Container(height=50),
                    ft.Icon(ft.Icons.SEARCH_OFF, size=80, color="grey300"),
                    ft.Text(
                        "У вас пока нет растений\nНажмите +, чтобы добавить первое!", 
                        text_align="center", 
                        size=16,
                        color="grey500", 
                        font_family="Montserrat"
                    )
                ], horizontal_alignment="center"),
                col=12
            )
        )
    else:
        for p in my_plants:
            grid.controls.append(create_plant_card(p))

    # СБОРКА
    view.controls.append(
        ft.ListView(
            controls=[
                header, 
                ft.Container(padding=ft.padding.all(20), content=grid)
            ], 
            expand=True
        )
    )
    return view