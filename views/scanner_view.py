import flet as ft
import threading
import base64
import urllib3
import json
import os
from sqlalchemy.orm import joinedload
from database.session import get_db
from database.models import Plant, PlantCatalog
from services.ai_services import GigaChatService

# Отключаем предупреждения SSL для работы с GigaChat
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def ScannerView(page: ft.Page, nav, user_state, global_picker=None):
    """
    Версия 4.0: ПОЛНАЯ УНИВЕРСАЛЬНАЯ ВЕРСИЯ (WEB + DESKTOP)
    - Исправлен AttributeError: 'FilePickerFile' object has no attribute 'content'
    - Реализован механизм автоматического Upload для Web (-w)
    - Полная интеграция с базой данных и GigaChat
    - Поддержка assets/plants для вывода фото
    """

    # --- СОСТОЯНИЕ И СЕРВИСЫ ---
    ai_service = GigaChatService()
    
    ui_state = {
        "image_bytes": None,
        "chat_image_pending": None,
        "current_plant_info": "Общий вопрос по садоводству",
        "chat_messages": [],
        "is_sending": False,
        "selected_light_raw": 50,
        "active_plant_id": None
    }

    # --- ЛОГИКА ОБРАБОТКИ ФАЙЛОВ (WEB FIX) ---

    def process_picked_file(picked_file):
        """Универсальное чтение байтов"""
        # 1. Проверяем путь (Desktop)
        if hasattr(picked_file, "path") and picked_file.path:
            with open(picked_file.path, "rb") as f:
                return f.read()
        
        # 2. Проверяем наличие content (Web, если передан напрямую)
        content = getattr(picked_file, "content", None)
        if content:
            return content

        # 3. Если мы в Вебе и пути/контента нет, файл нужно искать в assets/uploads (после upload)
        upload_path = os.path.join("assets", "uploads", picked_file.name)
        if os.path.exists(upload_path):
            with open(upload_path, "rb") as f:
                return f.read()
                
        return None

    def on_upload_progress(e: ft.FilePickerUploadEvent):
        """Срабатывает, когда файл физически долетел до сервера в assets/uploads"""
        if e.status == "completed":
            # Ищем файл в папке загрузок по имени
            upload_path = os.path.join("assets", "uploads", e.file_name)
            if os.path.exists(upload_path):
                with open(upload_path, "rb") as f:
                    ui_state["image_bytes"] = f.read()
                
                # Обновляем превью
                main_img_view.src_base64 = base64.b64encode(ui_state["image_bytes"]).decode("utf-8")
                image_preview_card.visible = True
                instruction_container.visible = False
                
                if choice_dialog not in page.overlay: page.overlay.append(choice_dialog)
                choice_dialog.open = True
                page.update()

    def on_main_file_result(e: ft.FilePickerResultEvent):
        if not e.files: return
        
        f = e.files[0]
        # Если десктоп — читаем сразу
        if f.path:
            bytes_data = process_picked_file(f)
            if bytes_data:
                ui_state["image_bytes"] = bytes_data
                main_img_view.src_base64 = base64.b64encode(bytes_data).decode("utf-8")
                image_preview_card.visible = True
                instruction_container.visible = False
                if choice_dialog not in page.overlay: page.overlay.append(choice_dialog)
                choice_dialog.open = True
                page.update()
        else:
            # Если Веб — инициируем выгрузку (Upload)
            upload_url = page.get_upload_url(f.name, 600)
            if upload_url:
                main_picker.upload([
                    ft.FilePickerUploadFile(f.name, upload_url=upload_url)
                ])

    def on_chat_file_result(e: ft.FilePickerResultEvent):
        if not e.files: return
        # Для чата упрощенная логика (предполагаем десктоп или мгновенный контент)
        bytes_data = process_picked_file(e.files[0])
        if bytes_data:
            ui_state["chat_image_pending"] = bytes_data
            page.snack_bar = ft.SnackBar(ft.Text("Фото прикреплено к сообщению", color="white"), bgcolor="#009753")
            page.snack_bar.open = True
            page.update()

    # Инициализация пикеров
    main_picker = global_picker if global_picker else ft.FilePicker()
    main_picker.on_result = on_main_file_result
    main_picker.on_upload = on_upload_progress
    
    chat_picker = ft.FilePicker()
    chat_picker.on_result = on_chat_file_result

    if main_picker not in page.overlay: page.overlay.append(main_picker)
    if chat_picker not in page.overlay: page.overlay.append(chat_picker)

    # --- ЭЛЕМЕНТЫ ИНТЕРФЕЙСА ---
    loading_ring = ft.ProgressRing(visible=False, color="#009753", width=50, height=50)
    chat_display = ft.Column(scroll=ft.ScrollMode.ALWAYS, expand=True, spacing=15)
    
    chat_input = ft.TextField(
        hint_text="Спросите агронома...", 
        expand=True, 
        border_radius=15, 
        bgcolor="#F8F9FA",
        text_style=ft.TextStyle(font_family="Montserrat"),
        content_padding=15, 
        on_submit=lambda _: send_chat_message()
    )

    light_slider = ft.Slider(
        min=0, max=100, divisions=10, value=50, 
        label="{value}%", active_color="#FFC107",
        on_change=lambda e: ui_state.update({"selected_light_raw": int(e.control.value)})
    )

    # --- ЛОГИКА ДИАЛОГОВ И БД ---
    
    def open_plant_selector(e):
        """Загрузка списка растений пользователя из БД"""
        with next(get_db()) as db:
            plants = db.query(Plant).options(joinedload(Plant.catalog_info)).filter(
                Plant.user_id == user_state.get("id", 1), 
                Plant.is_active == 1
            ).all()
            
            if not plants:
                page.snack_bar = ft.SnackBar(ft.Text("Ваш сад пуст. Добавьте первое растение.")); page.snack_bar.open = True
                page.update()
                return

            def select_this_plant(plant):
                species = plant.catalog_info.species_name if plant.catalog_info else "Неизвестный вид"
                ui_state["current_plant_info"] = f"Растение: {plant.custom_name}. Вид: {species}. Статус: {plant.status_text}."
                ui_state["active_plant_id"] = plant.plant_id
                selector_dialog.open = False
                open_chat_interface(f"Вы выбрали **{plant.custom_name}**. Чем я могу помочь?")
                page.update()

            plant_list = ft.Column(spacing=10, tight=True, scroll=ft.ScrollMode.AUTO, height=400)
            for p in plants:
                # Путь к картинке в папке проекта
                img_src = f"plants/{p.image_url}" if p.image_url else None
                
                plant_list.controls.append(
                    ft.ListTile(
                        leading=ft.Image(src=img_src, width=40, height=40, border_radius=5) if img_src else ft.Icon(ft.Icons.ECO, color="#009753"),
                        title=ft.Text(p.custom_name, weight="bold", font_family="Montserrat"),
                        subtitle=ft.Text(p.catalog_info.species_name if p.catalog_info else "Комнатное растение", size=12),
                        on_click=lambda e, p_obj=p: select_this_plant(p_obj)
                    )
                )
            selector_dialog.content = ft.Container(content=plant_list, width=320)
            selector_dialog.open = True
            page.update()

    selector_dialog = ft.AlertDialog(
        title=ft.Text("Мои растения", font_family="Montserrat"),
        actions=[ft.TextButton("Закрыть", on_click=lambda _: setattr(selector_dialog, 'open', False))]
    )
    if selector_dialog not in page.overlay: page.overlay.append(selector_dialog)

    def start_diagnosis(e):
        """Запуск ИИ диагностики по сделанному фото"""
        if not ui_state["image_bytes"]: return
        choice_dialog.open = False
        loading_ring.visible = True
        page.update()
        
        def ai_task():
            with next(get_db()) as db:
                res, err = ai_service.diagnose_plant(db, user_state.get("id", 1), ui_state["image_bytes"])
                loading_ring.visible = False
                if res:
                    open_chat_interface(res)
                else:
                    page.snack_bar = ft.SnackBar(ft.Text(f"Ошибка: {err}")); page.snack_bar.open = True
                page.update()
        
        threading.Thread(target=ai_task, daemon=True).start()

    def start_adding(e, use_ai=True):
        """Переход на экран добавления с передачей данных через сессию"""
        choice_dialog.open = False
        page.session.set("pending_image", ui_state["image_bytes"])
        page.session.set("pending_light", ui_state["selected_light_raw"] / 100)
        page.session.set("use_ai_recognition", use_ai)
        nav("/add_plant")

    choice_dialog = ft.AlertDialog(
        title=ft.Text("Настройка", font_family="Montserrat"),
        content=ft.Column([
            ft.Text("Освещенность места:"),
            ft.Row([ft.Icon(ft.Icons.WB_CLOUDY_OUTLINED, size=20), light_slider, ft.Icon(ft.Icons.WB_SUNNY, size=20)]),
            ft.Divider(),
            ft.Text("Что сделать?", weight="bold"),
        ], tight=True, spacing=15),
        actions=[
            ft.Column([
                ft.ElevatedButton("Распознать и добавить", icon=ft.Icons.AUTO_AWESOME, bgcolor="#009753", color="white", width=280, on_click=lambda e: start_adding(e, True)),
                ft.OutlinedButton("Добавить вручную", icon=ft.Icons.EDIT_NOTE, width=280, on_click=lambda e: start_adding(e, False)),
                ft.TextButton("Просто консультация", icon=ft.Icons.MEDICATION_OUTLINED, on_click=start_diagnosis),
            ], horizontal_alignment="center", spacing=10)
        ]
    )

    # --- ЛОГИКА ЧАТА ---

    def send_chat_message():
        if (not chat_input.value and not ui_state["chat_image_pending"]) or ui_state["is_sending"]:
            return
        
        u_text = chat_input.value
        u_img = ui_state["chat_image_pending"]
        
        chat_input.value = ""
        ui_state["chat_image_pending"] = None
        ui_state["chat_messages"].append({"role": "user", "text": u_text, "image": u_img})
        ui_state["is_sending"] = True
        update_chat_ui()

        def ai_thread():
            with next(get_db()) as db:
                try:
                    if u_img:
                        res, err = ai_service.diagnose_plant(db, user_state.get("id", 1), u_img)
                    else:
                        res, err = ai_service.ask_agronomist(db, user_state.get("id", 1), ui_state["current_plant_info"], u_text)
                    
                    ans = res if not err else f"Проблема: {err}"
                    ui_state["chat_messages"].append({"role": "bot", "text": ans})
                except Exception as ex:
                    ui_state["chat_messages"].append({"role": "bot", "text": f"Сбой системы: {str(ex)}"})
                finally:
                    ui_state["is_sending"] = False
                    update_chat_ui()

        threading.Thread(target=ai_thread, daemon=True).start()

    def update_chat_ui():
        chat_display.controls.clear()
        for m in ui_state["chat_messages"]:
            is_u = m["role"] == "user"
            msg_content = ft.Column(spacing=5, tight=True)
            
            if m.get("image"):
                img_b64 = base64.b64encode(m["image"]).decode()
                msg_content.controls.append(ft.Image(src_base64=img_b64, width=200, border_radius=10))
            
            if m.get("text"):
                msg_content.controls.append(ft.Markdown(
                    m["text"], 
                    selectable=True,
                    extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                    style=ft.TextStyle(font_family="Montserrat", size=14)
                ))

            chat_display.controls.append(
                ft.Column([
                    ft.Container(
                        content=msg_content,
                        bgcolor="#009753" if is_u else "#F1F5F9",
                        padding=ft.padding.all(14),
                        border_radius=ft.border_radius.only(
                            top_left=15, top_right=15, 
                            bottom_left=15 if not is_u else 15, 
                            bottom_right=0 if is_u else 15
                        ),
                        theme=ft.Theme(text_theme=ft.TextTheme(body_medium=ft.TextStyle(color="white" if is_u else "black")))
                    ),
                    ft.Text("Вы" if is_u else "Агроном GreenThumb", size=10, color="grey700", italic=True)
                ], horizontal_alignment=ft.CrossAxisAlignment.END if is_u else ft.CrossAxisAlignment.START)
            )
        page.update()
        try: chat_display.scroll_to(offset=-1, duration=300)
        except: pass

    def open_chat_interface(initial_text):
        ui_state["chat_messages"] = [{"role": "bot", "text": initial_text}]
        action_buttons.visible = False
        sheet_col.controls = [
            ft.Container(width=40, height=4, bgcolor="grey300", border_radius=10, margin=ft.margin.only(bottom=10)),
            ft.Row([
                ft.Text("ИИ-Консультант", size=18, weight="bold", font_family="Montserrat"),
                ft.IconButton(ft.Icons.CLOSE_ROUNDED, on_click=close_sheet)
            ], alignment="spaceBetween"),
            ft.Divider(height=1, color="grey100"),
            ft.Container(content=chat_display, height=450, padding=ft.padding.only(top=10, bottom=10)),
            ft.Row([
                ft.IconButton(ft.Icons.ADD_PHOTO_ALTERNATE_OUTLINED, icon_color="#009753", on_click=lambda _: chat_picker.pick_files()),
                chat_input,
                ft.FloatingActionButton(icon=ft.Icons.SEND_ROUNDED, bgcolor="#009753", mini=True, on_click=lambda _: send_chat_message())
            ], spacing=10)
        ]
        sheet_container.offset = ft.Offset(0, 0)
        update_chat_ui()

    def close_sheet(e=None):
        sheet_container.offset = ft.Offset(0, 1)
        action_buttons.visible = True
        instruction_container.visible = True
        image_preview_card.visible = False
        ui_state["image_bytes"] = None
        page.update()

    # --- КОМПОНОВКА ЭКРАНА ---
    main_img_view = ft.Image(src="", fit=ft.ImageFit.COVER, border_radius=20)
    
    image_preview_card = ft.Container(
        content=main_img_view, 
        width=320, height=420, 
        border_radius=25, 
        border=ft.border.all(2, "#E0E0E0"),
        visible=False,
        shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.with_opacity(0.1, "black"))
    )
    
    instruction_container = ft.Container(
        content=ft.Column([
            ft.Container(
                content=ft.Icon(ft.Icons.CAMERA_ENHANCE_OUTLINED, size=60, color="#009753"),
                bgcolor="#E8F5E9", padding=30, border_radius=50
            ),
            ft.Text("Сканер растений", size=24, weight="bold", font_family="Montserrat"),
            ft.Text("Сфотографируйте растение для диагностики\nили выберите из своего списка", 
                    color="grey700", text_align="center", size=14, font_family="Montserrat")
        ], horizontal_alignment="center", spacing=20),
        alignment=ft.alignment.center
    )

    sheet_container = ft.Container(
        bgcolor="white", 
        padding=ft.padding.only(left=20, right=20, bottom=20, top=10),
        offset=ft.Offset(0, 1), 
        animate_offset=ft.animation.Animation(600, ft.AnimationCurve.DECELERATE),
        border_radius=ft.border_radius.only(top_left=35, top_right=35),
        shadow=ft.BoxShadow(blur_radius=30, color=ft.Colors.with_opacity(0.15, "black")),
        content=(sheet_col := ft.Column(tight=True, horizontal_alignment="center"))
    )

    action_buttons = ft.Container(
        content=ft.Row([
            ft.Container(
                content=ft.Row([
                    ft.IconButton(ft.Icons.LOCAL_FLORIST_ROUNDED, icon_color="white", on_click=open_plant_selector),
                    ft.VerticalDivider(width=1, color="white24"),
                    ft.TextButton("МОЙ САД", style=ft.ButtonStyle(color="white"), on_click=open_plant_selector)
                ], spacing=0),
                bgcolor="#4CAF50", border_radius=15, padding=ft.padding.only(left=5, right=15)
            ),
            ft.FloatingActionButton(
                content=ft.Row([ft.Icon(ft.Icons.ADD_A_PHOTO), ft.Text("СКАН")], alignment="center", spacing=5),
                bgcolor="#009753", width=140, shape=ft.RoundedRectangleBorder(radius=15),
                on_click=lambda _: main_picker.pick_files()
            )
        ], alignment="center", spacing=15),
        bottom=30, left=0, right=0
    )

    # Результирующий вид
    return ft.View(
        route="/scanner",
        padding=0,
        bgcolor="#F8FAF8",
        controls=[
            ft.Stack(
                expand=True,
                controls=[
                    instruction_container,
                    ft.Container(image_preview_card, alignment=ft.alignment.center),
                    ft.Container(loading_ring, alignment=ft.alignment.center),
                    ft.Container(sheet_container, bottom=0, left=0, right=0),
                    action_buttons
                ]
            )
        ]
    )