import flet as ft

def AnalyticsView(page: ft.Page, nav):
    # 1. Инициализация View по правилам 0.81.0
    view = ft.View()
    view.route = "/analytics"
    view.bgcolor = ft.colors.WHITE
    view.padding = 20

    # Шапка экрана
    header = ft.Row(
        controls=[
            ft.IconButton(
                icon=ft.Icons.ARROW_BACK_IOS_NEW, 
                icon_color=ft.colors.BLACK, 
                on_click=lambda _: nav("/profile")
            ),
            ft.Text(value="Процесс роста", size=22, weight="bold", color=ft.colors.BLACK, expand=True),
        ]
    )

    # 1. ОСЬ Y (Цифры слева)
    y_axis = ft.Column(
        controls=[
            ft.Text(value="25", size=12, color=ft.colors.GREY),
            ft.Text(value="20", size=12, color=ft.colors.GREY),
            ft.Text(value="15", size=12, color=ft.colors.GREY),
            ft.Text(value="10", size=12, color=ft.colors.GREY),
            ft.Text(value="5", size=12, color=ft.colors.GREY),
            ft.Text(value="0", size=12, color=ft.colors.GREY),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        height=200 
    )

    # 2. ФУНКЦИЯ СОЗДАНИЯ СТОЛБИКА
    def create_bar(height_px, label):
        # Контейнер самого столбика
        bar = ft.Container(
            width=40,
            height=height_px,
            bgcolor="#009753",
            # Скругляем только верхние углы
            border_radius=ft.border_radius.only(top_left=10, top_right=10),
            # Вместо ft.alignment.bottom_center используем координаты (0, 1)
            alignment=ft.Alignment(0, 1) 
        )

        return ft.Column(
            controls=[
                bar,
                ft.Text(value=label, size=12, color=ft.colors.GREY)
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.END,
            height=230 # Высота столбика + текст под ним
        )

    # Сами столбики данных
    bars_row = ft.Row(
        controls=[
            create_bar(40, "Июнь"),   
            create_bar(80, "Июль"),   
            create_bar(160, "Август"), 
            create_bar(200, "Сент."),  
        ],
        alignment=ft.MainAxisAlignment.SPACE_AROUND,
        vertical_alignment=ft.CrossAxisAlignment.END,
        expand=True
    )

    # Фоновые линии (Сетка)
    grid_lines = ft.Column(
        controls=[
            ft.Divider(height=1, color="#F0F0F0"),
            ft.Divider(height=1, color="#F0F0F0"),
            ft.Divider(height=1, color="#F0F0F0"),
            ft.Divider(height=1, color="#F0F0F0"),
            ft.Divider(height=1, color="#F0F0F0"),
            ft.Divider(height=1, color="#F0F0F0"),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        height=200
    )

    # Собираем график (Сетка на заднем плане, цифры и столбики на переднем)
    chart_area = ft.Stack(
        controls=[
            ft.Container(content=grid_lines, padding=ft.padding.only(left=30)),
            ft.Row(
                controls=[
                    ft.Container(content=y_axis, width=30),
                    bars_row
                ],
                spacing=10,
                alignment=ft.MainAxisAlignment.START
            )
        ],
        height=250
    )

    # 3. КАРТОЧКА С ТЕКСТОМ ВНИЗУ
    summary_card = ft.Container(
        bgcolor="#F0F9F4",
        padding=25,
        border_radius=25,
        content=ft.Column(
            controls=[
                ft.Text(value="Аналитика", size=18, weight="bold", color=ft.colors.BLACK),
                ft.Text(
                    value="Ваш Ландыш вырос на 20 см за лето! Это отличный показатель. "
                          "Растение получает достаточно света и воды.",
                    color=ft.colors.BLACK54,
                    size=14
                )
            ],
            spacing=8
        )
    )

    # СБОРКА ВСЕГО ЭКРАНА
    main_layout = ft.Column(spacing=20)
    main_layout.controls.append(header)
    main_layout.controls.append(ft.Text(value="Высота (см)", size=16, color=ft.colors.GREY, margin=ft.margin.only(top=10)))
    main_layout.controls.append(ft.Container(content=chart_area, padding=10))
    main_layout.controls.append(summary_card)

    view.controls.append(main_layout)
    
    return view