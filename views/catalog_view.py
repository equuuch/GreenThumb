import flet as ft
from database.session import get_db
from database.models import PlantCatalog
from sqlalchemy import select
from services.plant_services import PlantService
from services.ai_services import GigaChatService  # Твоя структура папок

def CatalogView(page: ft.Page, nav, user_state):
    # 1. Инициализация
    ai_service = GigaChatService()
    user_id = user_state.get("id")
    
    view = ft.View(
        route="/catalog",
        bgcolor="#F5F7F6",
        padding=0
    )

    # 2. Объявление UI-компонентов (СНАЧАЛА объявляем, чтобы избежать ошибок "not defined")
    
    # Сетка карточек
    catalog_grid = ft.GridView(
        expand=True,
        runs_count=2,
        max_extent=200,
        child_aspect_ratio=0.75,
        spacing=15,
        run_spacing=15,
    )

    # Поле поиска (нужно объявить заранее, так как оно используется в функциях)
    search_field = ft.TextField(
        hint_text="Найти растение...",
        expand=True,
        border_radius=15,
        bgcolor="#F0F2F1",
        border_color="transparent",
        height=45,
        content_padding=ft.padding.only(left=15),
        on_change=lambda e: load_catalog(e.control.value),
    )

    # Состояние "Пусто" / Кнопка для поиска через ИИ
    empty_state = ft.Column([
        ft.Container(height=40),
        ft.Icon(ft.Icons.SEARCH_OFF_ROUNDED, size=50, color="grey"),
        ft.Text("Ничего не нашли в базе?", color="grey", text_align="center"),
        ft.ElevatedButton(
            "Найти и добавить через ИИ",
            icon=ft.Icons.AUTO_AWESOME,
            on_click=lambda _: run_ai_search(),
            style=ft.ButtonStyle(bgcolor="#009753", color="white")
        )
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, visible=False)

    # --- ЛОГИКА ---

    def create_card(item):
        """Создает карточку растения"""
        return ft.Container(
            bgcolor="white",
            border_radius=20,
            padding=12,
            ink=True,
            on_click=lambda e, cid=item.catalog_id: nav(f"/reference_detail/{cid}"),
            shadow=ft.BoxShadow(blur_radius=15, color=ft.Colors.with_opacity(0.05, "black")),
            content=ft.Column([
                ft.Container(
                    content=ft.Icon(ft.Icons.ECO, color="#009753", size=30),
                    width=50, height=50, bgcolor="#E8F5E9", border_radius=15, alignment=ft.alignment.center,
                ),
                ft.Container(height=5),
                ft.Text(item.species_name, size=14, weight="bold", max_lines=1, overflow="ellipsis"),
                ft.Text(item.latin_name or "Plant", size=11, italic=True, color="#9E9E9E"),
                ft.Divider(height=10, color="#F5F5F5"),
                ft.Row([
                    ft.Icon(ft.Icons.WATER_DROP, size=12, color="#009753"),
                    ft.Text(f"{item.default_watering_interval} дн.", size=11),
                ], spacing=4),
            ], spacing=4)
        )

    def load_catalog(query=""):
        """Загрузка и фильтрация списка из локальной БД"""
        catalog_grid.controls.clear()
        with next(get_db()) as db:
            stmt = select(PlantCatalog).order_by(PlantCatalog.species_name)
            items = db.scalars(stmt).all()
            
            filtered = [i for i in items if query.lower() in i.species_name.lower()]
            
            for item in filtered:
                catalog_grid.controls.append(create_card(item))
            
            # Если поиск не дал результатов, показываем кнопку поиска через ИИ
            empty_state.visible = len(catalog_grid.controls) == 0
        page.update()

    def run_ai_search():
        """Поиск через GigaChat и автоматическое добавление в каталог"""
        search_val = search_field.value.strip()
        if not search_val: return

        # Визуальный отклик
        search_field.disabled = True
        page.snack_bar = ft.SnackBar(
            content=ft.Row([ft.ProgressRing(width=20, height=20), ft.Text(" ИИ ищет информацию...")]),
            open=True
        )
        page.update()

        with next(get_db()) as db:
            # Используем твою бизнес-логику из PlantService
            item, err = PlantService.get_or_create_catalog_item(db, ai_service, user_id, search_val)
            
            if err:
                page.snack_bar = ft.SnackBar(ft.Text(f"❌ {err}"), bgcolor="red", open=True)
            else:
                page.snack_bar = ft.SnackBar(
                    ft.Text(f"✅ {item.species_name} добавлен в справочник!"), 
                    bgcolor="#009753", 
                    open=True
                )
                search_field.value = ""
                load_catalog() # Обновляем сетку

        search_field.disabled = False
        page.update()

    # --- СБОРКА VIEW ---

    # Назначаем действие на Enter в поле поиска
    search_field.on_submit = lambda _: run_ai_search()

    view.controls.extend([
        ft.AppBar(
            title=ft.Text("Справочник", size=20, weight="bold"),
            bgcolor="white",
            center_title=True,
            leading=ft.IconButton(
                icon=ft.Icons.ARROW_BACK_IOS_NEW_ROUNDED,
                on_click=lambda _: nav("/user_home")
            )
        ),
        ft.Container(
            padding=20,
            bgcolor="white",
            content=ft.Row([
                search_field,
                ft.IconButton(
                    icon=ft.Icons.AUTO_AWESOME,
                    icon_color="#009753",
                    tooltip="Найти через ИИ",
                    on_click=lambda _: run_ai_search()
                )
            ])
        ),
        ft.Container(
            content=ft.Column([
                empty_state,
                catalog_grid
            ], scroll=ft.ScrollMode.ADAPTIVE),
            padding=15, 
            expand=True
        )
    ])

    # Первоначальный запуск
    load_catalog()

    return view