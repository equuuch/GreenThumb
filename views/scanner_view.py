import flet as ft
import threading
import base64
import urllib3
import json
from sqlalchemy.orm import joinedload
from database.session import get_db
from database.models import Plant, PlantCatalog
from services.ai_services import GigaChatService

# Отключаем предупреждения SSL для работы с GigaChat
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def ScannerView(page: ft.Page, nav, user_state, _=None):
    """
    Версия 3.4: ПОЛНАЯ СТАБИЛЬНАЯ ВЕРСИЯ
    - Исправлен SQLAlchemy joinedload для доступа к catalog_info.
    - Исправлен Markdown: удалены конфликтующие аргументы style/text_style.
    - Стилизация текста реализована через наследование темы в Container.
    - Сохранены все FilePicker, Threading и UI-элементы.
    """
    
    # --- СЛУЖЕБНЫЕ ОБЪЕКТЫ ---
    main_picker = ft.FilePicker()
    chat_picker = ft.FilePicker()
    
    # Добавляем пикеры в overlay, если их там нет
    if main_picker not in page.overlay: page.overlay.append(main_picker)
    if chat_picker not in page.overlay: page.overlay.append(chat_picker)
    
    ui_state = {
        "image_bytes": None,          # Фото для обработки
        "chat_image_pending": None,   # Фото, прикрепленное внутри чата
        "current_plant_info": "Общий вопрос по садоводству",
        "chat_messages": [],
        "is_sending": False,
        "selected_light_raw": 50      # Значение ползунка освещения
    }

    # --- ЭЛЕМЕНТЫ ИНТЕРФЕЙСА ---
    loading_ring = ft.ProgressRing(visible=False, color="#009753", width=50, height=50)
    chat_display = ft.Column(scroll=ft.ScrollMode.ALWAYS, expand=True, spacing=15)
    
    chat_input = ft.TextField(
        hint_text="Спросите агронома...", 
        expand=True, 
        border_radius=15, 
        bgcolor="#F8F9FA", 
        content_padding=15, 
        on_submit=lambda _: send_chat_message()
    )

    light_slider = ft.Slider(
        min=0, max=100, divisions=10, value=50, 
        label="{value}%", active_color="#FFC107",
        on_change=lambda e: ui_state.update({"selected_light_raw": int(e.control.value)})
    )

    # --- ЛОГИКА ВЫБОРА РАСТЕНИЯ ИЗ БАЗЫ (МОЙ САД) ---

    def open_plant_selector(e):
        with next(get_db()) as db:
            # Используем joinedload для получения данных из plant_catalog
            plants = db.query(Plant).options(joinedload(Plant.catalog_info)).filter(
                Plant.user_id == user_state.get("id", 1), 
                Plant.is_active == 1
            ).all()
            
            if not plants:
                page.snack_bar = ft.SnackBar(ft.Text("В вашем саду пока нет растений")); page.snack_bar.open = True
                page.update()
                return

            def select_this_plant(plant):
                # Безопасно получаем название вида из связанной таблицы
                species = plant.catalog_info.species_name if plant.catalog_info else "Вид не определен"
                ui_state["current_plant_info"] = f"Растение: {plant.custom_name}. Вид: {species}. Статус: {plant.status_text}."
                selector_dialog.open = False
                open_chat_interface(f"Вы выбрали **{plant.custom_name}** ({species}). Чем я могу помочь?")
                page.update()

            plant_list = ft.Column(spacing=10, tight=True, scroll=ft.ScrollMode.AUTO, height=400)
            for p in plants:
                # Берем латынь из каталога или статус из основной таблицы
                subtitle_info = p.catalog_info.latin_name if p.catalog_info else (p.status_text or "Инфо отсутствует")
                
                plant_list.controls.append(
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.ECO, color="#009753"),
                        title=ft.Text(p.custom_name or "Безымянное растение"),
                        subtitle=ft.Text(subtitle_info, size=12),
                        on_click=lambda e, p_obj=p: select_this_plant(p_obj)
                    )
                )

            selector_dialog.content = ft.Container(content=plant_list, width=300)
            selector_dialog.open = True
            page.update()

    selector_dialog = ft.AlertDialog(
        title=ft.Text("Выберите растение"),
        actions=[ft.TextButton("Отмена", on_click=lambda _: setattr(selector_dialog, 'open', False))],
    )
    if selector_dialog not in page.overlay: page.overlay.append(selector_dialog)

    # --- ЛОГИКА ДИАГНОСТИКИ (ПОСЛЕ ФОТО) ---

    def start_diagnosis(e):
        choice_dialog.open = False
        image_preview_card.visible = True
        instruction_container.visible = False
        loading_ring.visible = True
        page.update()
        
        def ai_task():
            ai = GigaChatService()
            with next(get_db()) as db:
                res, err = ai.diagnose_plant(db, user_state.get("id", 1), ui_state["image_bytes"])
                loading_ring.visible = False
                if res:
                    open_chat_interface(res)
                else:
                    page.snack_bar = ft.SnackBar(ft.Text(f"Ошибка: {err}")); page.snack_bar.open = True
                    close_sheet()
                page.update()
            
        threading.Thread(target=ai_task, daemon=True).start()

    def start_adding(e, use_ai=True):
        choice_dialog.open = False
        page.session.set("pending_image", ui_state["image_bytes"])
        page.session.set("pending_light", ui_state["selected_light_raw"] / 100)
        page.session.set("use_ai_recognition", use_ai)
        nav("/add_plant") 

    choice_dialog = ft.AlertDialog(
        title=ft.Text("Настройка растения"),
        content=ft.Column([
            ft.Text("Укажите уровень освещения:"),
            ft.Row([ft.Icon(ft.Icons.WB_CLOUDY), light_slider, ft.Icon(ft.Icons.WB_SUNNY)]),
            ft.Divider(),
            ft.Text("Выберите действие:", weight="bold"),
        ], tight=True),
        actions=[
            ft.Column([
                ft.ElevatedButton("Авто-определение ИИ", icon=ft.Icons.AUTO_AWESOME, bgcolor="#009753", color="white", width=250, on_click=lambda e: start_adding(e, True)),
                ft.OutlinedButton("Ввести вручную", icon=ft.Icons.EDIT, width=250, on_click=lambda e: start_adding(e, False)),
                ft.TextButton("Только консультация", icon=ft.Icons.CHAT, on_click=start_diagnosis),
            ], horizontal_alignment="center", spacing=10)
        ]
    )

    # --- ОБРАБОТКА ФАЙЛОВ ---

    def on_main_file_result(e: ft.FilePickerResultEvent):
        if not e.files: return
        with open(e.files[0].path, "rb") as f:
            ui_state["image_bytes"] = f.read()
        main_img_view.src_base64 = base64.b64encode(ui_state["image_bytes"]).decode("utf-8")
        if choice_dialog not in page.overlay: page.overlay.append(choice_dialog)
        choice_dialog.open = True
        page.update()

    main_picker.on_result = on_main_file_result

    def on_chat_file_result(e: ft.FilePickerResultEvent):
        if not e.files: return
        with open(e.files[0].path, "rb") as f:
            ui_state["chat_image_pending"] = f.read()
        page.snack_bar = ft.SnackBar(ft.Text("Фото прикреплено")); page.snack_bar.open = True
        page.update()

    chat_picker.on_result = on_chat_file_result

    # --- ФУНКЦИИ ЧАТА ---

    def send_chat_message():
        if (not chat_input.value and not ui_state["chat_image_pending"]) or ui_state["is_sending"]: return
        
        user_text = chat_input.value
        current_img = ui_state["chat_image_pending"]
        
        chat_input.value = ""
        ui_state["chat_image_pending"] = None
        ui_state["chat_messages"].append({"role": "user", "text": user_text, "image": current_img})
        ui_state["is_sending"] = True
        update_chat_ui()
        
        def ai_thread():
            ai = GigaChatService()
            with next(get_db()) as db:
                try:
                    if current_img:
                        res, err = ai.diagnose_plant(db, user_state.get("id", 1), current_img)
                        ans = res if res else f"Ошибка ИИ: {err}"
                    else:
                        res, err = ai.ask_agronomist(db, user_state.get("id", 1), ui_state["current_plant_info"], user_text)
                        ans = res if not err else f"Ошибка связи: {err}"
                    ui_state["chat_messages"].append({"role": "bot", "text": ans})
                except Exception as e:
                    ui_state["chat_messages"].append({"role": "bot", "text": f"Сбой: {str(e)}"})
                finally:
                    ui_state["is_sending"] = False
                    update_chat_ui()
                    
        threading.Thread(target=ai_thread, daemon=True).start()

    def update_chat_ui():
        chat_display.controls.clear()
        for msg in ui_state["chat_messages"]:
            is_user = msg["role"] == "user"
            content = ft.Column(spacing=5, tight=True)
            if msg.get("image"):
                img_b64 = base64.b64encode(msg["image"]).decode()
                content.controls.append(ft.Image(src_base64=img_b64, width=200, border_radius=10))
            if msg.get("text"):
                # Универсальный способ задания цвета для Markdown во всех версиях Flet
                content.controls.append(
                    ft.Markdown(msg["text"], selectable=True)
                )

            chat_display.controls.append(
                ft.Column([
                    ft.Container(
                        content=content, 
                        bgcolor="#009753" if is_user else "#F0F4F8", 
                        padding=12, 
                        border_radius=15,
                        # Управляем цветом текста через тему контейнера, чтобы избежать TypeError
                        theme=ft.Theme(
                            text_theme=ft.TextTheme(
                                body_medium=ft.TextStyle(color="white" if is_user else "black")
                            )
                        )
                    ),
                    ft.Text("Вы" if is_user else "Агроном", size=10, color="grey500")
                ], horizontal_alignment=ft.CrossAxisAlignment.END if is_user else ft.CrossAxisAlignment.START)
            )
        page.update()
        try: chat_display.scroll_to(offset=-1, duration=300)
        except: pass

    def open_chat_interface(text):
        ui_state["chat_messages"] = [{"role": "bot", "text": text}]
        action_buttons.visible = False
        sheet_col.controls = [
            ft.Container(width=40, height=4, bgcolor="grey300", border_radius=2, margin=10),
            ft.Row([ft.Text("Консультация", size=20, weight="bold"), ft.IconButton(ft.Icons.CLOSE, on_click=close_sheet)], alignment="spaceBetween"),
            ft.Divider(height=1),
            ft.Container(content=chat_display, height=380, padding=10),
            ft.Row([
                ft.IconButton(ft.Icons.ATTACH_FILE, icon_color="#009753", on_click=lambda _: chat_picker.pick_files()),
                chat_input,
                ft.IconButton(ft.Icons.SEND, bgcolor="#009753", icon_color="white", on_click=lambda _: send_chat_message())
            ])
        ]
        sheet_container.offset = ft.Offset(0, 0)
        update_chat_ui()

    def close_sheet(e=None):
        sheet_container.offset = ft.Offset(0, 1)
        image_preview_card.visible = False
        instruction_container.visible = True
        action_buttons.visible = True
        ui_state["image_bytes"] = None
        ui_state["current_plant_info"] = "Общий вопрос по садоводству"
        page.update()

    # --- ВЕРСТКА ОСНОВНОГО ЭКРАНА ---
    main_img_view = ft.Image(src="", fit=ft.ImageFit.COVER, border_radius=15)
    image_preview_card = ft.Container(content=main_img_view, width=300, height=400, border_radius=20, visible=False)
    
    instruction_container = ft.Container(
        content=ft.Column([
            ft.Icon(ft.Icons.CAMERA_ALT_OUTLINED, size=80, color="grey300"),
            ft.Text("GreenThumb Scanner", size=22, weight="bold"),
            ft.Text("Сфотографируйте растение или выберите из сада", color="grey500", text_align="center")
        ], horizontal_alignment="center"),
        alignment=ft.alignment.center
    )

    sheet_container = ft.Container(
        bgcolor="white", padding=20, offset=ft.Offset(0, 1), animate_offset=600,
        border_radius=ft.border_radius.only(top_left=30, top_right=30),
        shadow=ft.BoxShadow(blur_radius=20, color="black12")
    )
    sheet_col = ft.Column()
    sheet_container.content = sheet_col

    btn_style = ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12), padding=ft.padding.all(15))

    action_buttons = ft.Container(
        content=ft.Row([
            ft.ElevatedButton("Из сада", icon=ft.Icons.LOCAL_FLORIST, color="white", bgcolor="#4CAF50", height=55, style=btn_style, on_click=open_plant_selector),
            ft.ElevatedButton("Начать фото", icon=ft.Icons.ADD_A_PHOTO, color="white", bgcolor="#009753", height=55, style=btn_style, on_click=lambda _: main_picker.pick_files())
        ], alignment="center", spacing=20),
        bottom=40, left=0, right=0
    )

    return ft.View(
        route="/scanner",
        padding=0,
        controls=[
            ft.Stack(
                expand=True,
                controls=[
                    ft.Container(expand=True, bgcolor="#FDFDFD"),
                    instruction_container,
                    ft.Container(image_preview_card, alignment=ft.alignment.center),
                    ft.Container(loading_ring, alignment=ft.alignment.center),
                    ft.Container(sheet_container, bottom=0, left=0, right=0),
                    action_buttons
                ]
            )
        ]
    )