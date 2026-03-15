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

# принудительное отключение предупреждений ssl для стабильной работы мультимодальных запросов к ии.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def ScannerView(page: ft.Page, nav, user_state, global_picker=None):
    """
    интерфейсный модуль интеллектуального сканера.
    построен на парадигме state-driven ui (интерфейс, управляемый состоянием).
    """
    
    # инициализация сервисного слоя для взаимодействия с нейросетью.
    ai_service = GigaChatService()
    
    # 1. определение объекта состояния (ui state).
    # это «единственный источник истины» для экрана. изменение этих данных 
    # и последующий вызов update() инициирует реактивное обновление интерфейса.
    ui_state = {
        "image_bytes": None,           # бинарные данные основного изображения.
        "chat_image_pending": None,    # временный буфер для фото-вложения в чате.
        "current_plant_info": "Общий вопрос по садоводству", # контекст для промпта ии.
        "chat_messages": [],           # массив истории сообщений для рендеринга.
        "is_sending": False,           # флаг блокировки интерфейса при отправке запроса.
        "selected_light_raw": 50,      # состояние регулятора освещенности.
        "active_plant_id": None        # id привязанного к чату растения.
    }

    # --- блок алгоритмов обработки файлов ---

    def process_picked_file(picked_file):
        """
        универсальный метод извлечения байтов. обеспечивает кроссплатформенность:
        чтение по пути файла (desktop) или через поток контента (web).
        """
        if hasattr(picked_file, "path") and picked_file.path:
            with open(picked_file.path, "rb") as f:
                return f.read()
        content = getattr(picked_file, "content", None)
        if content:
            return content
        # поиск во временной папке загрузок для веб-окружения.
        upload_path = os.path.join("assets", "uploads", picked_file.name)
        if os.path.exists(upload_path):
            with open(upload_path, "rb") as f:
                return f.read()
        return None

    def on_upload_progress(e: ft.FilePickerUploadEvent):
        """реакция системы на завершение физической транзакции загрузки файла в pwa/web-версии."""
        if e.status == "completed":
            upload_path = os.path.join("assets", "uploads", e.file_name)
            if os.path.exists(upload_path):
                with open(upload_path, "rb") as f:
                    ui_state["image_bytes"] = f.read()
                
                # обновление свойств визуальных компонентов на основе полученных данных.
                main_img_view.src_base64 = base64.b64encode(ui_state["image_bytes"]).decode("utf-8")
                image_preview_card.visible = True
                instruction_container.visible = False
                choice_dialog.open = True
                page.update() # триггер для перерисовки кадра интерфейса.

    def on_main_file_result(e: ft.FilePickerResultEvent):
        """обработка события выбора файла пользователем."""
        if not e.files: return
        f = e.files[0]
        if f.path:
            # для десктопа: прямое чтение и мгновенная реакция ui.
            bytes_data = process_picked_file(f)
            if bytes_data:
                ui_state["image_bytes"] = bytes_data
                main_img_view.src_base64 = base64.b64encode(bytes_data).decode("utf-8")
                image_preview_card.visible = True
                instruction_container.visible = False
                choice_dialog.open = True
                page.update()
        else:
            # для веба: инициирование асинхронного процесса upload.
            upload_url = page.get_upload_url(f.name, 600)
            if upload_url:
                main_picker.upload([ft.FilePickerUploadFile(f.name, upload_url=upload_url)])

    # создание системных объектов для работы с файловой системой устройства.
    main_picker = global_picker if global_picker else ft.FilePicker()
    main_picker.on_result = on_main_file_result
    main_picker.on_upload = on_upload_progress
    chat_picker = ft.FilePicker()
    chat_picker.on_result = lambda e: ui_state.update({"chat_image_pending": process_picked_file(e.files[0])}) if e.files else None

    # инъекция пикеров в дерево компонентов страницы.
    if main_picker not in page.overlay: page.overlay.append(main_picker)
    if chat_picker not in page.overlay: page.overlay.append(chat_picker)

    # --- визуальные элементы индикации ---
    # декларативное описание компонентов, чья видимость управляется логикой приложения.
    loading_ring = ft.Container(
        content=ft.Column([
            ft.ProgressRing(color="#009753", width=40, height=40),
            ft.Text("Анализирую...", color="#009753", size=12, weight="bold")
        ], horizontal_alignment="center", tight=True),
        visible=False, # компонент скрыт по умолчанию.
        bgcolor="white",
        padding=20,
        border_radius=15,
        shadow=ft.BoxShadow(blur_radius=20, color="black12")
    )

    chat_display = ft.Column(scroll=ft.ScrollMode.ALWAYS, expand=True, spacing=15)
    
    chat_input = ft.TextField(
        hint_text="Задайте вопрос...", 
        expand=True, 
        border=ft.InputBorder.NONE,
        bgcolor=ft.Colors.TRANSPARENT,
        text_style=ft.TextStyle(font_family="Montserrat"),
        on_submit=lambda _: send_chat_message()
    )

    light_slider = ft.Slider(
        min=0, max=100, divisions=10, value=50, 
        active_color="#009753",
        on_change=lambda e: ui_state.update({"selected_light_raw": int(e.control.value)})
    )

    # --- логика взаимодействия с бд и нейросетью ---

    def open_plant_selector(e):
        """загрузка данных из бд и отображение диалога выбора растения."""
        with next(get_db()) as db:
            # выполнение sql-запроса через orm sqlalchemy с фильтрацией активных записей.
            plants = db.query(Plant).options(joinedload(Plant.catalog_info)).filter(
                Plant.user_id == user_state.get("id", 1), Plant.is_active == 1
            ).all()
            if not plants:
                page.snack_bar = ft.SnackBar(ft.Text("Ваш сад пока пуст")); page.snack_bar.open = True
                page.update(); return

            plant_list = ft.Column(spacing=10, tight=True, scroll=ft.ScrollMode.AUTO, height=350)
            for p in plants:
                # динамическая сборка списка элементов на основе данных из базы.
                img_src = f"plants/{p.image_url}" if p.image_url else None
                plant_list.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Image(src=img_src, width=50, height=50, border_radius=10, fit=ft.ImageFit.COVER) if img_src else ft.Icon(ft.Icons.ECO, color="#009753"),
                            ft.Column([
                                ft.Text(p.custom_name, weight="bold", size=14),
                                ft.Text(p.catalog_info.species_name if p.catalog_info else "Растение", size=11, color="grey"),
                            ], spacing=2, expand=True),
                            ft.Icon(ft.Icons.CHEVRON_RIGHT_ROUNDED, color="grey400")
                        ]),
                        padding=10, border_radius=12, bgcolor="#F8FAF8",
                        on_click=lambda e, p_obj=p: select_this_plant(p_obj)
                    )
                )
            selector_dialog.content = ft.Container(content=plant_list, width=350)
            selector_dialog.open = True
            page.update()

    def select_this_plant(plant):
        """обработка выбора растения: формирование контекста для промпта ассистента."""
        ui_state["current_plant_info"] = f"Растение: {plant.custom_name}. Вид: {plant.catalog_info.species_name}."
        ui_state["active_plant_id"] = plant.plant_id
        selector_dialog.open = False
        # реактивный вызов открытия чата с персональным приветствием.
        open_chat_interface(f"Вы выбрали **{plant.custom_name}**. Задайте мне любой вопрос по уходу!")
        page.update()

    selector_dialog = ft.AlertDialog(title=ft.Text("Выберите растение", weight="bold"))
    if selector_dialog not in page.overlay: page.overlay.append(selector_dialog)

    choice_dialog = ft.AlertDialog(
        title=ft.Text("Что сделать с фото?", weight="bold", size=20),
        content=ft.Column([
            ft.Text("Настройте свет в месте съемки:", size=12, color="grey"),
            ft.Row([ft.Icon(ft.Icons.LIGHT_MODE_ROUNDED, size=18, color="amber"), light_slider], alignment="center"),
            ft.Divider(height=10, color="transparent"),
            ft.Container(
                content=ft.Column([
                    ft.ElevatedButton(
                        content=ft.Row([ft.Icon(ft.Icons.AUTO_AWESOME), ft.Text("ИИ Распознавание")], alignment="center"),
                        bgcolor="#009753", color="white", height=50, on_click=lambda e: start_adding(e, True)
                    ),
                    ft.OutlinedButton(
                        content=ft.Row([ft.Icon(ft.Icons.MEDICAL_SERVICES_OUTLINED), ft.Text("Диагностика болезни")], alignment="center"),
                        height=50, on_click=lambda e: start_diagnosis(e)
                    ),
                    ft.TextButton("Просто добавить в базу", icon=ft.Icons.ADD, on_click=lambda e: start_adding(e, False)),
                ], spacing=10, tight=True)
            )
        ], tight=True),
        shape=ft.RoundedRectangleBorder(radius=20)
    )
    if choice_dialog not in page.overlay: page.overlay.append(choice_dialog)

    # --- реализация асинхронной реактивности ---

    def start_diagnosis(e):
        """
        инициализация нейросетевой диагностики. 
        использование потока (threading) предотвращает блокировку ui во время ожидания ответа api.
        """
        choice_dialog.open = False; loading_ring.visible = True; page.update()
        def ai_task():
            with next(get_db()) as db:
                # запрос к мультимодальной модели gigachat-max для визуального анализа.
                res, err = ai_service.diagnose_plant(db, user_state.get("id", 1), ui_state["image_bytes"])
                # реактивное изменение состояния видимости после завершения сетевой операции.
                loading_ring.visible = False
                if res: open_chat_interface(res)
                else: 
                    page.snack_bar = ft.SnackBar(ft.Text(f"Ошибка: {err}")); page.snack_bar.open = True
                page.update()
        # запуск асинхронной задачи в фоновом режиме.
        threading.Thread(target=ai_task, daemon=True).start()

    def start_adding(e, use_ai=True):
        """переход к вью добавления с передачей параметров через сессию страницы."""
        choice_dialog.open = False
        page.session.set("pending_image", ui_state["image_bytes"])
        page.session.set("pending_light", ui_state["selected_light_raw"] / 100)
        page.session.set("use_ai_recognition", use_ai)
        nav("/add_plant")

    # --- механизмы функционирования чата ---

    def send_chat_message():
        """процедура отправки сообщения и мгновенного обновления визуальной истории."""
        if (not chat_input.value and not ui_state["chat_image_pending"]) or ui_state["is_sending"]: 
            return
        
        # фиксация введенных данных и обновление локального стейта.
        u_text, u_img = chat_input.value, ui_state["chat_image_pending"]
        chat_input.value = ""; ui_state["chat_image_pending"] = None
        ui_state["chat_messages"].append({"role": "user", "text": u_text, "image": u_img})
        ui_state["is_sending"] = True; update_chat_ui()

        def ai_thread():
            """фоновый поток для ожидания ответа от текстовой или vision модели."""
            with next(get_db()) as db:
                try:
                    if u_img: 
                        res, err = ai_service.diagnose_plant(db, user_state.get("id", 1), u_img)
                    else: 
                        res, err = ai_service.ask_agronomist(db, user_state.get("id", 1), ui_state["current_plant_info"], u_text)
                    ui_state["chat_messages"].append({"role": "bot", "text": res if not err else f"Ошибка: {err}"})
                except Exception as ex: 
                    ui_state["chat_messages"].append({"role": "bot", "text": "Технический сбой связи."})
                ui_state["is_sending"] = False; update_chat_ui()

        threading.Thread(target=ai_thread, daemon=True).start()

    def update_chat_ui():
        """
        алгоритм рендеринга истории сообщений (state-driven rendering).
        полностью очищает и перестраивает список, синхронизируя ui с данными массива chat_messages.
        """
        chat_display.controls.clear()
        for m in ui_state["chat_messages"]:
            is_u = m["role"] == "user"
            msg_content = ft.Column(spacing=5, tight=True)
            if m.get("image"):
                msg_content.controls.append(ft.Image(src_base64=base64.b64encode(m["image"]).decode(), width=180, border_radius=10))
            
            if m.get("text"):
                msg_content.controls.append(ft.Markdown(
                    m["text"], 
                    selectable=True,
                    extension_set=ft.MarkdownExtensionSet.GITHUB_WEB
                ))
            
            chat_display.controls.append(
                ft.Row([
                    ft.Container(
                        content=msg_content,
                        bgcolor="#009753" if is_u else "#F0F4F0",
                        padding=ft.padding.symmetric(vertical=12, horizontal=16),
                        width=270, # ограничение ширины для принудительного переноса текста.
                        theme=ft.Theme(
                            text_theme=ft.TextTheme(
                                body_medium=ft.TextStyle(size=14, color="white" if is_u else "black", font_family="Montserrat")
                            )
                        ),
                        border_radius=ft.border_radius.only(
                            top_left=15, top_right=15, 
                            bottom_left=15 if not is_u else 15, 
                            bottom_right=0 if is_u else 15
                        ),
                        shadow=ft.BoxShadow(blur_radius=10, color="black12")
                    )
                ], alignment=ft.MainAxisAlignment.END if is_u else ft.MainAxisAlignment.START)
            )
        page.update() # инициирование перерисовки холста страницы.
        try: chat_display.scroll_to(offset=-1, duration=300)
        except: pass

    def open_chat_interface(initial_text):
        """инициализация и визуальное открытие панели чата через анимацию смещения."""
        ui_state["chat_messages"] = [{"role": "bot", "text": initial_text}]
        action_buttons.visible = False
        sheet_col.controls = [
            ft.Container(width=50, height=5, bgcolor="grey300", border_radius=10, margin=10),
            ft.Row([
                ft.Row([
                    ft.Container(content=ft.Icon(ft.Icons.SUPPORT_AGENT, color="#009753"), bgcolor="#EBF7ED", padding=5, border_radius=10), 
                    ft.Text("Агроном ИИ", weight="bold", size=16)
                ], spacing=10),
                ft.IconButton(ft.Icons.CLOSE_ROUNDED, icon_color="#009753", on_click=close_sheet)
            ], alignment="spaceBetween"),
            ft.Container(content=chat_display, height=400, bgcolor="#F8FAF8", border_radius=20, padding=10),
            ft.Container(
                content=ft.Row([
                    ft.IconButton(ft.Icons.IMAGE_OUTLINED, icon_color="#009753", on_click=lambda _: chat_picker.pick_files()),
                    chat_input,
                    ft.IconButton(ft.Icons.SEND_ROUNDED, icon_color="#009753", on_click=lambda _: send_chat_message())
                ]),
                padding=ft.padding.symmetric(horizontal=12),
                bgcolor="white", border_radius=15, border=ft.border.all(1, "#E8E8E8")
            )
        ]
        # анимация: изменение offset вызывает плавный выезд панели снизу.
        sheet_container.offset = ft.Offset(0, 0)
        update_chat_ui()

    def close_sheet(e=None):
        """закрытие панели чата и сброс визуального состояния экрана."""
        sheet_container.offset = ft.Offset(0, 1)
        action_buttons.visible = True
        instruction_container.visible = True
        image_preview_card.visible = False
        page.update()

    # --- декларативное построение иерархии компонентов ---

    main_img_view = ft.Image(src="", fit=ft.ImageFit.COVER, border_radius=30)
    image_preview_card = ft.Container(content=main_img_view, width=300, height=400, border_radius=35, visible=False, shadow=ft.BoxShadow(blur_radius=30, color="black26"))
    
    instruction_container = ft.Container(
        content=ft.Column([
            ft.Container(
                content=ft.Icon(ft.Icons.CAMERA_ALT_ROUNDED, size=50, color="#009753"),
                bgcolor="#EBF7ED", width=120, height=120, border_radius=60, alignment=ft.alignment.center
            ),
            ft.Text("GreenThumb Scanner", size=24, weight="bold", color="#1B3122"),
            ft.Text("Сфотографируйте растение,\nчтобы начать диагностику", text_align="center", color="grey600")
        ], horizontal_alignment="center", spacing=20),
        alignment=ft.alignment.center
    )

    sheet_container = ft.Container(
        bgcolor="white", padding=20, offset=ft.Offset(0, 1), 
        animate_offset=ft.animation.Animation(500, ft.AnimationCurve.EASE_OUT_QUINT),
        border_radius=ft.border_radius.only(top_left=30, top_right=30),
        shadow=ft.BoxShadow(blur_radius=40, color="black26"),
        content=(sheet_col := ft.Column(tight=True))
    )

    action_buttons = ft.Container(
        content=ft.Row([
            ft.Container(
                content=ft.Row([ft.Icon(ft.Icons.MENU_BOOK_ROUNDED, color="white", size=20), ft.Text("МОЙ САД", color="white", weight="bold")], spacing=10),
                bgcolor="#4CAF50", padding=ft.padding.symmetric(horizontal=20, vertical=12), border_radius=15,
                on_click=open_plant_selector, shadow=ft.BoxShadow(blur_radius=10, color="#4CAF5044")
            ),
            ft.Container(
                content=ft.Row([ft.Icon(ft.Icons.CROP_FREE_ROUNDED, color="white", size=22), ft.Text("СКАН", color="white", weight="bold")], spacing=10),
                bgcolor="#009753", padding=ft.padding.symmetric(horizontal=30, vertical=15), border_radius=20,
                on_click=lambda _: main_picker.pick_files(), shadow=ft.BoxShadow(blur_radius=15, color="#00975366")
            )
        ], alignment="center", spacing=20),
        bottom=40, left=0, right=0
    )

    # результирующий вид экрана со слоистой компоновкой (stack) и эффектами размытия.
    return ft.View(
        route="/scanner",
        padding=0,
        bgcolor="#F3F7F4",
        controls=[
            ft.Stack(
                expand=True,
                controls=[
                    # декоративный элемент фона (blur effect).
                    ft.Container(width=300, height=300, bgcolor="#E1F0E5", border_radius=150, top=-100, right=-100, blur=ft.Blur(80, 80)),
                    instruction_container,
                    ft.Container(image_preview_card, alignment=ft.alignment.center),
                    ft.Container(loading_ring, alignment=ft.alignment.center),
                    ft.Container(sheet_container, bottom=0, left=0, right=0),
                    action_buttons
                ]
            )
        ]
    )