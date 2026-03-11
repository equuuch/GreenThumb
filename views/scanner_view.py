import flet as ft
import threading
import base64
import urllib3
from database.session import get_db
from database.models import Plant
from services.ai_services import GigaChatService

# Отключаем предупреждения SSL для работы с GigaChat
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def ScannerView(page: ft.Page, nav, user_state, _=None):
    """
    Версия 1.6: Полное разделение логики 'Добавить растение' и 'Чат с ИИ'.
    """
    
    # --- СЛУЖЕБНЫЕ ОБЪЕКТЫ ---
    main_picker = ft.FilePicker()
    chat_picker = ft.FilePicker()
    
    for picker in [main_picker, chat_picker]:
        if picker not in page.overlay:
            page.overlay.append(picker)
    
    ui_state = {
        "image_bytes": None,          # Фото для обработки
        "chat_image_pending": None,   # Фото, прикрепленное внутри чата
        "current_plant_info": "Новое растение",
        "chat_messages": [],
        "is_sending": False 
    }

    # --- ЭЛЕМЕНТЫ ИНТЕРФЕЙСА ---
    loading_ring = ft.ProgressRing(visible=False, color="#009753", width=50, height=50)
    
    chat_display = ft.Column(scroll=ft.ScrollMode.ALWAYS, expand=True, spacing=15)
    
    chat_input = ft.TextField(
        hint_text="Спросите агронома...", expand=True, border_radius=15, 
        bgcolor="#F8F9FA", content_padding=15, on_submit=lambda _: send_chat_message()
    )

    # --- ЛОГИКА ВЫБОРА (ДИАЛОГ) ---

    def start_diagnosis(e):
        """Режим: Спросить ИИ"""
        choice_dialog.open = False
        image_preview_card.visible = True
        instruction_container.visible = False
        loading_ring.visible = True
        page.update()
        
        def ai_task():
            ai = GigaChatService()
            # Вызываем диагностику по фото
            res = ai.diagnose_plant(next(get_db()), user_state.get("id", 1), ui_state["image_bytes"])
            loading_ring.visible = False
            if res:
                # Открываем чат с ответом ИИ
                open_chat_interface(res[0] if isinstance(res, tuple) else res)
            else:
                page.snack_bar = ft.SnackBar(ft.Text("Не удалось проанализировать фото")); page.snack_bar.open = True
                close_sheet()
            page.update()
            
        threading.Thread(target=ai_task, daemon=True).start()

    def start_adding(e):
        """Режим: Добавить в коллекцию"""
        choice_dialog.open = False
        # Сохраняем фото в сессию, чтобы экран /add_plant мог его забрать
        page.session.set("pending_image", ui_state["image_bytes"])
        nav("/add_plant") 

    choice_dialog = ft.AlertDialog(
        title=ft.Text("Фото получено"),
        content=ft.Text("Что вы хотите сделать с этим изображением?"),
        actions=[
            ft.TextButton("Проконсультироваться", icon=ft.Icons.CHAT_BUBBLE_OUTLINE, on_click=start_diagnosis),
            ft.ElevatedButton("Добавить в мой сад", icon=ft.Icons.ADD_ALARM, bgcolor="#009753", color="white", on_click=start_adding),
        ],
        actions_alignment=ft.MainAxisAlignment.CENTER,
    )

    # --- ОБРАБОТКА ФАЙЛОВ ---

    def on_main_file_result(e: ft.FilePickerResultEvent):
        if not e.files: return
        try:
            with open(e.files[0].path, "rb") as f:
                ui_state["image_bytes"] = f.read()
            
            # Показываем превью на фоне и открываем диалог выбора
            main_img_view.src_base64 = base64.b64encode(ui_state["image_bytes"]).decode("utf-8")
            page.overlay.append(choice_dialog)
            choice_dialog.open = True
            page.update()
        except Exception as ex:
            print(f"File error: {ex}")

    main_picker.on_result = on_main_file_result

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
                        res = ai.diagnose_plant(db, user_state.get("id", 1), current_img)
                        ans = res[0] if res else "Не удалось распознать фото."
                    else:
                        res, _ = ai.ask_agronomist(db, user_state.get("id", 1), ui_state["current_plant_info"], user_text)
                        ans = res[0] if isinstance(res, tuple) else res
                    ui_state["chat_messages"].append({"role": "bot", "text": ans})
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
                content.controls.append(ft.Text(msg["text"], color="white" if is_user else "black"))

            chat_display.controls.append(
                ft.Column([
                    ft.Container(
                        content=content,
                        bgcolor="#009753" if is_user else "#F0F4F8",
                        padding=12, border_radius=15
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
            ft.Row([
                ft.Text("Консультация", size=20, weight="bold"),
                ft.IconButton(ft.Icons.CLOSE, on_click=close_sheet)
            ], alignment="spaceBetween"),
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
        page.update()

    # --- ВЕРСТКА ---
    main_img_view = ft.Image(src="", fit=ft.ImageFit.COVER, border_radius=15)
    image_preview_card = ft.Container(content=main_img_view, width=300, height=400, border_radius=20, visible=False)
    
    instruction_container = ft.Container(
        content=ft.Column([
            ft.Icon(ft.Icons.CAMERA_ALT_OUTLINED, size=80, color="grey300"),
            ft.Text("GreenThumb Scanner", size=22, weight="bold"),
            ft.Text("Сфотографируйте растение", color="grey500")
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

    action_buttons = ft.Container(
        content=ft.Row([
            ft.FloatingActionButton(
                content=ft.Row([ft.Icon(ft.Icons.ADD_A_PHOTO), ft.Text(" Начать")], alignment="center"),
                width=160, bgcolor="#009753", on_click=lambda _: main_picker.pick_files()
            )
        ], alignment="center"),
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