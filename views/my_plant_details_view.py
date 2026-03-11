import flet as ft
from database.session import get_db
from database.models import Plant
from sqlalchemy.orm import joinedload

def MyPlantDetailsView(page: ft.Page, nav, plant_id, user_state):
    view = ft.View()
    view.route = f"/my_plant_details/{plant_id}"
    view.bgcolor = "white"
    view.padding = 0

    # 1. ЗАГРУЗКА ДАННЫХ (с фиксом DetachedInstanceError)
    with next(get_db()) as db:
        plant = db.query(Plant).options(
            joinedload(Plant.catalog_info)
        ).filter(Plant.plant_id == plant_id).first()

    if not plant:
        return ft.View(controls=[ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda _: nav("/my_plants")), ft.Text("Ошибка 404")])

    cat_info = plant.catalog_info
    # Берем данные из каталога, если они есть
    light_val = cat_info.default_light_level if cat_info else 0.5
    water_val = 0.7 # Здесь можно будет добавить логику из PlantService

    # --- ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ДЛЯ ШКАЛ ---
    def create_stat(label, icon, val):
        safe_val = min(10, max(1, int(val * 10)))
        return ft.Column([
            ft.Row([
                ft.Icon(icon, size=18, color="#009753"), 
                ft.Text(label, size=14, weight="w600", color="black", font_family="Montserrat")
            ], spacing=10),
            ft.Container(
                bgcolor="#EBEBEB", 
                height=10, 
                border_radius=5,
                content=ft.Row([
                    ft.Container(bgcolor="#009753", height=10, expand=safe_val, border_radius=5),
                    ft.Container(expand=10-safe_val) 
                ], spacing=0)
            ),
            ft.Container(height=12)
        ])

    # --- ВЕРСТКА ЭКРАНА ---
    img_path = f"uploads/{plant.image_url}" if plant.image_url else "https://images.unsplash.com/photo-1453904300235-0f2f60b15b5d?q=80&w=300"

    # 1. Задний фон (Фото)
    background = ft.Image(
        src=img_path,
        fit=ft.ImageFit.COVER,
        width=page.window.width,
        height=450
    )

    # 2. Кнопки поверх фото
    header_buttons = ft.Container(
        padding=ft.padding.only(top=40, left=15, right=15),
        content=ft.Row([
            ft.IconButton(
                ft.Icons.ARROW_BACK_IOS_NEW, 
                icon_color="black", 
                bgcolor="white70",
                on_click=lambda _: nav("/my_plants")
            ),
            ft.Text("Детали", weight="bold", size=18, color="black", font_family="Montserrat"),
            ft.IconButton(ft.Icons.EDIT_OUTLINED, icon_color="black", bgcolor="white70")
        ], alignment="spaceBetween")
    )

    # 3. Белая плашка с контентом
    content_sheet = ft.Container(
        bgcolor="#F4F4F4",
        padding=ft.padding.all(30),
        border_radius=ft.border_radius.only(top_left=35, top_right=35),
        margin=ft.margin.only(top=-40), # Наползает на фото
        expand=True,
        content=ft.Column([
            # Имя и статус
            ft.Row([
                ft.Text(plant.custom_name, size=28, weight="bold", color="black", font_family="Montserrat"),
                ft.Container(
                    width=12, height=12, bgcolor="#009753", border_radius=6
                )
            ], alignment="spaceBetween"),
            
            ft.Text(cat_info.species_name if cat_info else "Неизвестный вид", size=16, color="grey600", font_family="Montserrat"),
            
            ft.Container(height=25),
            
            # Статистика
            create_stat("Потребность в воде", ft.Icons.WATER_DROP_OUTLINED, water_val),
            create_stat("Требуемый свет", ft.Icons.WB_SUNNY_OUTLINED, light_val),
            create_stat("Здоровье", ft.Icons.FAVORITE_BORDER, 0.9),
            
            ft.Container(height=20),
            
            # Основная кнопка
            ft.ElevatedButton(
                "Отметить полив",
                bgcolor="#009753",
                color="white",
                height=55,
                width=float("inf"),
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=15)),
                on_click=lambda _: print(f"Полив растения {plant.plant_id}")
            )
        ], scroll=ft.ScrollMode.ADAPTIVE)
    )

    view.controls.append(
        ft.ListView([
            ft.Stack([background, header_buttons]),
            content_sheet
        ], expand=True, padding=0)
    )

    return view