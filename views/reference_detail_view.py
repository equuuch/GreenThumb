import flet as ft
from database.session import get_db
from database.models import PlantCatalog

def ReferenceDetailView(page: ft.Page, nav, catalog_id, user_state):
    """
    модуль детального просмотра записи из глобального ботанического справочника.
    предназначен для ознакомления с характеристиками вида и его последующего добавления в сад.
    """
    # конфигурация вьюхи с использованием стандартного системного компонента appbar.
    view = ft.View(
        route=f"/reference_detail/{catalog_id}",
        bgcolor="white",
        padding=0,
        appbar=ft.AppBar(
            # реализация навигации назад через системный метод page.on_view_pop.
            leading=ft.IconButton(
                ft.Icons.ARROW_BACK_IOS_NEW, 
                icon_size=18,
                on_click=lambda _: page.on_view_pop(None)
            ),
            title=ft.Text("Справочник", size=20, weight="bold"),
            bgcolor="white",
            color="black",
            elevation=0, # удаление тени для соответствия минималистичному дизайну.
            center_title=True
        )
    )

    # 1. этап синхронизации с базой данных (dal).
    with next(get_db()) as db:
        # получение объекта модели по первичному ключу из таблицы plant_catalog.
        plant = db.get(PlantCatalog, int(catalog_id))

    # логическая проверка существования записи (защита от битых ссылок).
    if not plant:
        view.controls.append(ft.Container(content=ft.Text("Растение не найдено"), padding=20))
        return view

    def stat_box(icon, label, value):
        """
        вспомогательный метод (ui factory) для рендеринга блоков характеристик.
        обеспечивает визуальное единообразие параметров полива и освещенности.
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

    # определение статуса пользователя (авторизован/гость) для коррекции логики cta-кнопки.
    is_guest = user_state.get("id") is None
    
    # формирование основного информационного контейнера.
    info_content = ft.Container(
        padding=ft.padding.only(left=25, right=25, top=10, bottom=40),
        content=ft.Column([
            # текстовый блок заголовков (официальное и латинское названия).
            ft.Column([
                ft.Text(plant.species_name, size=28, weight="bold", color="black"),
                ft.Text(plant.latin_name or "Botanical Name", size=16, italic=True, color="#757575"),
            ], spacing=2),
            
            ft.Container(height=15),
            
            # визуализация ключевых параметров ухода в виде горизонтального ряда.
            ft.Row([
                stat_box(ft.Icons.WATER_DROP, "Полив", f"{plant.default_watering_interval} дн."),
                # логическое преобразование числового коэффициента света в текстовое описание.
                stat_box(ft.Icons.WB_SUNNY, "Свет", "Яркий" if (plant.default_light_level or 0) > 0.7 else "Средний"),
            ], spacing=15),
            
            ft.Container(height=20),
            
            # блок ботанического описания с настройкой межстрочного интервала (height) для читаемости.
            ft.Text("ОПИСАНИЕ", size=12, weight="bold", color="#9E9E9E"),
            ft.Text(
                plant.description or "Описание скоро будет добавлено.", 
                color="#424242", 
                size=15,
                style=ft.TextStyle(height=1.4) 
            ),
            
            ft.Container(height=30),
            
            # реактивная кнопка действия. 
            # цвет и текст меняются в зависимости от состояния авторизации пользователя.
            ft.ElevatedButton(
                text="Добавить в мой сад" if not is_guest else "Войдите, чтобы добавить",
                bgcolor="#009753" if not is_guest else "#E0E0E0",
                color="white" if not is_guest else "#757575",
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=15)),
                width=float("inf"), 
                height=55,
                # маршрутизация: гостей — на вход, авторизованных — на экран сканирования.
                on_click=lambda _: nav("/auth") if is_guest else nav("/scanner")
            )
        ], spacing=10)
    )

    # результирующая компоновка: использование listview обеспечивает корректную прокрутку на малых экранах.
    view.controls.append(ft.ListView([info_content], expand=True))
    
    return view