import flet as ft
import threading # использование модуля threading для реализации асинхронного выполнения бизнес-логики.
from database.session import get_db
from services.plant_services import PlantService
from services.ai_services import GigaChatService

def SearchView(page: ft.Page, nav, query, user_state):
    """
    модуль промежуточного интерфейса интеллектуального поиска.
    реализует состояние ожидания (loading state) во время генерации данных нейросетью.
    """
    view = ft.View()
    view.route = f"/search?q={query}"
    view.bgcolor = ft.colors.WHITE
    # центрирование контента для создания фокуса пользователя на процессе загрузки.
    view.vertical_alignment = ft.MainAxisAlignment.CENTER
    view.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    # декларативное описание элементов индикации процесса.
    status_text = ft.Text(f"Ищем '{query}'...", size=18, weight="bold", color="black")
    progress_bar = ft.ProgressBar(width=250, color="#009753", bgcolor="#EEEEEE")
    ai_hint = ft.Text("Нейросеть GreenThumb анализирует запрос...", size=12, color="gray")

    def run_search_logic():
        """
        основной алгоритм поиска, выполняемый в выделенном потоке.
        инкапсулирует вызовы к api и транзакции базы данных.
        """
        ai_service = GigaChatService()
        u_id = user_state["id"] if user_state["id"] else 1

        # инициализация сессии бд внутри фонового потока.
        with next(get_db()) as db:
            try:
                # вызов комплексного метода «умного поиска».
                # если растение отсутствует в локальной бд, инициируется запрос к gigachat 
                # для нормализации названия и генерации технического паспорта вида.
                catalog_item, err = PlantService.get_or_create_catalog_item(
                    db, ai_service, u_id, query
                )

                if err:
                    # реактивное обновление текстовых статусов при возникновении логических ошибок.
                    status_text.value = "Ошибка поиска"
                    ai_hint.value = err
                    progress_bar.visible = False
                elif catalog_item:
                    # при успешном получении/создании записи — переход к экрану детальной информации.
                    # передача идентификатора записи обеспечивает корректную загрузку данных из dal.
                    nav(f"/reference/{catalog_item.catalog_id}")
            except Exception as ex:
                # обработка критических сбоев (сетевые ошибки, ошибки парсинга json).
                status_text.value = "Сбой системы"
                ai_hint.value = str(ex)
                progress_bar.visible = False
            
            # принудительная синхронизация визуального состояния из фонового потока.
            page.update()

    # построение визуальной иерархии экрана загрузки.
    view.controls.append(
        ft.Column([
            # использование иконки нейросети для визуального подтверждения работы интеллектуального модуля.
            ft.Icon(ft.Icons.AUTO_AWESOME, size=60, color="#009753"),
            status_text,
            progress_bar,
            ai_hint,
            ft.TextButton("Отмена", on_click=lambda _: nav("/"))
        ], horizontal_alignment="center", spacing=20)
    )

    # запуск логики поиска в отдельном daemon-потоке. 
    # это гарантирует, что тяжелая операция запроса к ии не заблокирует ui (main thread),
    # позволяя анимации прогресс-бара проигрываться плавно.
    threading.Thread(target=run_search_logic, daemon=True).start()

    return view