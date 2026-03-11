import flet as ft
import base64
import threading
import os
import uuid
from database.session import get_db
from database.models import Plant
from services.ai_services import GigaChatService
from datetime import datetime

def AddPlantView(page: ft.Page, nav, user_state):
    """
    Версия 2.7: Исправлено мгновенное позеленение шкалы и привязка к каталогу.
    """
    img_bytes = page.session.get("pending_image")
    use_ai = page.session.get("use_ai_recognition")
    selected_light = page.session.get("pending_light") or 0.5
    
    # Поля ввода
    name_field = ft.TextField(
        label="Название растения", 
        hint_text="Введите вручную или подождите ИИ",
        border_radius=15,
        bgcolor="#F5F5F5",
        focused_border_color="#009753",
        prefix_icon=ft.Icons.AUTO_AWESOME
    )
    
    height_field = ft.TextField(
        label="Рост растения (см) *", 
        hint_text="Например: 15",
        value="10",
        keyboard_type=ft.KeyboardType.NUMBER,
        border_radius=15,
        bgcolor="#F5F5F5",
        focused_border_color="#009753"
    )

    ai_loader = ft.ProgressBar(visible=False, color="#009753")
    ai_status = ft.Text("", size=12, italic=True, color="grey600")
    
    # Переменная для ID из каталога
    detected_cat_id = [None] 

    def auto_detect_name():
        if not img_bytes:
            return
            
        ai_loader.visible = True
        ai_status.value = "ИИ анализирует фото..."
        ai_status.color = "grey600"
        page.update()
            
        try:
            ai = GigaChatService()
            # Получаем кортеж (текст, catalog_id)
            res_data = ai.diagnose_plant(next(get_db()), user_state.get("id", 1), img_bytes)
            
            if res_data:
                full_text = res_data[0] if isinstance(res_data, tuple) else res_data
                if isinstance(res_data, tuple) and len(res_data) > 1:
                    detected_cat_id[0] = res_data[1] # Сохраняем найденный ID
                
                # Парсинг названия
                if "Вид растения:" in full_text:
                    detected_name = full_text.split("Вид растения:")[1].split("\n")[0].strip()
                else:
                    detected_name = full_text.split('\n')[0].split('.')[0].strip()

                if detected_name:
                    name_field.value = detected_name
                    ai_status.value = "Растение определено успешно!"
                    ai_status.color = "green"
        except Exception as e:
            print(f"Ошибка в потоке ИИ: {e}")
            ai_status.value = "Ошибка связи с GigaChat"
            ai_status.color = "red"
        finally:
            ai_loader.visible = False
            page.update()

    if use_ai is True:
        threading.Thread(target=auto_detect_name, daemon=True).start()

    def save_to_db(e):
        if not name_field.value or not height_field.value:
            page.snack_bar = ft.SnackBar(ft.Text("Заполните все поля!"), bgcolor="orange")
            page.snack_bar.open = True
            page.update()
            return

        save_btn.disabled = True
        save_btn.content = ft.ProgressRing(width=20, height=20, color="white")
        page.update()

        # Сохранение фото
        db_path = ""
        if img_bytes:
            try:
                if not os.path.exists("assets/plants"):
                    os.makedirs("assets/plants")
                filename = f"{uuid.uuid4().hex}.jpg"
                file_path = os.path.join("assets/plants", filename)
                with open(file_path, "wb") as f:
                    f.write(img_bytes)
                db_path = f"/plants/{filename}"
            except Exception as file_ex:
                print(f"Ошибка файла: {file_ex}")

        # Запись в базу
        try:
            with next(get_db()) as db:
                new_plant = Plant(
                    user_id=user_state.get("id", 1),
                    catalog_id=detected_cat_id[0], # Привязываем к каталогу, если ИИ нашел
                    custom_name=name_field.value,
                    image_url=db_path,
                    status_text=f"Рост: {height_field.value} см", 
                    user_light_level=selected_light,
                    is_active=1,
                    # ВАЖНО: Ставим текущее время полива сразу!
                    last_watered_at=datetime.now(),
                    added_at=datetime.now()
                )
                db.add(new_plant)
                db.commit()
                
            # Очистка сессии
            for key in ["pending_image", "pending_light", "use_ai_recognition"]:
                page.session.remove(key)

            page.snack_bar = ft.SnackBar(ft.Text("Растение добавлено в сад!"), bgcolor="#009753")
            page.snack_bar.open = True
            nav("/my_plants") # Сразу в список, чтобы увидеть результат
            
        except Exception as ex:
            print(f"Save error: {ex}")
            save_btn.disabled = False
            save_btn.content = ft.Text("Сохранить в сад", size=16, weight="bold")
            page.update()

    save_btn = ft.ElevatedButton(
        content=ft.Text("Сохранить в сад", size=16, weight="bold"),
        bgcolor="#009753", color="white", height=50, on_click=save_to_db,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=15))
    )

    retry_btn = ft.TextButton(
        "Повторить анализ", 
        icon=ft.Icons.REFRESH, 
        on_click=lambda _: threading.Thread(target=auto_detect_name, daemon=True).start()
    )

    return ft.View(
        route="/add_plant",
        bgcolor="white",
        controls=[
            ft.AppBar(
                title=ft.Text("Новое растение", color="black", weight="bold"),
                bgcolor="transparent",
                leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=lambda _: nav("/scanner"))
            ),
            ft.Container(
                content=ft.Column([
                    ft.Container(
                        content=ft.Image(
                            src_base64=base64.b64encode(img_bytes).decode() if img_bytes else "",
                            width=280, height=280, fit=ft.ImageFit.COVER, border_radius=20,
                        ) if img_bytes else ft.Icon(ft.Icons.IMAGE_NOT_SUPPORTED, size=100),
                        alignment=ft.alignment.center,
                    ),
                    ft.Row([
                        ai_status, 
                        ft.Text(f"Свет: {int(selected_light*100)}%", size=12, weight="bold")
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ai_loader,
                    name_field,
                    height_field,
                    ft.Container(height=10),
                    save_btn,
                    retry_btn if use_ai else ft.Container()
                ], 
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                scroll=ft.ScrollMode.ADAPTIVE,
                spacing=15
                ),
                padding=20,
                expand=True
            )
        ]
    )