import flet as ft
from database.session import get_db
from database.models import PlantCatalog
from sqlalchemy import select

def CatalogView(page: ft.Page, nav, user_state):
    view = ft.View()
    view.route = "/catalog"
    view.bgcolor = "#F9F9F9"
    view.padding = 0

    # --- AppBar с черной кнопкой назад ---
    view.controls.append(
        ft.AppBar(
            title=ft.Text("Справочник растений", size=20, weight="bold"),
            bgcolor="white",
            center_title=False,
            leading=ft.IconButton(
                icon=ft.Icons.ARROW_BACK_IOS_NEW_ROUNDED,
                icon_color="black",
                on_click=lambda _: nav("/user_home")
            )
        )
    )

    # Контейнер для списка
    catalog_list = ft.Column(spacing=15, scroll=ft.ScrollMode.ADAPTIVE)

    # 1. ЗАГРУЗКА ДАННЫХ ИЗ КАТАЛОГА
    with next(get_db()) as db:
        items = db.scalars(select(PlantCatalog).order_by(PlantCatalog.species_name)).all()

        if not items:
            catalog_list.controls.append(
                ft.Container(
                    content=ft.Text("Справочник пока пуст", color="grey", size=16),
                    alignment=ft.alignment.center,
                    padding=50
                )
            )
        else:
            for item in items:
                catalog_list.controls.append(
                    ft.Container(
                        bgcolor="white",
                        padding=20,
                        border_radius=20,
                        shadow=ft.BoxShadow(blur_radius=10, color="black10"),
                        content=ft.Column([
                            ft.Row([
                                ft.Column([
                                    ft.Text(item.species_name, size=18, weight="bold", color="black"),
                                    ft.Text(item.latin_name if item.latin_name else "", 
                                            size=14, italic=True, color="grey600"),
                                ], expand=True),
                                ft.Icon(ft.Icons.CHEVRON_RIGHT, color="grey400")
                            ], alignment="spaceBetween"),
                            
                            ft.Divider(height=20, color="#F5F5F5"),
                            
                            ft.Row([
                                # Краткие статы из дефолтных настроек каталога
                                ft.Row([
                                    ft.Icon(ft.Icons.WATER_DROP, size=16, color="#009753"),
                                    ft.Text(f"Раз в {item.default_watering_interval} дн.", size=12)
                                ], spacing=5),
                                ft.Row([
                                    ft.Icon(ft.Icons.WB_SUNNY, size=16, color="#FFC107"),
                                    ft.Text(f"{int(item.default_light_level * 100)}% света", size=12)
                                ], spacing=5),
                            ], spacing=20),
                            
                            ft.Text(
                                item.description if item.description else "Описание отсутствует",
                                size=13,
                                color="grey700",
                                max_lines=2,
                                overflow=ft.TextOverflow.ELLIPSIS
                            )
                        ], spacing=8),
                        on_click=lambda _: print(f"Клик по {item.species_name}") # Тут можно сделать детальный вид вида
                    )
                )

    # Обертка для отступов
    view.controls.append(
        ft.Container(
            content=catalog_list,
            padding=20,
            expand=True
        )
    )

    return view