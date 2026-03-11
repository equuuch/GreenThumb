import flet as ft
from database.session import get_db
from database.models import PlantCatalog

def ReferenceView(page: ft.Page, nav, catalog_id, user_state):
    view = ft.View()
    view.route = f"/reference/{catalog_id}"
    view.bgcolor = ft.Colors.WHITE
    view.padding = 0 

    # 1. Загрузка данных (используем современный db.get)
    with next(get_db()) as db:
        plant = db.get(PlantCatalog, catalog_id)

    if not plant:
        return ft.View(controls=[ft.Text("Растение не найдено", size=20)])

    # Логика подбора картинки
    name_lower = plant.species_name.lower()
    img_src = "/aloe.png"
    if "роза" in name_lower: img_src = "/rose.png"
    elif "петрушка" in name_lower: img_src = "/petrushka.png"
    elif "гибискус" in name_lower or "gib" in name_lower: img_src = "/gib.png"

    image_header = ft.Container(
        height=280,
        width=page.width,
        border_radius=ft.border_radius.only(bottom_left=35, bottom_right=35),
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        content=ft.Stack([
            ft.Image(src=img_src, width=page.width, height=280, fit=ft.ImageFit.COVER),
            ft.Container(
                content=ft.IconButton(
                    ft.Icons.ARROW_BACK_IOS_NEW, 
                    icon_color="black",
                    icon_size=18,
                    on_click=lambda _: nav("/")
                ),
                left=20, top=40, bgcolor="#CCFFFFFF", border_radius=12, width=40, height=40,
            )
        ])
    )

    def stat_box(icon, label, value):
        return ft.Container(
            padding=15, bgcolor="#F7F9F8", border_radius=20, expand=True,
            content=ft.Column([
                ft.Icon(icon, color="#009753", size=24),
                ft.Text(label, size=12, color="gray"),
                ft.Text(value, weight="bold", size=16, color="black")
            ], horizontal_alignment="center", spacing=2)
        )

    is_guest = user_state["id"] is None
    
    action_btn = ft.ElevatedButton(
        text="Добавить в мой сад" if not is_guest else "Войдите, чтобы добавить",
        bgcolor="#009753" if not is_guest else "#E0E0E0",
        color="white" if not is_guest else "#757575",
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=15)),
        width=float("inf"), height=55,
        on_click=lambda _: nav("/auth") if is_guest else nav("/scanner")
    )

    info_section = ft.Container(
        padding=ft.padding.only(left=25, right=25, top=10, bottom=40),
        content=ft.Column([
            ft.Row([
                ft.Column([
                    ft.Text(plant.species_name, size=28, weight="bold", color="black"),
                    ft.Text(plant.latin_name or "Botanical Name", size=16, italic=True, color="gray"),
                ], expand=True),
                ft.Icon(ft.Icons.INFO_OUTLINE, color="#009753")
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            
            ft.Container(height=10),
            ft.Row([
                stat_box(ft.Icons.WATER_DROP, "Полив", f"{plant.default_watering_interval} дн."),
                stat_box(ft.Icons.WB_SUNNY, "Свет", "Яркий" if (plant.default_light_level or 0) > 0.7 else "Средний"),
            ], spacing=15),
            
            ft.Container(height=15),
            ft.Text("ОПИСАНИЕ", size=13, weight="bold", color="#9E9E9E"), # Убрал letter_spacing
            ft.Text(plant.description or "Описание скоро появится...", color="#424242", size=15),
            
            ft.Container(height=25),
            action_btn
        ], spacing=10)
    )

    view.controls.append(ft.ListView([image_header, info_section], expand=True))
    return view