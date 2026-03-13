import flet as ft
from database.session import get_db
from services.auth_service import AuthService

def AuthView(page: ft.Page, nav, user_state, is_register_mode=False):
    """
    модуль аутентификации и регистрации пользователей.
    реализует логику управления доступом и интеграцию с сервисным слоем authservice.
    """
    
    # программное управление жизненным циклом навигационной панели.
    # скрытие навбара необходимо для исключения несанкционированного доступа к разделам приложения до авторизации.
    saved_navbar = None
    if page.navigation_bar:
        saved_navbar = page.navigation_bar
        page.navigation_bar.visible = False
        page.update()

    # конфигурация вьюхи как автономного контейнера с поддержкой вертикальной прокрутки.
    view = ft.View()
    view.route = "/auth"
    view.bgcolor = "white"
    view.padding = 0
    view.scroll = ft.ScrollMode.AUTO 

    # инициализация локального состояния экрана.
    # переменная is_login определяет текущую схему отображения (авторизация или создание аккаунта).
    ui_state = {"is_login": not is_register_mode}

    def show_msg(text, color="#FF5252"):
        """универсальный метод вывода системных уведомлений через компонент snackbar."""
        snack = ft.SnackBar(content=ft.Text(text, color="white"), bgcolor=color)
        page.overlay.append(snack)
        snack.open = True
        page.update()

    def restore_navbar_and_nav(route):
        """процедура восстановления состояния интерфейса перед переходом на защищенные маршруты."""
        if saved_navbar:
            page.navigation_bar = saved_navbar
            page.navigation_bar.visible = True
        nav(route)

    # --- инициализация компонентов ввода данных ---

    # поле ввода имени, отображаемое только в режиме регистрации (условный рендеринг).
    name_input = ft.TextField(
        label="Имя", visible=not ui_state["is_login"], 
        border_radius=15, bgcolor="#F9F9F9", border_color="#E0E0E0", 
        focused_border_color="#009753", color="black",
        prefix_icon=ft.Icons.PERSON_OUTLINE,
        text_style=ft.TextStyle(font_family="Montserrat")
    )
    
    # поле ввода адреса электронной почты.
    email_input = ft.TextField(
        label="Почта", border_radius=15, bgcolor="#F9F9F9",
        border_color="#E0E0E0", focused_border_color="#009753",
        color="black", value="test@mail.ru", prefix_icon=ft.Icons.EMAIL_OUTLINED,
        text_style=ft.TextStyle(font_family="Montserrat")
    )
    
    # поле ввода пароля с поддержкой функции маскирования и переключения видимости символов.
    password_input = ft.TextField(
        label="Пароль", password=True, can_reveal_password=True,
        border_radius=15, bgcolor="#F9F9F9", border_color="#E0E0E0",
        focused_border_color="#009753", color="black", value="123",
        prefix_icon=ft.Icons.LOCK_OUTLINE,
        text_style=ft.TextStyle(font_family="Montserrat")
    )

    # декларативное описание текстовых констант интерфейса.
    title_txt = ft.Text(value="Авторизация" if ui_state["is_login"] else "Регистрация", size=32, weight="bold", color="black")
    submit_btn_txt = ft.Text(value="Войти" if ui_state["is_login"] else "Создать аккаунт", color="white", weight="bold", size=16)
    toggle_hint = ft.Text("Нет аккаунта?" if ui_state["is_login"] else "Уже есть аккаунт?", color="black")
    toggle_link = ft.Text("Зарегистрируйтесь" if ui_state["is_login"] else "Войдите в систему", color="#009753", weight="bold")

    def toggle_mode(e):
        """метод реактивного переключения режимов входа и регистрации без смены маршрута."""
        ui_state["is_login"] = not ui_state["is_login"]
        # синхронизация свойств видимости и текстовых значений компонентов.
        name_input.visible = not ui_state["is_login"]
        title_txt.value = "Авторизация" if ui_state["is_login"] else "Регистрация"
        submit_btn_txt.value = "Войти" if ui_state["is_login"] else "Создать аккаунт"
        toggle_link.value = "Зарегистрируйтесь" if ui_state["is_login"] else "Войдите в систему"
        toggle_hint.value = "Нет аккаунта?" if ui_state["is_login"] else "Уже есть аккаунт?"
        view.update() # полная перерисовка вьюхи.

    def handle_auth(e):
        """
        основной обработчик события отправки формы. 
        реализует валидацию, защиту от повторных кликов и вызов логики bll.
        """
        # первичная очистка и проверка обязательных полей.
        if not email_input.value.strip() or not password_input.value.strip():
            show_msg("Заполните почту и пароль")
            return

        # блокировка интерфейса на время обработки запроса (loading state).
        login_btn.disabled = True
        page.update()
        
        # использование генератора сессий для выполнения транзакции к базе данных.
        with next(get_db()) as db:
            try:
                if ui_state["is_login"]:
                    # запрос к сервису авторизации (проверка хеша и политики блокировок).
                    user, err_msg = AuthService.login(db, email_input.value.strip(), password_input.value.strip())
                    if user:
                        # обновление глобального состояния сессии пользователя.
                        user_state["id"] = user.user_id
                        user_state["name"] = user.first_name
                        restore_navbar_and_nav("/user_home")
                    else:
                        show_msg(err_msg) # вывод детализированной ошибки (напр. "аккаунт заблокирован").
                else:
                    # логика регистрации нового пользователя.
                    if not name_input.value.strip():
                        show_msg("Введите ваше имя")
                        return
                        
                    user, err_msg = AuthService.register(
                        db, 
                        email_input.value.strip(), 
                        password_input.value.strip(), 
                        name_input.value.strip()
                    )
                    if user:
                        user_state["id"] = user.user_id
                        user_state["name"] = user.first_name
                        restore_navbar_and_nav("/user_home")
                    else:
                        show_msg(err_msg)
            except Exception as ex:
                show_msg(f"Ошибка системы: {ex}")
            finally:
                # снятие блокировки с элементов управления.
                login_btn.disabled = False
                page.update()

    # построение интерактивного контейнера кнопки с применением стилистики бренда.
    login_btn = ft.Container(
        content=submit_btn_txt, alignment=ft.alignment.center, 
        bgcolor="#009753", padding=15, border_radius=18,
        on_click=handle_auth, width=float("inf")
    )
    
    # добавление кнопки возврата для гостевого доступа.
    view.controls.append(
        ft.Container(
            content=ft.IconButton(ft.Icons.ARROW_BACK_IOS_NEW, icon_color="black", on_click=lambda _: restore_navbar_and_nav("/")),
            padding=ft.padding.only(top=20, left=10)
        )
    )
    
    # финальная компоновка визуальной иерархии страницы в единый вертикальный стек.
    view.controls.append(
        ft.Container(
            padding=ft.padding.all(35),
            content=ft.Column([
                ft.Column([title_txt, ft.Text("Добро пожаловать в GreenThumb", color="grey600", size=14)], spacing=5),
                ft.Container(height=20),
                name_input, email_input, password_input,
                ft.Container(height=15), login_btn,
                ft.Container(height=10),
                # механизм переключения между формами через жест (gesture detector).
                ft.GestureDetector(
                    content=ft.Row([toggle_hint, toggle_link], alignment=ft.MainAxisAlignment.CENTER),
                    on_tap=toggle_mode
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.START, spacing=15)
        )
    )
    
    return view