import flet as ft
from database.session import get_db
from services.auth_service import AuthService

# Аргумент is_register_mode определяет, какую форму показать первой
def AuthView(page: ft.Page, nav, user_state, is_register_mode=False):
    view = ft.View()
    view.route = "/auth"
    view.bgcolor = "white" # Заменили ft.colors.WHITE
    view.padding = 0
    view.scroll = ft.ScrollMode.AUTO 

    # Состояние экрана
    ui_state = {"is_login": not is_register_mode}

    def show_msg(text, color="red"):
        # В новых версиях Flet SnackBar лучше добавлять в overlay
        snack = ft.SnackBar(
            content=ft.Text(text, color="white"),
            bgcolor=color
        )
        page.overlay.append(snack)
        snack.open = True
        page.update()

    # --- ПОЛЯ ВВОДА ---
    name_input = ft.TextField(
        label="Имя", 
        visible=not ui_state["is_login"], 
        border_radius=15, 
        bgcolor="#F9F9F9",
        border_color="#E0E0E0", 
        focused_border_color="#009753",
        color="black" # Заменили ft.colors.BLACK
    )
    email_input = ft.TextField(
        label="Почта", 
        border_radius=15, 
        bgcolor="#F9F9F9",
        border_color="#E0E0E0", 
        focused_border_color="#009753",
        color="black", 
        value="test@mail.ru"
    )
    password_input = ft.TextField(
        label="Пароль", 
        password=True, 
        can_reveal_password=True,
        border_radius=15, 
        bgcolor="#F9F9F9", 
        border_color="#E0E0E0",
        focused_border_color="#009753", 
        color="black", 
        value="123"
    )

    # --- ТЕКСТОВЫЕ ЭЛЕМЕНТЫ ---
    initial_title = "Авторизация" if ui_state["is_login"] else "Регистрация"
    initial_btn = "Войти" if ui_state["is_login"] else "Создать аккаунт"
    initial_hint = "Нет аккаунта?" if ui_state["is_login"] else "Уже есть аккаунт?"
    initial_link = "Зарегистрируйтесь" if ui_state["is_login"] else "Войдите в систему"

    title_txt = ft.Text(value=initial_title, size=28, weight="bold", color="black")
    submit_btn_txt = ft.Text(value=initial_btn, color="white", weight="bold", size=16)
    toggle_hint = ft.Text(initial_hint, color="black")
    toggle_link = ft.Text(initial_link, color="#009753", weight="bold")

    def toggle_mode(e):
        ui_state["is_login"] = not ui_state["is_login"]
        name_input.visible = not ui_state["is_login"]
        title_txt.value = "Авторизация" if ui_state["is_login"] else "Регистрация"
        submit_btn_txt.value = "Войти" if ui_state["is_login"] else "Создать аккаунт"
        toggle_link.value = "Зарегистрируйтесь" if ui_state["is_login"] else "Войдите в систему"
        toggle_hint.value = "Нет аккаунта?" if ui_state["is_login"] else "Уже есть аккаунт?"
        view.update()

    def handle_auth(e):
        with next(get_db()) as db:
            try:
                if ui_state["is_login"]:
                    user = AuthService.login(db, email_input.value, password_input.value)
                    if user:
                        user_state["id"] = user.user_id
                        user_state["name"] = user.first_name
                        nav("/user_home")
                    else:
                        show_msg("Неверная почта или пароль")
                else:
                    user = AuthService.register(db, email_input.value, password_input.value, name_input.value)
                    if user:
                        user_state["id"] = user.user_id
                        user_state["name"] = user.first_name
                        nav("/user_home")
                    else:
                        show_msg("Ошибка регистрации")
            except Exception as ex:
                show_msg(f"Ошибка: {ex}")

    # Кнопка входа (исправленная версия)
    login_btn = ft.Container(
        content=submit_btn_txt, # Текст кнопки
        alignment=ft.alignment.center, # Центрируем текст внутри
        bgcolor="#009753", 
        padding=15, 
        border_radius=20,
        on_click=handle_auth, 
        width=float("inf")
    )
    
    # Формируем список контролов
    view.controls.append(
        ft.Container(
            content=ft.IconButton(ft.Icons.ARROW_BACK_IOS_NEW, icon_color="black", on_click=lambda _: nav("/")),
            padding=ft.padding.only(top=20, left=10)
        )
    )
    
    view.controls.append(
        ft.Container(
            padding=30,
            content=ft.Column([
                title_txt, 
                name_input, 
                email_input, 
                password_input,
                ft.Container(height=10), 
                login_btn,
                ft.GestureDetector(
                    content=ft.Row(
                        [toggle_hint, toggle_link], 
                        alignment=ft.MainAxisAlignment.CENTER
                    ),
                    on_tap=toggle_mode
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )
    )
    
    return view