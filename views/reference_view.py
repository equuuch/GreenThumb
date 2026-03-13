import flet as ft
from database.session import get_db
from database.models import PlantCatalog

def ReferenceView(page: ft.Page, nav, catalog_id, user_state):
    """
    модуль детального отображения информации из ботанического справочника.
    реализует логику визуализации эталонных данных вида и адаптивное управление доступом.
    """
    # инициализация объекта вьюхи с привязкой уникального динамического маршрута.
    view = ft.View(
        route=f"/reference/{catalog_id}",
        bgcolor="white",
        padding=0
    )

    # 1. этап взаимодействия с уровнем доступа к данным (dal).
    with next(get_db()) as db:
        # получение объекта растения из глобального каталога по первичному ключу.
        # использование метода get обеспечивает эффективный поиск по индексированному полю.
        plant = db.get(PlantCatalog, int(catalog_id))

    # реализация защитного программирования: обработка случая отсутствия данных в бд.
    if not plant:
        view.controls.append(
            ft.AppBar(title=ft.Text("Ошибка"), bgcolor="white")
        )
        view.controls.append(
            ft.Container(
                content=ft.Text("Растение не найдено в базе", size=20, weight="bold"),
                padding=50, alignment=ft.alignment.center
            )
        )
        return view

    # алгоритм подбора графического контента. 
    # сопоставляет текстовый идентификатор вида с локальными статическими ресурсами.
    name_lower = plant.species_name.lower()
    img_src = "/aloe.png" # ресурс по умолчанию (fallback).
    if "роза" in name_lower: img_src = "/rose.png"
    elif "петрушка" in name_lower: img_src = "/petrushka.png"
    elif "гибискус" in name_lower or "gib" in name_lower: img_src = "/gib.png"

    # формирование графического заголовка. 
    # использование stack позволяет наложить навигационную кнопку поверх изображения.
    image_header = ft.Container(
        height=320,
        border_radius=ft.border_radius.only(bottom_left=35, bottom_right=35),
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS, # обрезка контента по радиусу скругления.
        content=ft.Stack([
            ft.Image(
                src=img_src, 
                fit=ft.ImageFit.COVER, 
                width=1000, 
                height=320
            ),
            # контейнер кнопки возврата с эффектом полупрозрачного фона (стекломорфизм).
            ft.Container(
                content=ft.IconButton(
                    ft.Icons.ARROW_BACK_IOS_NEW, 
                    icon_color="black",
                    icon_size=18,
                    on_click=lambda _: page.on_view_pop(None) # вызов системного метода возврата по стеку.
                ),
                left=20, 
                top=40, 
                bgcolor="#CCFFFFFF", 
                border_radius=12, 
                width=40, 
                height=40,
            )
        ])
    )

    def stat_box(icon, label, value):
        """
        вспомогательный метод построения информационных блоков.
        реализует переиспользование ui-компонентов для визуализации характеристик.
        """
        return ft.Container(
            padding=15, 
            bgcolor="#F7F9F8", 
            border_radius=20, 
            expand=True,
            content=ft.Column([
                ft.Icon(icon, color="#009753", size=24),
                ft.Text(label, size=12, color="#9E9E9E"),
                ft.Text(value, weight="bold", size=16, color="black")
            ], horizontal_alignment="center", spacing=2)
        )

    # проверка состояния авторизации для изменения бизнес-логики кнопки действия.
    is_guest = user_state.get("id") is None
    
    # декларативное описание основной кнопки действия (cta).
    # свойства кнопки (текст, цвет, навигация) зависят от текущего контекста пользователя.
    action_btn = ft.ElevatedButton(
        text="Добавить в мой сад" if not is_guest else "Войдите, чтобы добавить",
        bgcolor="#009753" if not is_guest else "#E0E0E0",
        color="white" if not is_guest else "#757575",
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=15)),
        width=float("inf"), 
        height=55,
        on_click=lambda _: nav("/auth") if is_guest else nav("/scanner")
    )

    # построение информационного блока с текстовым описанием и характеристиками.
    info_section = ft.Container(
        padding=ft.padding.only(left=25, right=25, top=20, bottom=40),
        content=ft.Column([
            # секция заголовков вида.
            ft.Row([
                ft.Column([
                    ft.Text(plant.species_name, size=28, weight="bold", color="black"),
                    ft.Text(plant.latin_name or "Botanical Name", size=16, italic=True, color="#757575"),
                ], expand=True),
                ft.Icon(ft.Icons.INFO_OUTLINE, color="#009753")
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            
            ft.Container(height=10),
            
            # визуализация интервалов полива и требований к свету.
            ft.Row([
                stat_box(ft.Icons.WATER_DROP, "Полив", f"{plant.default_watering_interval} дн."),
                stat_box(ft.Icons.WB_SUNNY, "Свет", "Яркий" if (plant.default_light_level or 0) > 0.7 else "Средний"),
            ], spacing=15),
            
            ft.Container(height=15),
            
            # блок ботанического описания.
            ft.Text("ОПИСАНИЕ", size=12, weight="bold", color="#9E9E9E"),
            ft.Text(
                plant.description or "Для этого растения описание пока не добавлено.", 
                color="#424242", 
                size=15,
                # настройка межстрочного интервала для повышения удобочитаемости текста.
                style=ft.TextStyle(height=1.4) 
            ),
            
            ft.Container(height=25),
            
            # интеграция кнопки в основную колонку.
            action_btn
        ], spacing=10)
    )

    # результирующая сборка вьюхи. 
    # использование listview гарантирует работоспособность интерфейса на экранах с малой высотой.
    view.controls.append(
        ft.ListView(
            [image_header, info_section], 
            expand=True,
            spacing=0
        )
    )
    
    return view