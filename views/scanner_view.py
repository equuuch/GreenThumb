import flet as ft
import threading
import base64
from database.session import get_db
from services.plant_services import PlantService
from services.ai_services import GigaChatService

def ScannerView(page: ft.Page, nav, user_state):
    ui_state = {"image_bytes": None, "catalog_data": None}

    def show_msg(text, color="red"):
        page.snack_bar = ft.SnackBar(content=ft.Text(text, color="white"), bgcolor=color)
        page.snack_bar.open = True
        page.update()

    def on_file_picked(e: ft.FilePickerResultEvent):
        if e.files:
            try:
                # В 0.25.2 путь к файлу берется именно так
                with open(e.files[0].path, "rb") as f:
                    ui_state["image_bytes"] = f.read()
                
                main_image.src_base64 = base64.b64encode(ui_state["image_bytes"]).decode("utf-8")
                loading_ring.visible = True
                page.update()
                
                threading.Thread(target=process_image_with_ai, daemon=True).start()
            except Exception as ex:
                show_msg(f"Ошибка загрузки: {ex}")

    # ВАЖНО: Создаем и регистрируем пикер ДО сборки UI
    file_picker = ft.FilePicker(on_result=on_file_picked)
    page.overlay.append(file_picker)
    page.update() # Принудительно регистрируем его в системе

    def process_image_with_ai():
        ai = GigaChatService()
        u_id = user_state.get("id") or 1
        try:
            with next(get_db()) as db:
                result, err = ai.identify_plant_photo(db, u_id, ui_state["image_bytes"])
                loading_ring.visible = False
                if err: 
                    show_msg(err)
                elif result:
                    ui_state["catalog_data"] = result
                    populate_sheet(result)
                page.update()
        except Exception as e:
            loading_ring.visible = False
            show_msg(f"Ошибка ИИ: {e}")
            page.update()

    main_image = ft.Image(src="https://picsum.photos/800/1200", fit=ft.ImageFit.COVER)
    loading_ring = ft.ProgressRing(visible=False, color="#009753")
    
    sheet_container = ft.Container(
        bgcolor="#F4F4F4", 
        padding=30, 
        width=1000, 
        height=450,
        border_radius=ft.border_radius.only(top_left=30, top_right=30),
        offset=ft.Offset(0, 0.85), 
        animate_offset=ft.animation.Animation(600, ft.AnimationCurve.DECELERATE)
    )
    sheet_col = ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    sheet_container.content = sheet_col

    def populate_sheet(data):
        sheet_col.controls = [
            ft.Container(width=40, height=4, bgcolor="grey300", border_radius=2),
            ft.Text(data.get('species_name', 'Растение'), size=24, weight="bold", color="black"),
            ft.Text("Обнаружено ИИ", size=14, color="grey600"),
            ft.Divider(height=20, color="transparent"),
            ft.ElevatedButton(
                "Добавить в мой сад", 
                bgcolor="#009753", 
                color="white", 
                on_click=lambda _: save_plant()
            )
        ]
        sheet_container.offset = ft.Offset(0, 0.3)
        page.update()

    def save_plant():
        if not ui_state["catalog_data"]: return
        with next(get_db()) as db:
            PlantService.confirm_and_create_plant(
                db, user_state.get("id") or 1, ui_state["catalog_data"], 
                image_bytes=ui_state["image_bytes"]
            )
            nav("/my_plants")

    # Сборка экрана с использованием Stack на весь экран
    return ft.View(
        route="/scanner",
        padding=0,
        controls=[
            ft.Stack(
                expand=True, # Обязательно для Stack во весь экран
                controls=[
                    # Фоновое изображение
                    ft.Container(expand=True, bgcolor="black", content=main_image),
                    
                    # Индикатор загрузки
                    ft.Container(content=loading_ring, alignment=ft.alignment.center),
                    
                    # Плашка с информацией (снизу)
                    ft.Container(content=sheet_container, bottom=0, left=0, right=0),
                    
                    # Кнопка камеры (позиционируем через Container в Stack)
                    ft.Container(
                        content=ft.FloatingActionButton(
                            icon=ft.icons.CAMERA_ALT, 
                            bgcolor="#009753",
                            # Вызываем pick_files через лямбду
                            on_click=lambda _: file_picker.pick_files()
                        ),
                        bottom=140, 
                        right=20
                    )
                ]
            )
        ]
    )