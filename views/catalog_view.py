import flet as ft
from database.session import get_db
from database.models import PlantCatalog
from sqlalchemy import select
from services.plant_services import PlantService
from services.ai_services import GigaChatService

def CatalogView(page: ft.Page, nav, user_state):
    """
    модуль визуализации ботанического справочника.
    реализует механизмы локального поиска и динамического расширения базы знаний через ии.
    """
    # 1. инициализация сервисного слоя для работы с нейросетью и идентификация сессии.
    ai_service = GigaChatService()
    user_id = user_state.get("id")
    
    view = ft.View(
        route="/catalog",
        bgcolor="#F5F7F6",
        padding=0
    )

    # --- описание ui-компонентов ---

    # адаптивная сетка (gridview) для отображения карточек растений. 
    # автоматически пересчитывает количество колонок в зависимости от ширины экрана.
    catalog_grid = ft.GridView(
        expand=True,
        runs_count=2,
        max_extent=200,
        child_aspect_ratio=0.75,
        spacing=15,
        run_spacing=15,
    )

    # декларативное описание состояния «пустой выдачи».
    # содержит призыв к действию (cta) для инициирования поиска через нейросеть.
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

    # компонент текстового ввода для реализации «живого» поиска по локальной базе.
    search_field = ft.TextField(
        hint_text="Найти растение...",
        expand=True,
        border_radius=15,
        bgcolor="#F0F2F1",
        border_color="transparent",
        height=45,
        content_padding=ft.padding.only(left=15),
        # триггер реактивного обновления списка при каждом изменении текста.
        on_change=lambda e: load_catalog(e.control.value),
    )

    # --- блок программной логики ---

    def create_card(item):
        """
        фабрика визуальных компонентов карточек.
        преобразует объект модели sqlalchemy в интерактивный контейнер flet.
        """
        return ft.Container(
            bgcolor="white",
            border_radius=20,
            padding=12,
            ink=True, # включение эффекта «чернильного пятна» при нажатии.
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
        """
        алгоритм выборки и фильтрации данных. 
        взаимодействует с базой данных sqlite через orm-запросы.
        """
        catalog_grid.controls.clear()
        with next(get_db()) as db:
            # выполнение структурированного запроса с сортировкой по названию.
            stmt = select(PlantCatalog).order_by(PlantCatalog.species_name)
            items = db.scalars(stmt).all()
            
            # реализация клиентской фильтрации по вхождению подстроки.
            filtered = [i for i in items if query.lower() in i.species_name.lower()]
            
            for item in filtered:
                catalog_grid.controls.append(create_card(item))
            
            # реактивное управление видимостью состояния «пусто».
            empty_state.visible = len(catalog_grid.controls) == 0
        
        if page:
            page.update() # принудительная синхронизация ui.

    def show_msg(text, is_error=False):
        """метод вывода системных оповещений."""
        snack = ft.SnackBar(
            content=ft.Text(text),
            bgcolor="red" if is_error else "#009753",
        )
        page.overlay.append(snack)
        snack.open = True
        page.update()

    def run_ai_search():
        """
        интеграционный алгоритм взаимодействия с gigachat api.
        отвечает за генерацию технического паспорта растения и автоматическое внесение в бд.
        """
        search_val = search_field.value.strip()
        if not search_val: return

        # визуальная блокировка интерфейса для предотвращения race condition.
        search_field.disabled = True
        search_field.update()
        
        # отображение индикатора выполнения длительной сетевой операции.
        loading_snack = ft.SnackBar(
            content=ft.Row([ft.ProgressRing(width=20, height=20), ft.Text(" ИИ ищет информацию...")]),
            open=True
        )
        page.overlay.append(loading_snack)
        page.update()

        try:
            with next(get_db()) as db:
                # вызов метода сервисного слоя, инкапсулирующего логику промптов и парсинга json.
                item, err = PlantService.get_or_create_catalog_item(db, ai_service, user_id, search_val)
                
                # принудительная фиксация транзакции для записи нового вида в глобальный справочник.
                db.commit()

                if err:
                    loading_snack.open = False
                    show_msg(f"❌ {err}", is_error=True)
                else:
                    loading_snack.open = False
                    show_msg(f"✅ {item.species_name} добавлен в справочник!")
                    search_field.value = ""
                    # актуализация списка для отображения новой записи без перезагрузки страницы.
                    load_catalog() 

        except Exception as ex:
            show_msg(f"Ошибка: {str(ex)}", is_error=True)
        finally:
            # возврат интерфейса в интерактивное состояние.
            search_field.disabled = False
            page.update()

    # --- сборка иерархии вьюхи ---

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
        # контейнер поисковой панели.
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
        # основной контейнер данных с поддержкой адаптивного скролла.
        ft.Container(
            content=ft.Column([
                empty_state,
                catalog_grid
            ], scroll=ft.ScrollMode.ADAPTIVE),
            padding=15, 
            expand=True
        )
    ])

    # первичная загрузка данных при инициализации модуля.
    load_catalog()

    return view