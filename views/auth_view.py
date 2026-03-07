import flet as ft

def AuthView(page: ft.Page):
    view = ft.View(route="/auth", bgcolor="white", padding=30)

    # Кнопка "Назад" возвращает на гостевую
    back_btn = ft.Container(
        content=ft.IconButton(
            icon=ft.Icons.ARROW_BACK_IOS_NEW, 
            icon_color="black", 
            on_click=lambda _: page.go("/") 
        ),
        alignment=ft.Alignment.TOP_LEFT,
        margin=ft.margin.only(bottom=20, left=-15)
    )

    title = ft.Text("Авторизация", size=26, weight="bold", color="black", text_align="center")

    email_input = ft.TextField(
        label="Почта",
        border_radius=15, border_color="black", focused_border_color="#009753",
        text_style=ft.TextStyle(color="black"), label_style=ft.TextStyle(color="gray"),
        cursor_color="#009753", bgcolor="#F9F9F9"
    )

    password_input = ft.TextField(
        label="Пароль", password=True, can_reveal_password=True,
        border_radius=15, border_color="black", focused_border_color="#009753",
        text_style=ft.TextStyle(color="black"), label_style=ft.TextStyle(color="gray"),
        cursor_color="#009753", bgcolor="#F9F9F9"
    )

    # Кнопка "Войти" теперь ведет на USER HOME (вход выполнен)
    login_btn = ft.Container(
        content=ft.Text("Войти", color="white", weight="bold", size=16),
        bgcolor="#009753",
        border_radius=20,
        padding=15,
        alignment=ft.Alignment.CENTER,
        on_click=lambda _: page.go("/user_home") # <--- ИЗМЕНЕНИЕ ЗДЕСЬ
    )

    forgot_pwd = ft.Text("Забыли пароль?", color="#009753", size=12, weight="bold")

    register_link = ft.Row(
        controls=[ft.Text("Нет аккаунта?", color="black", size=13),
                  ft.Text("Зарегистрируйтесь", color="#009753", size=13, weight="bold")], 
        alignment=ft.MainAxisAlignment.CENTER
    )

    view.controls.append(ft.Column(controls=[
        back_btn, ft.Container(height=10),
        ft.Container(content=title, alignment=ft.Alignment.CENTER),
        ft.Container(height=40), email_input, ft.Container(height=15), password_input,
        ft.Container(height=30), login_btn, ft.Container(height=20),
        ft.Container(content=forgot_pwd, alignment=ft.Alignment.CENTER),
        ft.Container(height=40), register_link
    ]))
    return view