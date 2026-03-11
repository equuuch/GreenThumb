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
    
    # Поля ввода для редактирования данных
    name_edit_field = ft.TextField(
        label="Название вида",
        border_color="#009753",
        text_size=16
    )
    # НОВОЕ: Поле для ввода начальной высоты
    height_field = ft.TextField(
        label="Начальная высота (см)",
        value="10", # Значение по умолчанию
        keyboard_type=ft.KeyboardType.NUMBER,
        border_color="#009753",
        width=150
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
        fit=ft.ImageFit.COVER, opacity=0.4
    )
    loading_ring = ft.ProgressRing(visible=False, color="#009753", width=50, height=50)

    instruction_container = ft.Container(
        content=ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Icon(ft.Icons.FILTER_CENTER_FOCUS, size=60, color="white"),
                ft.Text("Умный сканер", size=24, weight="bold", color="white"),
                ft.Text("Сделайте фото или выберите файл", color="white70"),
            ]
        ),
        alignment=ft.alignment.center
    )
    
    sheet_container = ft.Container(
        bgcolor="white", padding=20, 
        border_radius=ft.border_radius.only(top_left=30, top_right=30),
        offset=ft.Offset(0, 1),
        animate_offset=ft.animation.Animation(600, ft.AnimationCurve.DECELERATE),
    )
    sheet_col = ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10)
    sheet_container.content = sheet_col

    def populate_sheet(data):
        name_edit_field.value = data.get('species_name', '')
        sheet_col.controls = [
            ft.Container(width=40, height=4, bgcolor="grey300", border_radius=2),
            ft.Text("Настройка растения", size=18, weight="bold"),
            name_edit_field,
            ft.Row([ft.Text("Высота:"), height_field], alignment="center"),
            ft.ElevatedButton(
                "Добавить в коллекцию и замерить", 
                bgcolor="#009753", color="white", height=50, width=280,
                on_click=lambda _: save_plant_with_log()
            )
        ]
        sheet_container.offset = ft.Offset(0, 0)
        page.update()

    def save_plant_with_log():
        if not ui_state["catalog_data"]: return
        
        # 1. Берем исправленное имя
        ui_state["catalog_data"]['species_name'] = name_edit_field.value
        h_val = float(height_field.value) if height_field.value else 0.0
        u_id = user_state.get("id") or 1

        with next(get_db()) as db:
            # 2. Вызываем основную функцию создания (Бэкенд)
            plant, err = PlantService.confirm_and_create_plant(
                db, u_id, ui_state["catalog_data"], image_bytes=ui_state["image_bytes"]
            )
            
            if plant:
                # 3. СРАЗУ вызываем вторую функцию бэкенда для лога роста
                PlantService.add_measurement(
                    db, 
                    plant_id=plant.plant_id, 
                    height=h_val, 
                    note="Первичный замер при сканировании",
                    image_bytes=ui_state["image_bytes"] # Используем то же фото
                )
                nav("/my_plants")
            else:
                print(f"Ошибка сохранения: {err}")

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
                            "Выбрать фото / Камера", 
                            on_click=lambda _: local_picker.pick_files(),
                            bgcolor="#009753", color="white"
                        ),
                        bottom=40, left=0, right=0, alignment=ft.alignment.center
                    ),
                    ft.Container(content=sheet_container, bottom=0, left=0, right=0)
                ]
            )
        ]
    )