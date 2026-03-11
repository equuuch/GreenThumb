import flet as ft
from database.session import get_db
from database.models import Plant

def MyPlantDetailsView(page: ft.Page, nav, plant_id, user_state):
    view = ft.View()
    view.route = f"/my_plant_details/{plant_id}"
    view.bgcolor = "white"
    view.padding = 0

    with next(get_db()) as db:
        plant = db.query(Plant).filter(Plant.plant_id == plant_id).first()

    if not plant:
        return ft.View(controls=[ft.Text("Растение не найдено")])

    # Функция прогресс-бара
    def create_stat(label, icon, val):
        return ft.Column([
            ft.Row([ft.Icon(icon, size=20, color="#009753"), ft.Text(label, size=14, weight="bold")], spacing=10),
            ft.Container(
                bgcolor="#D0D0D0", height=8, border_radius=4,
                content=ft.Row([ft.Container(bgcolor="#009753", height=8, expand=int(val*10), border_radius=4)], spacing=0)
            ),
            ft.Container(height=10)
        ])

    # 1. ШАПКА
    header = ft.Container(
        padding=ft.padding.only(top=40, left=10, right=10),
        content=ft.Row([
            ft.IconButton(ft.Icons.ARROW_BACK_IOS_NEW, icon_color="black", on_click=lambda _: nav("/my_plants")),
            ft.Text("GreenThumb", weight="bold", size=18, color="black"),
            ft.IconButton(ft.Icons.INFO_OUTLINE, icon_color="black")
        ], alignment="spaceBetween")
    )

    # 2. ФОТО (на весь экран)
    img_path = f"uploads/{plant.image_url}" if plant.image_url else "https://images.unsplash.com/photo-1453904300235-0f2f60b15b5d?q=80&w=300"
    image_box = ft.Container(
        height=400,
        content=ft.Image(src=img_path, fit=ft.ImageFit.COVER)
    )

    # 3. КАРТОЧКА НАЛОЖЕНИЯ
    info_card = ft.Container(
        bgcolor="#E8E8E8",
        padding=30,
        margin=ft.margin.only(top=-50), # Эффект наложения на фото
        border_radius=ft.border_radius.only(top_left=30, top_right=30),
        content=ft.Column([
            ft.Row([
                ft.Text(plant.custom_name, size=26, weight="bold", color="black"),
                ft.Icon(ft.Icons.CIRCLE, color="#009753", size=12)
            ], alignment="spaceBetween"),
            ft.Container(height=20),
            create_stat("Содержание воды", ft.Icons.WATER_DROP_OUTLINED, 0.5),
            create_stat("Уровень освещенности", ft.Icons.WB_SUNNY_OUTLINED, 0.7),
            create_stat("Состояние растения", ft.Icons.FAVORITE_BORDER, 0.4),
        ])
    )

    # 4. СБОРКА
    view.controls.append(
        ft.Stack([
            ft.Column([image_box, info_card]),
            header
        ])
    )
    
    return view