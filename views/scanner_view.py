import flet as ft

def ScannerView(page: ft.Page, nav):
    # 1. Создаем объект View строго по правилам 0.81.0
    view = ft.View()
    view.route = "/scanner"
    view.bgcolor = ft.Colors.BLACK
    view.padding = 0

    # Контейнер для выезжающего меню
    sheet_container = ft.Container()
    sheet_container.bgcolor = "#E8E8E8"
    sheet_container.padding = 30
    sheet_container.border_radius = ft.border_radius.only(top_left=30, top_right=30)
    sheet_container.width = 1000 # Большая ширина, чтобы перекрыть экран
    sheet_container.height = 450 

    # Начальное положение (скрыто внизу)
    sheet_container.offset = ft.Offset(0, 0.85)
    sheet_container.animate_offset = ft.Animation(600, "decelerate")

    def toggle_menu(e):
        # Если внизу - поднимаем, если вверху - опускаем
        if sheet_container.offset.y == 0.85:
            sheet_container.offset = ft.Offset(0, 0)
        else:
            sheet_container.offset = ft.Offset(0, 0.85)
        sheet_container.update()

    # Вспомогательная функция для прогресс-баров (используем int для expand)
    def create_stat(icon, label, val):
        green = int(val * 10)
        gray = 10 - green
        
        bar_row = ft.Row(spacing=0)
        bar_row.controls.append(ft.Container(bgcolor="#009753", height=8, expand=green, border_radius=4))
        bar_row.controls.append(ft.Container(bgcolor="#D0D0D0", height=8, expand=gray, border_radius=4))
        
        return ft.Row(
            controls=[
                ft.Icon(icon, color="#009753", size=24),
                ft.Column(
                    controls=[
                        ft.Text(value=label, color=ft.Colors.BLACK, size=14, weight="bold"),
                        bar_row
                    ],
                    expand=True,
                    spacing=5
                )
            ],
            spacing=15
        )

    # Контент внутри меню
    sheet_col = ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    
    # Кликабельная шапка меню (индикатор свайпа)
    swipe_handle = ft.Container(
        width=40, height=4, bgcolor=ft.Colors.WHITE, border_radius=2,
        on_click=toggle_menu
    )
    
    sheet_col.controls.append(swipe_handle)
    sheet_col.controls.append(ft.Container(height=10))
    sheet_col.controls.append(ft.Text(value="Ландыш", size=26, weight="bold", color=ft.Colors.BLACK))
    sheet_col.controls.append(ft.Container(height=10))
    sheet_col.controls.append(create_stat(ft.Icons.WATER_DROP_OUTLINED, "Содержание воды", 0.5))
    sheet_col.controls.append(ft.Container(height=10))
    sheet_col.controls.append(create_stat(ft.Icons.WB_SUNNY_OUTLINED, "Уровень освещенности", 0.7))
    sheet_col.controls.append(ft.Container(height=10))
    sheet_col.controls.append(create_stat(ft.Icons.FAVORITE_BORDER, "Состояние растения", 0.4))
    sheet_col.controls.append(ft.Container(height=20))
    
    # Кнопка перехода в паспорт
    passport_btn = ft.Container(
        content=ft.Text(value="Открыть паспорт растения", color=ft.Colors.WHITE, weight="bold"),
        bgcolor="#009753",
        padding=15,
        border_radius=15,
        alignment=ft.Alignment(0, 0), # Замена ft.alignment.center
        on_click=lambda _: nav("/details")
    )
    sheet_col.controls.append(passport_btn)
    
    sheet_container.content = sheet_col

    # --- ВЕРХНЯЯ ПАНЕЛЬ ---
    header = ft.Container(
        padding=ft.padding.only(top=40, left=10, right=10),
        bgcolor=ft.Colors.BLACK38,
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK_IOS_NEW, 
                    icon_color=ft.Colors.WHITE, 
                    on_click=lambda _: nav("/my_plants")
                ),
                ft.Text(value="Сканирование", color=ft.Colors.WHITE, weight="bold", size=18),
                ft.IconButton(
                    icon=ft.Icons.INFO_OUTLINE, 
                    icon_color=ft.Colors.WHITE, 
                    on_click=lambda _: nav("/reference")
                ),
            ]
        )
    )

    # --- КНОПКА СКАНЕРА ---
    scan_trigger = ft.Container(
        content=ft.FloatingActionButton(
            icon=ft.Icons.QR_CODE_SCANNER, 
            bgcolor="#009753", 
            on_click=toggle_menu
        ),
        bottom=140,
        right=20
    )

    # --- СБОРКА ЧЕРЕЗ STACK ---
    main_stack = ft.Stack(expand=True)
    # Имитация камеры
    main_stack.controls.append(
        ft.Container(
            expand=True, 
            bgcolor=ft.Colors.BLACK, 
            content=ft.Image(src="https://picsum.photos/800/1200", fit="cover")
        )
    )
    main_stack.controls.append(header)
    main_stack.controls.append(scan_trigger)
    # Оборачиваем меню в контейнер для позиционирования внизу
    main_stack.controls.append(
        ft.Container(content=sheet_container, bottom=0, left=0, right=0)
    )

    view.controls.append(main_stack)
    return view