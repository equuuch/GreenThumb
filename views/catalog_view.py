import flet as ft
from database.session import get_db
from database.models import PlantCatalog
from sqlalchemy import select

def CatalogView(page: ft.Page, nav, user_state):
    view = ft.View(
        route="/catalog",
        bgcolor="#F5F7F6", # Чуть более "растительный" серый оттенок
        padding=0
    )

    view.controls.append(
        ft.AppBar(
            title=ft.Text("Справочник", size=20, weight="bold", font_family="Manrope"),
            bgcolor="white",
            center_title=True,
            elevation=0,
            leading=ft.IconButton(
                icon=ft.Icons.ARROW_BACK_IOS_NEW_ROUNDED,
                icon_color="black",
                icon_size=18,
                on_click=lambda _: nav("/user_home")
            )
        )
    )

    # Используем GridView для двух колонок
    catalog_grid = ft.GridView(
        expand=True,
        runs_count=2, # 2 колонки
        max_extent=200, # Максимальная ширина одной карточки
        child_aspect_ratio=0.75, # Соотношение сторон (высокая карточка)
        spacing=15,
        run_spacing=15,
    )

    with next(get_db()) as db:
        items = db.scalars(select(PlantCatalog).order_by(PlantCatalog.species_name)).all()

        if not items:
            view.controls.append(
                ft.Container(
                    content=ft.Text("Справочник пуст", color="grey"),
                    alignment=ft.alignment.center, expand=True
                )
            )
        else:
            for item in items:
                # Компактная карточка
                card = ft.Container(
                    bgcolor="white",
                    border_radius=20,
                    padding=12,
                    ink=True,
                    on_click=lambda e, cid=item.catalog_id: nav(f"/reference_detail/{cid}"),
                    shadow=ft.BoxShadow(blur_radius=15, color=ft.Colors.with_opacity(0.05, "black")),
                    content=ft.Column([
                        # Верхняя часть: Иконка или сокращенное название в круге
                        ft.Container(
                            content=ft.Icon(ft.Icons.ECO, color="#009753", size=30),
                            width=50,
                            height=50,
                            bgcolor="#E8F5E9",
                            border_radius=15,
                            alignment=ft.alignment.center,
                        ),
                        
                        ft.Container(height=5),
                        
                        # Названия
                        ft.Text(
                            item.species_name, 
                            size=15, 
                            weight="bold", 
                            max_lines=1, 
                            overflow=ft.TextOverflow.ELLIPSIS
                        ),
                        ft.Text(
                            item.latin_name if item.latin_name else "Plant", 
                            size=11, 
                            italic=True, 
                            color="#9E9E9E",
                            max_lines=1
                        ),
                        
                        ft.Divider(height=10, color="#F5F5F5"),
                        
                        # Компактные характеристики
                        ft.Row([
                            ft.Icon(ft.Icons.WATER_DROP, size=12, color="#009753"),
                            ft.Text(f"{item.default_watering_interval} дн.", size=11, weight="w500"),
                        ], spacing=4),
                        
                        ft.Row([
                            ft.Icon(ft.Icons.WB_SUNNY_ROUNDED, size=12, color="#FFC107"),
                            ft.Text(
                                "Яркий" if (item.default_light_level or 0) > 0.6 else "Тень", 
                                size=11, 
                                weight="w500"
                            ),
                        ], spacing=4),

                    ], spacing=4, horizontal_alignment=ft.CrossAxisAlignment.START)
                )
                catalog_grid.controls.append(card)

    view.controls.append(
        ft.Container(
            content=catalog_grid,
            padding=15,
            expand=True
        )
    )

    return view