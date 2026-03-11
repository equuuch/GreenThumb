import flet as ft
import base64
import threading
from database.session import get_db
from database.models import Plant
from services.ai_services import GigaChatService
from datetime import datetime

def AddPlantView(page: ft.Page, nav, user_state):
    img_bytes = page.session.get("pending_image")
    
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
        label="Рост растения (см)", 
        hint_text="Например: 15",
        keyboard_type=ft.KeyboardType.NUMBER,
        border_radius=15,
        bgcolor="#F5F5F5",
        focused_border_color="#009753"
    )

    ai_loader = ft.ProgressBar(visible=False, color="#009753")
    ai_status = ft.Text("", size=12, italic=True, color="grey600")

    def auto_detect_name():
        if not img_bytes:
            return
            
        ai_loader.visible = True
        ai_status.value = "ИИ анализирует фото..."
        ai_status.color = "grey600"
        page.update()
            
        try:
            ai = GigaChatService()
            # Пытаемся получить ответ
            res_data = ai.diagnose_plant(next(get_db()), user_state.get("id", 1), img_bytes)
            
            # Тщательная проверка ответа
            if res_data is not None:
                full_text = res_data[0] if isinstance(res_data, tuple) else res_data
                
                if full_text and "Вид растения:" in full_text:
                    detected_name = full_text.split("Вид растения:")[1].split("\n")[0].strip()
                elif full_text:
                    detected_name = full_text.split('\n')[0].split('.')[0].strip()
                else:
                    detected_name = ""

                if detected_name:
                    name_field.value = detected_name
                    ai_status.value = "Растение определено успешно!"
                    ai_status.color = "green"
                else:
                    ai_status.value = "ИИ не смог распознать название."
            else:
                ai_status.value = "Сервер ИИ занят (429). Попробуйте позже."
                ai_status.color = "orange"
                
        except Exception as e:
            print(f"Ошибка в потоке ИИ: {e}")
            ai_status.value = "Ошибка связи с GigaChat"
            ai_status.color = "red"
        finally:
            ai_loader.visible = False
            page.update()

    # Кнопка для ручного повтора запроса к ИИ
    retry_btn = ft.TextButton(
        "Повторить анализ", 
        icon=ft.Icons.REFRESH, 
        on_click=lambda _: threading.Thread(target=auto_detect_name, daemon=True).start()
    )

    # Первый запуск при загрузке страницы
    threading.Thread(target=auto_detect_name, daemon=True).start()

    def save_to_db(e):
        if not name_field.value:
            page.snack_bar = ft.SnackBar(ft.Text("Введите название!"), bgcolor="orange")
            page.snack_bar.open = True
            page.update()
            return

        save_btn.disabled = True
        save_btn.content = ft.ProgressRing(width=20, height=20, color="white")
        page.update()

        try:
            with next(get_db()) as db:
                new_plant = Plant(
                    user_id=user_state.get("id", 2),
                    custom_name=name_field.value,
                    status_text=f"Рост: {height_field.value or '0'} см", 
                    is_active=1,
                    added_at=datetime.now()
                )
                db.add(new_plant)
                db.commit()
                
            page.session.remove("pending_image")
            page.snack_bar = ft.SnackBar(ft.Text("Сохранено в сад!"), bgcolor="#009753")
            page.snack_bar.open = True
            nav("/my_plants")
            
        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text("Ошибка сохранения"), bgcolor="red")
            page.snack_bar.open = True
            save_btn.disabled = False
            save_btn.content = ft.Text("Сохранить в сад", size=16, weight="bold")
        page.update()

    save_btn = ft.ElevatedButton(
        content=ft.Text("Сохранить в сад", size=16, weight="bold"),
        bgcolor="#009753", color="white", height=50, on_click=save_to_db,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=15))
    )

    return ft.View(
        route="/add_plant",
        bgcolor="white",
        controls=[
            ft.AppBar(
                title=ft.Text("Новый питомец", color="black"),
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
                    
                    ft.Row([ai_status, retry_btn], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ai_loader,
                    
                    ft.Text("Детали", size=18, weight="bold"),
                    name_field,
                    height_field,
                    
                    ft.Container(height=10),
                    save_btn
                ], 
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                scroll=ft.ScrollMode.ADAPTIVE,
                spacing=10
                ),
                padding=20,
                expand=True
            )
        ]
    )