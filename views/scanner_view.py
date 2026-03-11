import flet as ft
import threading
import base64
import os
import urllib3
from database.session import get_db
from database.models import Plant, AIConsultation
from services.ai_services import GigaChatService

# Отключаем предупреждения SSL (для работы с GigaChat без установки сертификатов Минцифры)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def ScannerView(page: ft.Page, nav, user_state, _=None):
    """
    Модуль интеллектуального сканирования и консультаций GreenThumb.
    Версия 1.2: Исправлены отступы текста и строковые иконки.
    """
    
    # --- СЛУЖЕБНЫЕ ОБЪЕКТЫ ---
    local_picker = ft.FilePicker()
    if local_picker not in page.overlay:
        page.overlay.append(local_picker)
    
    ui_state = {
        "image_bytes": None,
        "current_plant_info": "Новое растение",
        "chat_messages": [],
        "is_loading": False,
        "is_sending": False 
    }

    # --- UI ЭЛЕМЕНТЫ ---
    loading_ring = ft.ProgressRing(
        visible=False, 
        color="#009753", 
        width=50, 
        height=50,
        stroke_width=4
    )
    
    chat_display = ft.Column(
        scroll=ft.ScrollMode.ALWAYS, 
        expand=True, 
        spacing=15
    )
    
    chat_input = ft.TextField(
        hint_text="Задайте вопрос агроному...", 
        expand=True, 
        border_radius=15, 
        border_color="#E0E0E0",
        bgcolor="#F8F9FA",
        content_padding=15,
        on_submit=lambda _: send_chat_message()
    )

    # --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---

    def close_sheet(e=None):
        sheet_container.offset = ft.Offset(0, 1)
        image_preview_card.visible = False
        instruction_container.visible = True
        loading_ring.visible = False
        ui_state["image_bytes"] = None
        ui_state["chat_messages"] = []
        ui_state["is_loading"] = False
        page.update()

    def create_chat_bubble(role, text):
        """Исправленная генерация облака сообщения"""
        is_user = role == "user"
        return ft.Column([
            ft.Container(
                content=ft.Text(text, color="white" if is_user else "black", size=14),
                bgcolor="#009753" if is_user else "#F0F4F8",
                padding=ft.padding.symmetric(vertical=12, horizontal=16),
                border_radius=ft.border_radius.only(
                    top_left=18, 
                    top_right=18, 
                    bottom_left=18 if is_user else 2, 
                    bottom_right=2 if is_user else 18
                ),
            ),
            # ТЕПЕРЬ ТЕКСТ В КОНТЕЙНЕРЕ С MARGIN
            ft.Container(
                content=ft.Text(
                    "Вы" if is_user else "Агроном GreenThumb", 
                    size=10, 
                    color="grey500"
                ),
                margin=ft.margin.only(top=4, bottom=10)
            )
        ], horizontal_alignment=ft.CrossAxisAlignment.END if is_user else ft.CrossAxisAlignment.START)

    def update_chat_ui():
        chat_display.controls.clear()
        for msg in ui_state["chat_messages"]:
            chat_display.controls.append(create_chat_bubble(msg["role"], msg["text"]))
        
        if ui_state["is_sending"]:
            chat_display.controls.append(
                ft.Text("Агроном печатает...", size=12, italic=True, color="grey500")
            )
            
        page.update()
        if chat_display.controls:
            chat_display.scroll_to(offset=-1, duration=300)

    # --- БИЗНЕС-ЛОГИКА ---

    def send_chat_message():
        if not chat_input.value or ui_state["is_sending"]:
            return
            
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
                except Exception as ex:
                    print(f"Chat error: {ex}")
                finally:
                    ui_state["is_sending"] = False
                    update_chat_ui()

        threading.Thread(target=ai_thread, daemon=True).start()

    def process_diagnosis_with_ai():
        ai = GigaChatService()
        u_id = user_state.get("id") or 1
        with next(get_db()) as db:
            try:
                res_text, _ = ai.diagnose_plant(db, u_id, ui_state["image_bytes"])
                loading_ring.visible = False
                if res_text:
                    ui_state["current_plant_info"] = "Растение на анализе"
                    open_chat_interface(res_text)
                else:
                    close_sheet()
            except Exception as ex:
                print(f"Diagnosis error: {ex}")
                close_sheet()
            page.update()

    # --- ИНТЕРФЕЙСНЫЕ ПАНЕЛИ ---

    def open_chat_interface(initial_text):
        ui_state["chat_messages"] = [{"role": "bot", "text": initial_text}]
        
        sheet_col.controls = [
            ft.Container(width=40, height=4, bgcolor="grey300", border_radius=2, margin=ft.margin.only(bottom=10)),
            ft.Row([
                ft.Text("Консультация", size=20, weight="bold"),
                ft.IconButton("close", icon_color="grey600", on_click=close_sheet)
            ], alignment="spaceBetween"),
            ft.Divider(height=1, color="#EEEEEE"),
            ft.Container(
                content=chat_display,
                height=400,
                padding=ft.padding.symmetric(vertical=10)
            ),
            ft.Row([
                chat_input,
                ft.IconButton(
                    "send", 
                    icon_color="white", 
                    bgcolor="#009753",
                    on_click=lambda _: send_chat_message()
                )
            ])
        ]
        update_chat_ui()
        sheet_container.offset = ft.Offset(0, 0)
        page.update()

    def show_existing_plants_dialog(e):
        u_id = user_state.get("id") or 1
        with next(get_db()) as db:
            plants = db.query(Plant).filter(Plant.user_id == u_id, Plant.is_active == 1).all()
        
        if not plants:
            page.snack_bar = ft.SnackBar(ft.Text("Ваш сад пока пуст!")); page.snack_bar.open = True; page.update()
            return

        def select_plant(p):
            dlg.open = False
            ui_state["current_plant_info"] = f"Растение: {p.custom_name}, Статус: {p.status_text}"
            loading_ring.visible = True
            page.update()
            
            def plant_task():
                ai = GigaChatService()
                with next(get_db()) as db:
                    res, _ = ai.ask_agronomist(db, u_id, ui_state["current_plant_info"], "Дай общие рекомендации по уходу.")
                    loading_ring.visible = False
                    if res:
                        open_chat_interface(res[0] if isinstance(res, tuple) else res)
                    page.update()
            threading.Thread(target=plant_task, daemon=True).start()

        list_items = [
            ft.ListTile(
                title=ft.Text(p.custom_name, weight="bold"),
                subtitle=ft.Text(f"Статус: {p.status_text}"),
                leading=ft.Icon("eco", color="#009753"),
                on_click=lambda _, plant=p: select_plant(plant)
            ) for p in plants
        ]

        dlg = ft.AlertDialog(
            title=ft.Text("Выберите растение"),
            content=ft.Column(list_items, scroll=True, height=350, tight=True),
            shape=ft.RoundedRectangleBorder(radius=20)
        )
        page.overlay.append(dlg); dlg.open = True; page.update()

    # --- ФАЙЛЫ ---

    def handle_file_result(e: ft.FilePickerResultEvent):
        if not e.files or not e.files[0]: return
        try:
            f_info = e.files[0]
            if f_info.path:
                with open(f_info.path, "rb") as f:
                    ui_state["image_bytes"] = f.read()
                main_img_view.src_base64 = base64.b64encode(ui_state["image_bytes"]).decode("utf-8")
                image_preview_card.visible = True
                instruction_container.visible = False
                loading_ring.visible = True
                page.update()
                threading.Thread(target=process_diagnosis_with_ai, daemon=True).start()
        except Exception as ex: print(f"File Error: {ex}")

    local_picker.on_result = handle_file_result

    # --- ВЕРСТКА ---

    main_img_view = ft.Image(src="", fit=ft.ImageFit.COVER, border_radius=15)
    image_preview_card = ft.Container(
        content=main_img_view, width=300, height=400, bgcolor="white", 
        padding=10, border_radius=25, visible=False,
        shadow=ft.BoxShadow(blur_radius=30, color=ft.Colors.with_opacity(0.1, "black"))
    )
    
    instruction_container = ft.Container(
        content=ft.Column([
            ft.Icon("camera_enhance_outlined", size=80, color="#E0E0E0"),
            ft.Text("GreenThumb AI Scanner", size=24, weight="bold"),
            ft.Text("Сделайте фото или выберите из списка", color="grey600", text_align="center")
        ], horizontal_alignment="center", spacing=10),
        alignment=ft.alignment.center
    )

    sheet_container = ft.Container(
        bgcolor="white", padding=25, border_radius=ft.border_radius.only(top_left=35, top_right=35),
        offset=ft.Offset(0, 1), animate_offset=ft.animation.Animation(600, ft.AnimationCurve.DECELERATE),
        shadow=ft.BoxShadow(blur_radius=40, color=ft.Colors.with_opacity(0.1, "black"))
    )
    sheet_col = ft.Column(horizontal_alignment="center", spacing=5)
    sheet_container.content = sheet_col

    action_buttons = ft.Container(
        content=ft.Row([
            ft.ElevatedButton("Фото", icon="add_a_photo", on_click=lambda _: [close_sheet(), local_picker.pick_files()]),
            ft.FloatingActionButton(icon="support_agent", bgcolor="#009753", on_click=show_existing_plants_dialog)
        ], alignment="center", spacing=25), bottom=80, left=0, right=0
    )

    return ft.View(
        route="/scanner", padding=0,
        controls=[
            ft.Stack(
                expand=True, 
                controls=[
                    ft.Container(expand=True, bgcolor="#FDFDFD"),
                    ft.Container(content=image_preview_card, alignment=ft.alignment.center),
                    instruction_container,
                    ft.Container(content=loading_ring, alignment=ft.alignment.center),
                    action_buttons,
                    ft.Container(content=sheet_container, bottom=0, left=0, right=0)
                ]
            )
        ]
    )