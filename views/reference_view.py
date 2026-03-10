import flet as ft
from database.session import get_db
from database.models import PlantCatalog

def ReferenceView(page: ft.Page, nav, catalog_id, user_state):
    view = ft.View()
    view.route = f"/reference/{catalog_id}"
    view.bgcolor = ft.colors.WHITE
    view.padding = 0 # Для красивой шапки

    # 1. Загрузка данных из эталонного справочника
    with next(get_db()) as db:
        # Используем .get() для поиска по первичному ключу
        plant = db.query(PlantCatalog).get(catalog_id)

    if not plant:
        return ft.View(controls=[ft.Text("Растение не найдено")])

    # Шапка с картинкой (заглушка из assets)
    image_header = ft.Container(
        height=300, bgcolor="#F0F9F4",
        content=ft.Stack([
            ft.Image(src="/aloe.png", width=400, fit="contain", top=40),
            ft.IconButton(
                ft.Icons.ARROW_BACK_IOS_NEW, 
                left=20, top=40, icon_color="black",
                on_click=lambda _: nav("/")
            )
        ])
    )

    # Иконка характеристики (капля, солнце)
    def stat_box(icon, label, value):
        return ft.Container(
            padding=15, bgcolor="#F9F9F9", border_radius=20, expand=True,
            content=ft.Column([
                ft.Icon(icon, color="#009753"),
                ft.Text(label, size=12, color="gray"),
                ft.Text(value, weight="bold", color="black")
            ], horizontal_alignment="center", spacing=2)
        )

    # Кнопка действия (Зависит от того, Гость или Юзер)
    is_guest = user_state["id"] is None
    
    action_btn = ft.Container(
        bgcolor="#009753" if not is_guest else "#E0E0E0",
        padding=15, border_radius=20, alignment=ft.Alignment(0, 0),
        on_click=lambda _: nav("/auth") if is_guest else nav("/scanner"),
        content=ft.Text(
            "Добавить в мой сад" if not is_guest else "Войдите, чтобы добавить",
            color="white" if not is_guest else "gray", weight="bold"
        )
    )

    # Основной контент
    info_section = ft.Container(
        padding=30,
        content=ft.Column([
            ft.Row([
                ft.Column([
                    ft.Text(plant.species_name, size=30, weight="bold", color="black"),
                    ft.Text(plant.latin_name or "Latin Name", italic=True, color="gray"),
                ], expand=True),
                ft.Icon(ft.Icons.INFO_OUTLINE, color="#009753")
            ], alignment="spaceBetween"),
            
            ft.Container(height=10),
            ft.Row([
                stat_box(ft.Icons.WATER_DROP, "Полив", f"{plant.default_watering_interval} дн."),
                stat_box(ft.Icons.WB_SUNNY, "Свет", "Средний"),
            ], spacing=20),
            
            ft.Container(height=10),
            ft.Text("ОПИСАНИЕ", size=14, weight="bold", color="gray"),
            ft.Text(plant.description or "Нет описания", color="black", size=15),
            
            ft.Container(height=20),
            action_btn
        ], spacing=15)
    )

    view.controls.append(ft.ListView([image_header, info_section], expand=True))
    return view