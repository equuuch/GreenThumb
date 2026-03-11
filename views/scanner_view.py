import flet as ft
import threading
import base64
import os
from database.session import get_db
from services.plant_services import PlantService
from services.ai_services import GigaChatService

def ScannerView(page: ft.Page, nav, user_state, _=None):
    local_picker = ft.FilePicker()
    if local_picker not in page.overlay:
        page.overlay.append(local_picker)
    
    ui_state = {"image_bytes": None, "catalog_data": None}
    # Контрол для редактирования названия
    name_edit_field = ft.TextField(
        label="Название растения",
        border_color="#009753",
        focused_border_color="#009753",
        text_size=18,
        text_align=ft.TextAlign.CENTER
    )

    def on_file_picked(e: ft.FilePickerResultEvent):
        if not e.files or not e.files[0]: return
        try:
            file_info = e.files[0]
            if file_info.path and os.path.exists(file_info.path):
                with open(file_info.path, "rb") as f:
                    ui_state["image_bytes"] = f.read()
            elif file_info.content:
                ui_state["image_bytes"] = bytes(file_info.content)
            
            main_image.src_base64 = base64.b64encode(ui_state["image_bytes"]).decode("utf-8")
            main_image.opacity = 1.0
            instruction_container.visible = False
            loading_ring.visible = True
            page.update()
            
            threading.Thread(target=process_image_with_ai, daemon=True).start()
        except Exception as ex:
            print(f"Ошибка: {ex}")

    local_picker.on_result = on_file_picked

    def process_image_with_ai():
        ai = GigaChatService()
        u_id = user_state.get("id") or 1
        try:
            with next(get_db()) as db:
                result, err = ai.identify_plant_photo(db, u_id, ui_state["image_bytes"])
                loading_ring.visible = False
                if result:
                    ui_state["catalog_data"] = result
                    populate_sheet(result)
                page.update()
        except Exception as e:
            loading_ring.visible = False
            page.update()

    main_image = ft.Image(
        src="https://images.unsplash.com/photo-1491147334573-44cbb4602074?q=80&w=1000", 
        fit=ft.ImageFit.COVER,
        opacity=0.4
    )
    
    loading_ring = ft.ProgressRing(visible=False, color="#009753", width=50, height=50)

    instruction_container = ft.Container(
        padding=40,
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Icon(ft.Icons.FILTER_CENTER_FOCUS, size=80, color="white"),
                ft.Text("Умный сканер", size=28, weight="bold", color="white"),
                ft.Text(
                    "Сделайте фото камерой или выберите\nиз галереи. Имя можно будет изменить.", 
                    size=16, color="white70", text_align=ft.TextAlign.CENTER
                ),
            ]
        ),
        alignment=ft.alignment.center
    )
    
    sheet_container = ft.Container(
        bgcolor="white", padding=30, 
        border_radius=ft.border_radius.only(top_left=30, top_right=30),
        offset=ft.Offset(0, 1),
        animate_offset=ft.animation.Animation(600, ft.AnimationCurve.DECELERATE),
        shadow=ft.BoxShadow(blur_radius=20, color="black26")
    )
    sheet_col = ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15)
    sheet_container.content = sheet_col

    def populate_sheet(data):
        # Подставляем имя из ИИ в поле для редактирования
        name_edit_field.value = data.get('species_name', '')
        
        sheet_col.controls = [
            ft.Container(width=40, height=4, bgcolor="grey300", border_radius=2),
            ft.Text("Результат сканирования", size=14, color="grey600"),
            name_edit_field, # Поле ввода вместо обычного текста
            ft.Text(f"Точность определения: {data.get('confidence', 90)}%", color="#009753", size=12),
            ft.Divider(height=10, color="transparent"),
            ft.ElevatedButton(
                "Подтвердить и добавить", 
                bgcolor="#009753", color="white", 
                height=55, width=280,
                on_click=lambda _: save_plant()
            )
        ]
        sheet_container.offset = ft.Offset(0, 0)
        page.update()

    def save_plant():
        if not ui_state["catalog_data"]: return
        # ОБЯЗАТЕЛЬНО: Берем имя из текстового поля, а не из данных ИИ
        ui_state["catalog_data"]['species_name'] = name_edit_field.value
        
        with next(get_db()) as db:
            PlantService.confirm_and_create_plant(
                db, user_state.get("id") or 1, ui_state["catalog_data"], 
                image_bytes=ui_state["image_bytes"]
            )
            nav("/my_plants")

    return ft.View(
        route="/scanner",
        padding=0,
        controls=[
            ft.Stack(
                expand=True,
                controls=[
                    ft.Container(expand=True, bgcolor="black", content=main_image),
                    instruction_container,
                    ft.Container(content=loading_ring, alignment=ft.alignment.center),
                    ft.Container(
                        content=ft.ElevatedButton(
                            content=ft.Row([ft.Icon(ft.Icons.ADD_A_PHOTO), ft.Text(" Сделать фото / Выбрать файл ")], alignment="center"),
                            bgcolor="#009753", color="white", height=60, width=320,
                            on_click=lambda _: local_picker.pick_files()
                        ),
                        bottom=40, left=0, right=0, alignment=ft.alignment.center
                    ),
                    ft.Container(content=sheet_container, bottom=0, left=0, right=0)
                ]
            )
        ]
    )