import flet as ft
from database.session import get_db
from database.models import PlantCatalog

def ReferenceView(page: ft.Page, nav, catalog_id, user_state):
    # Создаем вьюху и сразу задаем ей роут
    view = ft.View(
        route=f"/reference/{catalog_id}",
        bgcolor="white",
        padding=0
    )

    # 1. Загрузка данных из БД по ID
    with next(get_db()) as db:
        # Пытаемся получить объект из базы по первичному ключу
        plant = db.get(PlantCatalog, int(catalog_id))

    # Если растение не найдено (защита от ошибок)
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

    # Логика подбора локальной картинки по названию
    name_lower = plant.species_name.lower()
    img_src = "/aloe.png" # Картинка по умолчанию
    if "роза" in name_lower: img_src = "/rose.png"
    elif "петрушка" in name_lower: img_src = "/petrushka.png"
    elif "гибискус" in name_lower or "gib" in name_lower: img_src = "/gib.png"

    # Шапка с картинкой и кнопкой назад
    image_header = ft.Container(
        height=320,
        border_radius=ft.border_radius.only(bottom_left=35, bottom_right=35),
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        content=ft.Stack([
            ft.Image(
                src=img_src, 
                fit=ft.ImageFit.COVER, 
                width=1000, 
                height=320
            ),
            # Кнопка возврата
            ft.Container(
                content=ft.IconButton(
                    ft.Icons.ARROW_BACK_IOS_NEW, 
                    icon_color="black",
                    icon_size=18,
                    on_click=lambda _: page.on_view_pop(None) 
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

    # Вспомогательный виджет для карточек с инфой
    def stat_box(icon, label, value):
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

    # Проверка статуса пользователя
    is_guest = user_state.get("id") is None
    
    # Кнопка действия
    action_btn = ft.ElevatedButton(
        text="Добавить в мой сад" if not is_guest else "Войдите, чтобы добавить",
        bgcolor="#009753" if not is_guest else "#E0E0E0",
        color="white" if not is_guest else "#757575",
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=15)),
        width=float("inf"), 
        height=55,
        on_click=lambda _: nav("/auth") if is_guest else nav("/scanner")
    )

    # Текстовая информация
    info_section = ft.Container(
        padding=ft.padding.only(left=25, right=25, top=20, bottom=40),
        content=ft.Column([
            # Названия
            ft.Row([
                ft.Column([
                    ft.Text(plant.species_name, size=28, weight="bold", color="black"),
                    ft.Text(plant.latin_name or "Botanical Name", size=16, italic=True, color="#757575"),
                ], expand=True),
                ft.Icon(ft.Icons.INFO_OUTLINE, color="#009753")
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            
            ft.Container(height=10),
            
            # Ряд с характеристиками
            ft.Row([
                stat_box(ft.Icons.WATER_DROP, "Полив", f"{plant.default_watering_interval} дн."),
                stat_box(ft.Icons.WB_SUNNY, "Свет", "Яркий" if (plant.default_light_level or 0) > 0.7 else "Средний"),
            ], spacing=15),
            
            ft.Container(height=15),
            
            # Секция описания
            ft.Text("ОПИСАНИЕ", size=12, weight="bold", color="#9E9E9E"),
            ft.Text(
                plant.description or "Для этого растения описание пока не добавлено.", 
                color="#424242", 
                size=15,
                # ИСПРАВЛЕНО: используем TextStyle для задания высоты строки
                style=ft.TextStyle(height=1.4) 
            ),
            
            ft.Container(height=25),
            
            # Кнопка
            action_btn
        ], spacing=10)
    )

    # Добавляем всё в список со скроллом
    view.controls.append(
        ft.ListView(
            [image_header, info_section], 
            expand=True,
            spacing=0
        )
    )
    
    return view