import flet as ft
import base64
import threading
import os
import uuid
from database.session import get_db
from database.models import Plant
from services.ai_services import GigaChatService
from services.plant_services import PlantService  # Импортируем наш сервис
from datetime import datetime

def AddPlantView(page: ft.Page, nav, user_state):
    """
    Версия 2.8: Полная интеграция с PlantService и автоматическое создание задач.
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
    
    # Переменная для ID из каталога (теперь управляется сервисом, но оставим для логов)
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
            # Используем обновленный метод идентификации
            res_data, err = ai.identify_plant_photo(next(get_db()), user_state.get("id", 1), img_bytes)
            
            if res_data:
                # В res_data теперь должен приходить чистый JSON с именем
                detected_name = res_data.get("common_name") or res_data.get("species_name")
                
                if detected_name:
                    name_field.value = detected_name
                    ai_status.value = "Растение определено успешно!"
                    ai_status.color = "green"
            else:
                ai_status.value = "ИИ не смог точно определить вид"
                ai_status.color = "orange"

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
            page.overlay.append(ft.SnackBar(ft.Text("Заполните все поля!"), bgcolor="orange"))
            page.update()
            return

        save_btn.disabled = True
        save_btn.content = ft.ProgressRing(width=20, height=20, color="white")
        page.update()

        try:
            with next(get_db()) as db:
                ai_service = GigaChatService()
                user_id = user_state.get("id", 1)

                # 1. Получаем или создаем запись в каталоге через сервис
                # Если названия нет в БД, ИИ сам сгенерирует паспорт
                catalog_item, err = PlantService.get_or_create_catalog_item(
                    db, ai_service, user_id, name_field.value
                )
                
                if err:
                    raise Exception(f"Ошибка каталога: {err}")

                # 2. Подготавливаем данные для создания растения
                catalog_data = {
                    'species_name': catalog_item.species_name,
                    'latin_name': catalog_item.latin_name,
                    'description': catalog_item.description,
                    'watering_interval': catalog_item.default_watering_interval,
                    'light_level': catalog_item.default_light_level
                }

                # 3. Создаем растение и автоматическую задачу на сегодня
                new_plant, plant_err = PlantService.confirm_and_create_plant(
                    db,
                    user_id=user_id,
                    catalog_data=catalog_data,
                    custom_name=name_field.value,
                    image_bytes=img_bytes
                )

                if plant_err:
                    raise Exception(plant_err)

            # Очистка сессии
            for key in ["pending_image", "pending_light", "use_ai_recognition"]:
                page.session.remove(key)

            # Выводим уведомление и уходим в список
            page.overlay.append(ft.SnackBar(ft.Text("Растение и график ухода созданы!"), bgcolor="#009753"))
            nav("/my_plants")
            
        except Exception as ex:
            print(f"Save error: {ex}")
            page.overlay.append(ft.SnackBar(ft.Text(f"Ошибка: {str(ex)}"), bgcolor="red"))
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
                # Добавим скролл на случай маленьких экранов
                scroll=ft.ScrollMode.ADAPTIVE,
                spacing=15
                ),
                padding=20,
                expand=True
            )
        ]
    )