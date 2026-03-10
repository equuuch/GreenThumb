import flet as ft
import threading # ИМПОРТИРУЕМ ПОТОКИ
from database.session import get_db
from services.plant_services import PlantService
from services.ai_services import GigaChatService

def SearchView(page: ft.Page, nav, query, user_state):
    view = ft.View()
    view.route = f"/search?q={query}"
    view.bgcolor = ft.Colors.WHITE
    view.vertical_alignment = ft.MainAxisAlignment.CENTER
    view.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    status_text = ft.Text(f"Ищем '{query}'...", size=18, weight="bold", color="black")
    progress_bar = ft.ProgressBar(width=250, color="#009753", bgcolor="#EEEEEE")
    ai_hint = ft.Text("Нейросеть GreenThumb анализирует запрос...", size=12, color="gray")

    def run_search_logic():
        ai_service = GigaChatService()
        u_id = user_state["id"] if user_state["id"] else 1

        with next(get_db()) as db:
            try:
                # ВЫЗОВ ТВОЕГО МЕТОДА ИЗ PLANT_SERVICE
                catalog_item, err = PlantService.get_or_create_catalog_item(
                    db, ai_service, u_id, query
                )

                if err:
                    status_text.value = "Ошибка поиска"
                    ai_hint.value = err
                    progress_bar.visible = False
                elif catalog_item:
                    # УСПЕХ: переходим в ТВОЙ красивый справочник по ID
                    nav(f"/reference/{catalog_item.catalog_id}")
            except Exception as ex:
                status_text.value = "Сбой системы"
                ai_hint.value = str(ex)
                progress_bar.visible = False
            
            # Обязательно обновляем страницу из фонового потока
            page.update()

    # Разметка экрана загрузки
    view.controls.append(
        ft.Column([
            ft.Icon(ft.Icons.AUTO_AWESOME, size=60, color="#009753"),
            status_text,
            progress_bar,
            ai_hint,
            ft.TextButton("Отмена", on_click=lambda _: nav("/"))
        ], horizontal_alignment="center", spacing=20)
    )

    # ИСПОЛЬЗУЕМ СТАНДАРТНЫЙ ПОТОК PYTHON ВМЕСТО run_task
    threading.Thread(target=run_search_logic, daemon=True).start()

    return view