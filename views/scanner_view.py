import flet as ft
import threading
import base64
import urllib3
from database.session import get_db
from database.models import Plant, AIConsultation
from services.ai_services import GigaChatService

# Отключаем предупреждения SSL для работы с GigaChat
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def ScannerView(page: ft.Page, nav, user_state, _=None):
    """
    Версия 1.4: Исправлен тайминг появления кнопок и отображение статусов.
    """
    
    # --- СЛУЖЕБНЫЕ ОБЪЕКТЫ ---
    local_picker = ft.FilePicker()
    if local_picker not in page.overlay:
        page.overlay.append(local_picker)
    
    ui_state = {
        "image_bytes": None,
        "current_plant_info": "Новое растение",
        "chat_messages": [],
        "is_sending": False 
    }

    # --- UI ЭЛЕМЕНТЫ ---
    loading_ring = ft.ProgressRing(
        visible=False, color="#009753", width=50, height=50, stroke_width=4
    )
    
    chat_display = ft.Column(scroll=ft.ScrollMode.ALWAYS, expand=True, spacing=15)
    
    chat_input = ft.TextField(
        hint_text="Задайте вопрос агроному...", expand=True, border_radius=15, 
        bgcolor="#F8F9FA", content_padding=15,
        on_submit=lambda _: send_chat_message()
    )

    # --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---

    def on_sheet_animation_end(e):
        # Проверяем: если шторка уехала вниз (offset=1), только тогда показываем кнопки
        if sheet_container.offset.y == 1:
            action_buttons.visible = True
            page.update()

    def close_sheet(e=None):
        sheet_container.offset = ft.Offset(0, 1) # Плавный уезд вниз
        image_preview_card.visible = False
        instruction_container.visible = True
        loading_ring.visible = False
        # Кнопки НЕ включаем здесь, ждем завершения анимации в on_sheet_animation_end
        ui_state["image_bytes"] = None
        ui_state["chat_messages"] = []
        page.update()

    def create_chat_bubble(role, text):
        is_user = role == "user"
        return ft.Column([
            ft.Container(
                content=ft.Text(text, color="white" if is_user else "black", size=14),
                bgcolor="#009753" if is_user else "#F0F4F8",
                padding=ft.padding.symmetric(vertical=12, horizontal=16),
                border_radius=ft.border_radius.only(
                    top_left=18, top_right=18, 
                    bottom_left=18 if is_user else 2, bottom_right=2 if is_user else 18
                ),
            ),
            ft.Container(
                content=ft.Text("Вы" if is_user else "Агроном GreenThumb", size=10, color="grey500"),
                margin=ft.margin.only(top=4, bottom=10)
            )
        ], horizontal_alignment=ft.CrossAxisAlignment.END if is_user else ft.CrossAxisAlignment.START)

    def update_chat_ui():
        chat_display.controls.clear()
        for msg in ui_state["chat_messages"]:
            chat_display.controls.append(create_chat_bubble(msg["role"], msg["text"]))
        if ui_state["is_sending"]:
            chat_display.controls.append(ft.Text("Агроном печатает...", size=12, italic=True, color="grey500"))
        page.update()
        try:
            if chat_display.page:
                chat_display.scroll_to(offset=-1, duration=300)
        except: pass

    # --- БИЗНЕС-ЛОГИКА ---

    def send_chat_message():
        if not chat_input.value or ui_state["is_sending"]: return
        user_text = chat_input.value
        chat_input.value = ""
        ui_state["chat_messages"].append({"role": "user", "text": user_text})
        ui_state["is_sending"] = True
        update_chat_ui()
        
        def ai_thread():
            ai = GigaChatService()
            u_id = user_state.get("id") or 1
            with next(get_db()) as db:
                try:
                    res, _ = ai.ask_agronomist(db, u_id, ui_state["current_plant_info"], user_text)
                    if res:
                        content = res[0] if isinstance(res, tuple) else res
                        ui_state["chat_messages"].append({"role": "bot", "text": content})
                finally:
                    ui_state["is_sending"] = False
                    update_chat_ui()
        threading.Thread(target=ai_thread, daemon=True).start()

    def open_chat_interface(initial_text):
        ui_state["chat_messages"] = [{"role": "bot", "text": initial_text}]
        action_buttons.visible = False # Скрываем сразу, чтобы не мешали
        
        sheet_col.controls = [
            ft.Container(width=40, height=4, bgcolor="grey300", border_radius=2, margin=ft.margin.only(bottom=10)),
            ft.Row([
                ft.Text("Консультация", size=20, weight="bold"),
                ft.IconButton(ft.Icons.CLOSE, icon_color="grey600", on_click=close_sheet)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Divider(height=1, color="#EEEEEE"),
            ft.Container(content=chat_display, height=400, padding=ft.padding.symmetric(vertical=10)),
            ft.Row([
                chat_input,
                ft.IconButton(ft.Icons.SEND, icon_color="white", bgcolor="#009753", on_click=lambda _: send_chat_message())
            ])
        ]
        sheet_container.offset = ft.Offset(0, 0)
        update_chat_ui()

    def show_existing_plants_dialog(e):
        u_id = user_state.get("id") or 1
        with next(get_db()) as db:
            plants = db.query(Plant).filter(Plant.user_id == u_id, Plant.is_active == 1).all()
        
        if not plants:
            page.snack_bar = ft.SnackBar(ft.Text("Ваш сад пока пуст!")); page.snack_bar.open = True; page.update(); return

        def select_plant(p):
            dlg.open = False
            ui_state["current_plant_info"] = f"Растение: {p.custom_name}, Состояние: {p.status_text}"
            loading_ring.visible = True
            page.update()
            
            def plant_task():
                ai = GigaChatService()
                with next(get_db()) as db:
                    res, _ = ai.ask_agronomist(db, u_id, ui_state["current_plant_info"], "Дай краткий отчет по уходу.")
                    loading_ring.visible = False
                    if res: open_chat_interface(res[0] if isinstance(res, tuple) else res)
                    else: page.update()
            threading.Thread(target=plant_task, daemon=True).start()

        list_items = [
            ft.ListTile(
                title=ft.Text(p.custom_name, weight="bold"),
                subtitle=ft.Text(f"Статус: {p.status_text}"), # Возвращаем отображение статуса
                leading=ft.Icon(ft.Icons.ECO, color="#009753"),
                on_click=lambda _, plant=p: select_plant(plant)
            ) for p in plants
        ]

        dlg = ft.AlertDialog(
            title=ft.Text("Ваш сад"),
            content=ft.Column(list_items, scroll=True, height=350, tight=True),
            shape=ft.RoundedRectangleBorder(radius=20)
        )
        page.overlay.append(dlg); dlg.open = True; page.update()

    # --- ФАЙЛЫ ---

    def handle_file_result(e: ft.FilePickerResultEvent):
        if not e.files: return
        try:
            with open(e.files[0].path, "rb") as f: ui_state["image_bytes"] = f.read()
            main_img_view.src_base64 = base64.b64encode(ui_state["image_bytes"]).decode("utf-8")
            image_preview_card.visible = True; instruction_container.visible = False; loading_ring.visible = True; page.update()
            
            threading.Thread(target=lambda: (
                ai := GigaChatService(),
                res := ai.diagnose_plant(next(get_db()), user_state.get("id", 1), ui_state["image_bytes"]),
                setattr(loading_ring, 'visible', False),
                open_chat_interface(res[0]) if res else close_sheet()
            ), daemon=True).start()
        except: pass

    local_picker.on_result = handle_file_result

    # --- ВЕРСТКА ---

    main_img_view = ft.Image(src="", fit=ft.ImageFit.COVER, border_radius=15)
    image_preview_card = ft.Container(content=main_img_view, width=300, height=400, bgcolor="white", padding=10, border_radius=25, visible=False)
    
    instruction_container = ft.Container(
        content=ft.Column([
            ft.Icon(ft.Icons.CAMERA_ENHANCE_OUTLINED, size=80, color="#E0E0E0"),
            ft.Text("GreenThumb AI Scanner", size=24, weight="bold"),
            ft.Text("Сделайте фото или выберите из списка", color="grey600", text_align="center")
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
        alignment=ft.alignment.center
    )

    sheet_container = ft.Container(
        bgcolor="white", padding=25, border_radius=ft.border_radius.only(top_left=35, top_right=35),
        offset=ft.Offset(0, 1), animate_offset=600,
        on_animation_end=on_sheet_animation_end, # КРИТИЧНО для плавности
        shadow=ft.BoxShadow(blur_radius=40, color=ft.Colors.with_opacity(0.1, "black"))
    )
    sheet_col = ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5)
    sheet_container.content = sheet_col

    action_buttons = ft.Container(
        content=ft.Row([
            ft.ElevatedButton("Фото", icon=ft.Icons.ADD_A_PHOTO, on_click=lambda _: local_picker.pick_files()),
            ft.FloatingActionButton(icon=ft.Icons.SUPPORT_AGENT, bgcolor="#009753", on_click=show_existing_plants_dialog)
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=25), bottom=80, left=0, right=0
    )

    return ft.View(
        route="/scanner", padding=0,
        controls=[
            ft.Stack(
                expand=True, 
                controls=[
                    ft.Container(expand=True, bgcolor="#FDFDFD"),
                    instruction_container,
                    ft.Container(content=image_preview_card, alignment=ft.alignment.center),
                    ft.Container(content=loading_ring, alignment=ft.alignment.center),
                    ft.Container(content=sheet_container, bottom=0, left=0, right=0),
                    action_buttons
                ]
            )
        ]
    )