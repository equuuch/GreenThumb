import flet as ft
from database.session import get_db
from services.auth_service import AuthService

def AuthView(page: ft.Page, nav, user_state):
    view = ft.View()
    view.route = "/auth"
    view.bgcolor = ft.Colors.WHITE
    view.padding = 0
    view.scroll = ft.ScrollMode.AUTO 

    # ЛОКАЛЬНОЕ СОСТОЯНИЕ (Обычный словарь вместо Ref)
    ui_state = {"is_login": True}

    def show_msg(text, color=ft.Colors.RED):
        page.snack_bar = ft.SnackBar(
            content=ft.Text(text, color=ft.Colors.WHITE),
            bgcolor=color
        )
        page.snack_bar.open = True
        page.update()

    # --- ПОЛЯ ВВОДА ---
    name_input = ft.TextField(
        label="Имя", visible=False, border_radius=15, bgcolor="#F9F9F9",
        border_color="#E0E0E0", focused_border_color="#009753",
        color=ft.Colors.BLACK
    )
    email_input = ft.TextField(
        label="Почта", border_radius=15, bgcolor="#F9F9F9",
        border_color="#E0E0E0", focused_border_color="#009753",
        color=ft.Colors.BLACK, value="test@mail.ru"
    )
    password_input = ft.TextField(
        label="Пароль", password=True, can_reveal_password=True,
        border_radius=15, bgcolor="#F9F9F9", border_color="#E0E0E0",
        focused_border_color="#009753", color=ft.Colors.BLACK, value="123"
    )

    title_txt = ft.Text(value="Авторизация", size=28, weight="bold", color=ft.Colors.BLACK)
    submit_btn_txt = ft.Text(value="Войти", color=ft.Colors.WHITE, weight="bold", size=16)
    toggle_hint = ft.Text("Нет аккаунта?", color=ft.Colors.BLACK)
    toggle_link = ft.Text("Зарегистрируйтесь", color="#009753", weight="bold")

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

    login_btn = ft.Container(
        content=submit_btn_txt, bgcolor="#009753", padding=15, border_radius=20,
        alignment=ft.Alignment(0, 0), on_click=handle_auth, width=float("inf")
    )

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
                title_txt, name_input, email_input, password_input,
                ft.Container(height=10), login_btn,
                ft.GestureDetector(
                    content=ft.Row([toggle_hint, toggle_link], alignment="center"),
                    on_tap=toggle_mode
                )
            ], horizontal_alignment="center")
        )
    )
    return view