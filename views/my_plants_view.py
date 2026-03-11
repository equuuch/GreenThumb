import flet as ft
from database.session import get_db
from services.plant_services import PlantService

def MyPlantsView(page: ft.Page, nav, user_state):
    view = ft.View()
    view.route = "/my_plants"
    view.bgcolor = "#F9F9F9"
    view.padding = 0 

    user_id = user_state.get("id") or 1

    # 1. ЗАГРУЗКА ВСЕХ РАСТЕНИЙ
    with next(get_db()) as db:
        my_plants = PlantService.get_user_plants(db, user_id)

    # 2. ШАПКА
    header = ft.Container(
        padding=ft.padding.only(left=20, right=20, top=40, bottom=10),
        content=ft.Row(
            controls=[
                ft.IconButton(
                    ft.Icons.ARROW_BACK_IOS_NEW, 
                    icon_size=20, 
                    icon_color="black", 
                    on_click=lambda _: nav("/user_home")
                ),
                ft.Text(
                    value="Мои растения", 
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
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )
    )

    # 3. ФУНКЦИЯ СОЗДАНИЯ КАРТОЧКИ
    def create_plant_card(plant_obj):
        # Путь к фото: если есть в БД — берем из uploads, если нет — ставим заглушку
        img_path = f"uploads/{plant_obj.image_url}" if plant_obj.image_url else "https://images.unsplash.com/photo-1453904300235-0f2f60b15b5d?q=80&w=300"
        
        # Определяем цвет капли на основе статуса
        water_color = "#009753" if plant_obj.status_text == "healthy" else "#D32F2F"

        return ft.Container(
            bgcolor="white",
            border_radius=20,
            shadow=ft.BoxShadow(
                blur_radius=15, 
                color=ft.Colors.with_opacity(0.1, "black"),
                offset=ft.Offset(0, 5)
            ),
            col={"xs": 6, "sm": 6, "md": 3}, # 2 карточки в ряд на мобильных
            # ПЕРЕДАЕМ ID В МАРШРУТ
            on_click=lambda _: nav(f"/my_plant_details/{plant_obj.plant_id}"),
            content=ft.Column(
                spacing=0,
                controls=[
                    # Слой 1: Изображение (сверху без отступов)
                    ft.Container(
                        aspect_ratio=1.0,
                        content=ft.Image(
                            src=img_path,
                            fit=ft.ImageFit.COVER,
                            border_radius=ft.border_radius.only(top_left=20, top_right=20)
                        ),
                    ),
                    # Слой 2: Инфо-блок (с отступами)
                    ft.Container(
                        padding=ft.padding.only(left=12, right=12, bottom=15, top=5),
                        content=ft.Column(
                            spacing=5,
                            controls=[
                                ft.Text(
                                    value=plant_obj.custom_name, 
                                    weight="bold", 
                                    size=15, 
                                    color="black", 
                                    max_lines=1, 
                                    overflow=ft.TextOverflow.ELLIPSIS,
                                    font_family="Montserrat"
                                ),
                                ft.Row([
                                    ft.Icon(ft.Icons.WATER_DROP_OUTLINED, size=16, color=water_color),
                                    ft.Icon(ft.Icons.WB_SUNNY_OUTLINED, size=16, color="#6E6E6E"),
                                    ft.Icon(ft.Icons.FAVORITE_BORDER, size=16, color="red400" if plant_obj.status_text == "healthy" else "grey400"),
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
                    ft.Icon(ft.Icons.SEARCH_OFF, size=50, color="gray"),
                    ft.Text("Список пуст\nНажмите +, чтобы добавить", text_align="center", color="gray", font_family="Montserrat")
                ], horizontal_alignment="center"),
                padding=100, col=12
            )
        )
    else:
        for p in my_plants:
            grid.controls.append(create_plant_card(p))

    # Основной контент с паддингом для сетки
    content_area = ft.Container(padding=20, content=grid)

    view.controls.append(
        ft.ListView(
            controls=[
                header, 
                ft.Container(height=10), 
                content_area
            ], 
            expand=True
        )
    )
    return view