import flet as ft
from database.session import get_db
from database.models import PlantCatalog
from sqlalchemy import select

def CatalogView(page: ft.Page, nav, user_state):
    # Создаем объект вьюхи с привязкой к роуту
    view = ft.View(
        route="/catalog",
        bgcolor="#F9F9F9",
        padding=0
    )

    # --- Верхняя панель (AppBar) ---
    view.controls.append(
        ft.AppBar(
            title=ft.Text("Справочник растений", size=20, weight="bold"),
            bgcolor="white",
            center_title=False,
            elevation=0, # Плоский дизайн
            leading=ft.IconButton(
                icon=ft.Icons.ARROW_BACK_IOS_NEW_ROUNDED,
                icon_color="black",
                icon_size=18,
                on_click=lambda _: nav("/user_home")
            )
        )
    )

    # Контейнер для списка карточек
    catalog_list = ft.Column(spacing=15, scroll=ft.ScrollMode.ADAPTIVE)

    # Загрузка данных из базы
    with next(get_db()) as db:
        # Получаем все растения из каталога, сортируем по алфавиту
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
                # Создаем карточку растения
                catalog_list.controls.append(
                    ft.Container(
                        bgcolor="white",
                        padding=20,
                        border_radius=20,
                        shadow=ft.BoxShadow(blur_radius=10, color="black10"),
                        ink=True, 
                        # ИСПРАВЛЕНО: ведем на reference_detail, чтобы открылось БЕЗ картинки
                        on_click=lambda e, cid=item.catalog_id: nav(f"/reference_detail/{cid}"),
                        content=ft.Column([
                            ft.Row([
                                ft.Column([
                                    ft.Text(
                                        item.species_name, 
                                        size=18, 
                                        weight="bold", 
                                        color="black"
                                    ),
                                    ft.Text(
                                        item.latin_name if item.latin_name else "", 
                                        size=14, 
                                        italic=True, 
                                        color="grey600"
                                    ),
                                ], expand=True),
                                ft.Icon(ft.Icons.CHEVRON_RIGHT, color="grey400")
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            
                            ft.Divider(height=20, color="#F5F5F5"),
                            
                            ft.Row([
                                # Характеристика: Полив
                                ft.Row([
                                    ft.Icon(ft.Icons.WATER_DROP, size=16, color="#009753"),
                                    ft.Text(f"Раз в {item.default_watering_interval} дн.", size=12)
                                ], spacing=5),
                                # Характеристика: Свет
                                ft.Row([
                                    ft.Icon(ft.Icons.WB_SUNNY, size=16, color="#FFC107"),
                                    ft.Text(f"{int((item.default_light_level or 0) * 100)}% света", size=12)
                                ], spacing=5),
                            ], spacing=20),
                            
                            # Короткое описание (максимум 2 строки)
                            ft.Text(
                                item.description if item.description else "Описание скоро появится",
                                size=13,
                                color="grey700",
                                max_lines=2,
                                overflow=ft.TextOverflow.ELLIPSIS
                            )
                        ], spacing=8)
                    )
                )

    # Добавляем список на страницу с отступами
    view.controls.append(
        ft.Container(
            content=catalog_list,
            padding=20,
            expand=True
        )
    )

    return view