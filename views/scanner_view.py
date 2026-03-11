import flet as ft
import threading
import base64
import os
from database.session import get_db
from database.models import Plant
from services.plant_services import PlantService
from services.ai_services import GigaChatService

def ScannerView(page: ft.Page, nav, user_state, _=None):
    local_picker = ft.FilePicker()
    if local_picker not in page.overlay:
        page.overlay.append(local_picker)
    
    # Состояние интерфейса
    ui_state = {
        "image_bytes": None, 
        "catalog_data": None, 
        "mode": "identify",
        "current_plant_info": "",
    }
    
    error_text = ft.Text(color="red", weight="bold", visible=False, text_align="center")
    loading_ring = ft.ProgressRing(visible=False, color="#009753", width=40, height=40)

    # --- ЭЛЕМЕНТЫ ИНТЕРФЕЙСА ---
    
    # Красивое минималистичное окно для фото
    main_image = ft.Image(
        src="", 
        fit=ft.ImageFit.COVER, 
        border_radius=15,
    )

    image_preview_card = ft.Container(
        content=main_image,
        width=280,
        height=350,
        bgcolor="white",
        padding=10,
        border_radius=25,
        shadow=ft.BoxShadow(
            blur_radius=30,
            color=ft.Colors.with_opacity(0.2, "black"),
            offset=ft.Offset(0, 10),
        ),
        visible=False,
        animate_opacity=300,
    )

    name_edit_field = ft.TextField(label="Название вида", border_color="#009753")
    height_field = ft.TextField(label="Рост (см)", value="10", width=100, border_color="#009753")
    
    chat_display = ft.Column(scroll=ft.ScrollMode.ALWAYS, expand=True, spacing=10)
    chat_input = ft.TextField(
        hint_text="Спросите агронома...", 
        expand=True, 
        border_radius=10,
        on_submit=lambda _: send_chat_message()
    )

    # --- ЛОГИКА ---

    def on_file_picked(e: ft.FilePickerResultEvent):
        if not e.files or not e.files[0]: return
        try:
            file_info = e.files[0]
            if file_info.path and os.path.exists(file_info.path):
                with open(file_info.path, "rb") as f: ui_state["image_bytes"] = f.read()
            elif file_info.content: ui_state["image_bytes"] = bytes(file_info.content)
            
            # Обновляем превью
            main_image.src_base64 = base64.b64encode(ui_state["image_bytes"]).decode("utf-8")
            image_preview_card.visible = True
            instruction_container.visible = False
            error_text.visible = False
            loading_ring.visible = True
            page.update()
            
            target = process_image_with_ai if ui_state["mode"] == "identify" else process_diagnosis_with_ai
            threading.Thread(target=target, daemon=True).start()
        except Exception as ex: print(f"Ошибка: {ex}")

    local_picker.on_result = on_file_picked

    def process_image_with_ai():
        ai = GigaChatService(); u_id = user_state.get("id") or 1
        with next(get_db()) as db:
            result, err = ai.identify_plant_photo(db, u_id, ui_state["image_bytes"])
            loading_ring.visible = False
            if result:
                ui_state["catalog_data"] = result
                populate_identify_sheet(result)
            else:
                error_text.value = "ИИ не узнал растение."; error_text.visible = True
            page.update()

    def process_diagnosis_with_ai():
        ai = GigaChatService(); u_id = user_state.get("id") or 1
        with next(get_db()) as db:
            res_text, err = ai.diagnose_plant(db, u_id, ui_state["image_bytes"])
            loading_ring.visible = False
            if res_text:
                ui_state["current_plant_info"] = "Новое растение по фото"
                open_chat_interface(res_text)
            else:
                error_text.value = "Ошибка диагностики."; error_text.visible = True
            page.update()

    def send_chat_message():
        if not chat_input.value: return
        user_msg = chat_input.value
        chat_input.value = ""
        chat_display.controls.append(ft.Container(
            content=ft.Text(f"Вы: {user_msg}", color="white"),
            bgcolor="#009753", padding=10, border_radius=10, alignment=ft.alignment.center_right
        ))
        page.update()
        
        def ai_thread():
            ai = GigaChatService(); u_id = user_state.get("id") or 1
            with next(get_db()) as db:
                res, err = ai.ask_agronomist(db, u_id, ui_state["current_plant_info"], user_msg)
                if res:
                    content = res[0] if isinstance(res, tuple) else res
                    chat_display.controls.append(ft.Container(
                        content=ft.Text(f"Агроном: {content}"),
                        bgcolor="#F0F4F8", padding=10, border_radius=10
                    ))
                page.update()
        threading.Thread(target=ai_thread, daemon=True).start()

    # --- ШТОРКИ ---

    def populate_identify_sheet(data):
        name_edit_field.value = data.get('species_name', '')
        sheet_col.controls = [
            ft.Container(width=40, height=4, bgcolor="grey300", border_radius=2),
            ft.Text("Найдено растение", size=18, weight="bold"),
            name_edit_field,
            ft.Row([ft.Text("Рост:"), height_field], alignment="center"),
            ft.ElevatedButton("Добавить в сад", bgcolor="#009753", color="white", width=250, 
                              on_click=lambda _: save_plant())
        ]
        sheet_container.offset = ft.Offset(0, 0); page.update()

    def open_chat_interface(initial_text):
        chat_display.controls.clear()
        chat_display.controls.append(ft.Container(
            content=ft.Text(initial_text),
            padding=15, bgcolor="#E8F5E9", border_radius=15
        ))
        sheet_col.controls = [
            ft.Container(width=40, height=4, bgcolor="grey300", border_radius=2),
            ft.Text("Чат с агрономом", weight="bold"),
            ft.Container(content=chat_display, height=300),
            ft.Row([chat_input, ft.IconButton(ft.Icons.SEND_ROUNDED, icon_color="#009753", on_click=lambda _: send_chat_message())])
        ]
        sheet_container.offset = ft.Offset(0, 0); page.update()

    # --- ДИАЛОГ ВЫБОРА ---

    def show_existing_plants_dialog(e):
        u_id = user_state.get("id") or 1
        with next(get_db()) as db:
            plants = db.query(Plant).filter(Plant.user_id == u_id, Plant.is_active == 1).all()
        
        if not plants:
            error_text.value = "Сад пуст. Сначала добавьте растение."; error_text.visible = True
            page.update(); return

        def select_and_diagnose(p):
            dlg.open = False
            ui_state["current_plant_info"] = f"Растение: {p.custom_name}, Состояние: {p.status_text}"
            loading_ring.visible = True; page.update()
            
            def text_diag():
                ai = GigaChatService()
                with next(get_db()) as db:
                    res, err = ai.ask_agronomist(db, u_id, ui_state["current_plant_info"], "Сделай краткий обзор состояния.")
                    loading_ring.visible = False
                    open_chat_interface(res[0] if res else "Ошибка")
            threading.Thread(target=text_diag, daemon=True).start()

        dlg = ft.AlertDialog(
            title=ft.Text("Выберите растение"),
            content=ft.Column([ft.ListTile(title=ft.Text(p.custom_name), on_click=lambda _, p=p: select_and_diagnose(p)) for p in plants], scroll=True, height=300, tight=True),
        )
        page.overlay.append(dlg); dlg.open = True; page.update()

    # --- СБОРКА ЭКРАНА ---

    instruction_container = ft.Container(
        content=ft.Column([
            ft.Icon(ft.Icons.CAMERA_ENHANCE_OUTLINED, size=50, color="#BDBDBD"),
            ft.Text("GreenThumb Scanner", size=20, weight="bold", color="black"),
            ft.Text("Сфоткайте новое или выберите из сада", color="grey700"),
        ], horizontal_alignment="center"),
        alignment=ft.alignment.center
    )

    sheet_container = ft.Container(
        bgcolor="white", padding=20, border_radius=ft.border_radius.only(top_left=30, top_right=30),
        offset=ft.Offset(0, 1), animate_offset=ft.animation.Animation(600, ft.AnimationCurve.DECELERATE),
    )
    sheet_col = ft.Column(horizontal_alignment="center", spacing=10)
    sheet_container.content = sheet_col

    action_buttons = ft.Container(
        content=ft.Row([
            ft.ElevatedButton(
                "Новое фото", 
                icon=ft.Icons.ADD_A_PHOTO, 
                on_click=lambda _: [ui_state.__setitem__("mode", "identify"), local_picker.pick_files()],
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12))
            ),
            ft.FloatingActionButton(
                icon=ft.Icons.SUPPORT_AGENT, 
                bgcolor="#009753", 
                on_click=show_existing_plants_dialog
            )
        ], alignment="center", spacing=20),
        bottom=100, left=0, right=0
    )

    def save_plant():
        # Твоя логика перехода
        nav("/my_plants")

    return ft.View(
        route="/scanner", padding=0,
        controls=[
            ft.Stack(expand=True, controls=[
                ft.Container(expand=True, bgcolor="#F8F9FA"), # Светлый чистый фон
                ft.Container(content=image_preview_card, alignment=ft.alignment.center),
                instruction_container,
                ft.Container(content=loading_ring, alignment=ft.alignment.center),
                action_buttons,
                ft.Container(content=sheet_container, bottom=0, left=0, right=0)
            ])
        ]
    )