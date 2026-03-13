import flet as ft
from database.session import get_db
from database.models import PlantCatalog

def HomeView(page: ft.Page, nav):
    """
    модуль реализации главного экрана приложения (landing page).
    обеспечивает первичную навигацию, поиск по каталогу и демонстрацию популярных видов.
    """
    view = ft.View()
    view.route = "/"
    view.bgcolor = "#F9F9F9"
    view.padding = 20
    
    # блок визуальной идентификации: заголовок и краткое описание назначения системы.
    header = ft.Column([
        ft.Text("GreenThumb", size=28, weight="bold", color="#009753"),
        ft.Text("Ваш проводник в мире растений", size=14, color="gray")
    ], spacing=0)

    # компонент текстового ввода для инициации глобального поиска по справочнику.
    # событие on_submit перенаправляет пользователя на маршрут поиска с передачей query-параметра.
    search_field = ft.TextField(
        hint_text="Найти растение (например, Монстера)...",
        border_radius=15, 
        bgcolor="white",
        prefix_icon=ft.Icons.SEARCH,
        border_color="transparent",
        on_submit=lambda e: nav(f"/search?q={e.control.value}")
    )

    def create_card(name, img, cat_id):
        """
        вспомогательная функция формирования карточки растения.
        реализует визуальный паттерн карточки с эффектом тени и скруглением углов.
        """
        return ft.Container(
            bgcolor="white", 
            padding=10, 
            border_radius=25,
            # использование теней для создания глубины интерфейса.
            shadow=ft.BoxShadow(blur_radius=15, color=ft.Colors.BLACK12),
            # настройка колонок для responsiverow: 2 карточки в ряд на мобильных экранах (6/12).
            col={"xs": 6, "sm": 6},
            on_click=lambda _: nav(f"/reference/{cat_id}"),
            content=ft.Column([
                # контейнер для изображения с использованием clip_behavior для обрезки по углам.
                ft.Container(
                    height=120,
                    width=float("inf"),
                    border_radius=15,
                    clip_behavior=ft.ClipBehavior.ANTI_ALIAS, 
                    border=ft.border.all(1, "#EEEEEE"),
                    content=ft.Image(
                        src=img, 
                        fit="cover",
                        # обработка исключений при отсутствии изображения.
                        error_content=ft.Icon(ft.Icons.IMAGE_NOT_SUPPORTED, size=40)
                    ),
                ),
                # текстовый блок карточки с ограничением строк и обработкой переполнения.
                ft.Column([
                    ft.Text(name, weight="bold", size=16, color="black", max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Text("Справочник", size=12, color="#009753")
                ], horizontal_alignment="center", spacing=2)
            ], horizontal_alignment="center", spacing=12)
        )

    # инициализация адаптивной сетки на базе responsiverow.
    grid = ft.ResponsiveRow(spacing=20)

    # прямое взаимодействие с dal (data access layer) через генератор сессий.
    with next(get_db()) as db:
        # выборка первых 4 элементов каталога для отображения в блоке «популярные».
        popular_plants = db.query(PlantCatalog).limit(4).all()
        
        if not popular_plants:
            # логика обработки пустого состояния справочника.
            grid.controls.append(ft.Text("Справочник пока пуст.", color="gray"))
        else:
            # массив доступных статических ассетов для маппинга изображений.
            available_images = ["/aloe.png", "/gib.png", "/rose.png", "/petrushka.png"]
            
            for i, plant in enumerate(popular_plants):
                name_lower = plant.species_name.lower()
                
                # алгоритм сопоставления текстового названия вида с локальным графическим файлом.
                if "алоэ" in name_lower:
                    img_src = "/aloe.png"
                elif "роза" in name_lower:
                    img_src = "/rose.png"
                elif "петрушка" in name_lower:
                    img_src = "/petrushka.png"
                elif "гибискус" in name_lower or "gib" in name_lower:
                    img_src = "/gib.png"
                else:
                    # циклическое распределение картинок по умолчанию при отсутствии точного совпадения.
                    img_src = available_images[i % len(available_images)]
                
                # добавление сформированной карточки в коллекцию сетки.
                grid.controls.append(
                    create_card(plant.species_name, img_src, plant.catalog_id)
                )

    # блок призыва к действию (cta) для неавторизованных пользователей.
    cta_btn = ft.Container(
        content=ft.ElevatedButton(
            "Зарегистрироваться, чтобы создать сад",
            bgcolor="#009753", color="white",
            width=float("inf"), height=50,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=15)),
            on_click=lambda _: nav("/auth?mode=register")
        ),
        margin=ft.margin.only(top=10, bottom=20)
    )

    # компоновка финальной структуры страницы в вертикальный список со скроллом.
    lv = ft.ListView(expand=True, spacing=30)
    lv.controls.extend([
        header, 
        search_field, 
        ft.Text("Популярные растения", size=20, weight="bold", color="black"),
        grid, 
        cta_btn
    ])
    
    # регистрация основного контейнера в списке контроля вьюхи.
    view.controls.append(lv)
    return view