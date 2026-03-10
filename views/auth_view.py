import flet as ft
from database.session import SessionLocal
from services.auth_service import AuthService

def AuthView(page: ft.Page, nav, user_state):
    view = ft.View()
    view.route = "/auth"
    view.bgcolor = ft.Colors.WHITE
    view.padding = 0
    # Автоматическая прокрутка — спасение для адаптива
    view.scroll = ft.ScrollMode.AUTO 

    # --- 1. КНОПКА НАЗАД ---
    back_btn = ft.Container(
        content=ft.IconButton(
            icon=ft.Icons.ARROW_BACK_IOS_NEW, 
            icon_color=ft.Colors.BLACK, 
            on_click=lambda _: nav("/")
        ),
        padding=ft.padding.only(top=20, left=10)
    )

    # --- 2. ПОЛЯ ВВОДА ---
    email_input = ft.TextField(
        label="Почта",
        border_radius=15,
        border_color="#E0E0E0",
        focused_border_color="#009753",
        bgcolor="#F9F9F9",
        color=ft.Colors.BLACK,
        label_style=ft.TextStyle(color=ft.Colors.GREY),
        value="test@mail.ru"
    )

    password_input = ft.TextField(
        label="Пароль",
        password=True,
        can_reveal_password=True,
        border_radius=15,
        border_color="#E0E0E0",
        focused_border_color="#009753",
        bgcolor="#F9F9F9",
        color=ft.Colors.BLACK,
        label_style=ft.TextStyle(color=ft.Colors.GREY),
        value="123"
    )

    error_txt = ft.Text(value="", color=ft.Colors.RED, size=12)

    def login_click(e):
        db = SessionLocal()
        try:
            user = AuthService.login(db, email_input.value, password_input.value)
            if user:
                user_state["id"] = user.user_id
                user_state["name"] = user.first_name
                nav("/user_home")
            else:
                error_txt.value = "Неверная почта или пароль"
                error_txt.update()
        except Exception as ex:
            error_txt.value = f"Ошибка: {ex}"
            error_txt.update()
        finally:
            db.close()

    # --- 3. КНОПКА ВОЙТИ ---
    login_btn = ft.Container(
        content=ft.Text(value="Войти", color=ft.Colors.WHITE, weight="bold", size=16),
        bgcolor="#009753",
        padding=15,
        border_radius=20,
        alignment=ft.Alignment(0, 0), # Центр
        on_click=login_click,
        width=float("inf") # Растягивается внутри колонки
    )

    # --- 4. ЦЕНТРАЛЬНАЯ КОЛОНКА (ФОРМА) ---
    # Ограничиваем ширину формы, чтобы она не "плыла" в браузере
    form_content = ft.Column(
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=20,
        controls=[
            ft.Text(value="Авторизация", size=28, weight="bold", color=ft.Colors.BLACK),
            ft.Container(height=10), # Отступ
            email_input,
            password_input,
            error_txt,
            login_btn,
            ft.Row(
                controls=[
                    ft.Text("Нет аккаунта?", color=ft.Colors.BLACK),
                    ft.Text("Зарегистрируйтесь", color="#009753", weight="bold")
                ],
                alignment=ft.MainAxisAlignment.CENTER
            )
        ]
    )

    # --- 5. СЕТКА ДЛЯ ЦЕНТРИРОВАНИЯ (СЕКРЕТ АДАПТИВА) ---
    # Мы создаем ResponsiveRow, где форма занимает 12 колонок на мобилке 
    # и только часть по центру на большом экране
    responsive_wrapper = ft.ResponsiveRow(
        alignment=ft.MainAxisAlignment.CENTER,
        controls=[
            ft.Container(
                col={"xs": 12, "sm": 8, "md": 6, "lg": 4}, # Ширина в зависимости от экрана
                padding=30,
                content=form_content
            )
        ]
    )

    # --- ФИНАЛЬНАЯ СБОРКА ---
    # Используем Column, чтобы кнопка "Назад" была сверху, а форма — под ней
    view.controls.append(back_btn)
    view.controls.append(responsive_wrapper)

    return view