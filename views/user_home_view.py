import flet as ft

def UserHomeView(page: ft.Page):
    view = ft.View(route="/user_home", bgcolor="#F9F9F9", padding=20)
    
    # 1. Шапка
    header = ft.Row(
        controls=[
            ft.Column(
                controls=[
                    ft.Text("Здравствуйте, Шахзод!", size=12, color="#6E6E6E"),
                    ft.Text("Ваш сад", size=26, weight="bold", color="black"),
                ],
                spacing=2
            ),
            ft.IconButton(icon=ft.Icons.NOTIFICATIONS_OUTLINED, icon_color="black", icon_size=28)
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
    )

    # 2. Полоска здоровья (Исправленная версия с int)
    def create_custom_bar(percentage):
        # Превращаем 0.4 -> 40 (целое число)
        green_part = int(percentage * 100)
        gray_part = 100 - green_part
        
        return ft.Row(
            controls=[
                ft.Container(
                    bgcolor="#009753", 
                    height=8, 
                    border_radius=ft.border_radius.only(top_left=4, bottom_left=4), 
                    expand=green_part
                ),
                ft.Container(
                    bgcolor="#E0E0E0", 
                    height=8, 
                    border_radius=ft.border_radius.only(top_right=4, bottom_right=4), 
                    expand=gray_part
                ),
            ],
            spacing=0,
            expand=True 
        )

    # 3. Карточки растений
    def create_garden_card(name, image_path, health_pct):
        return ft.Container(
            content=ft.Column(
                controls=[
                    # fit="cover" чтобы картинка красиво заполняла пространство
                    ft.Image(src=image_path, width=150, height=130, fit="cover", border_radius=15),
                    
                    ft.Text(name, weight="bold", size=16, color="black"),
                    
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.FAVORITE_BORDER, color="#009753", size=20),
                            create_custom_bar(health_pct) 
                        ],
                        spacing=10,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER
                    )
                ], 
                spacing=8
            ),
            bgcolor="white",
            padding=10,
            border_radius=20,
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.BLACK12),
            col={"xs": 6, "sm": 6},
            # При клике идем в детали
            on_click=lambda _: page.go("/details")
        )

    garden_grid = ft.ResponsiveRow(
        controls=[
            # ИСПОЛЬЗУЕМ КАРТИНКИ ИЗ ASSETS (слэш в начале обязателен)
            # Убедись, что файлы aloe.png и petrushka.png лежат в папке assets
            create_garden_card("Алоэ", "/aloe1.png", 0.4),
            create_garden_card("Петрушка", "/petrushka5.png", 0.8),
        ], 
        spacing=15
    )

    # 4. Задачи
    def create_task_item(icon, color, text):
        return ft.Row(
            controls=[
                ft.Icon(icon, color=color, size=24),
                ft.Text(text, size=14, color="black", weight="w500")
            ],
            spacing=15
        )

    tasks_card = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("Сегодняшние задачи", size=18, weight="bold", color="black"),
                ft.Container(height=10),
                create_task_item(ft.Icons.WATER_DROP_OUTLINED, "#009753", "Полить Петрушку"),
                ft.Container(height=10),
                create_task_item(ft.Icons.WB_SUNNY_OUTLINED, "#009753", "Поставить на свет\nАлоэ"),
            ],
        ),
        bgcolor="white",
        padding=20,
        border_radius=20,
        shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.BLACK12),
    )

    view.controls.append(
        ft.ListView(
            controls=[
                header,
                ft.Container(height=20),
                garden_grid,
                ft.Container(height=20),
                tasks_card,
                ft.Container(height=20),
            ], 
            expand=True
        )
    )

    return view