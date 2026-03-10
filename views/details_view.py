import flet as ft

def DetailsView(page: ft.Page, nav):
    # 1. Инициализация View по правилам 0.81.0
    view = ft.View()
    view.route = "/details"
    view.bgcolor = ft.colors.WHITE
    view.padding = 0

    # Шапка (Кнопка назад теперь ведет на /scanner)
    header = ft.Container(
        content=ft.Row(
            controls=[
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK_IOS_NEW, 
                    icon_color=ft.colors.BLACK, 
                    # ИЗМЕНЕНИЕ ЗДЕСЬ: Возврат на сканер (камеру)
                    on_click=lambda _: nav("/scanner") 
                ),
                ft.Text(
                    value="GreenThumb", 
                    weight="bold", 
                    size=18, 
                    color=ft.colors.BLACK,
                    expand=True,
                    text_align="center"
                ),
                ft.IconButton(
                    icon=ft.Icons.INFO_OUTLINE, 
                    icon_color=ft.colors.BLACK
                )
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        ),
        padding=ft.padding.only(top=10, left=10, right=10)
    )

    # 2. Функция для создания полосок прогресса (зеленая + серая части)
    def create_stat_item(icon, label, val):
        green_part = int(val * 10)
        gray_part = 10 - green_part
        
        progress_bar = ft.Row(
            controls=[
                ft.Container(
                    bgcolor="#009753", 
                    height=10, 
                    expand=green_part, 
                    border_radius=5
                ),
                ft.Container(
                    bgcolor="#F0F0F0", 
                    height=10, 
                    expand=gray_part, 
                    border_radius=5
                ),
            ],
            spacing=0
        )

        return ft.Row(
            controls=[
                ft.Icon(icon, color="#009753", size=28),
                ft.Column(
                    controls=[
                        ft.Text(value=label, color=ft.colors.BLACK, size=15, weight="w500"),
                        progress_bar
                    ],
                    expand=True,
                    spacing=5
                )
            ],
            spacing=15,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )

    # 3. Контент страницы
    
    # Фото растения
    plant_image = ft.Container(
        content=ft.Image(
            src="/aloe.png", # Убедись, что файл есть в assets
            height=300,
            fit="contain"
        ),
        alignment=ft.Alignment(0, 0),
        padding=20
    )

    # Информационный блок
    info_section = ft.Container(
        padding=ft.padding.symmetric(horizontal=30),
        content=ft.Column(
            controls=[
                ft.Text(
                    value="Ландыш", 
                    size=32, 
                    weight="bold", 
                    color=ft.colors.BLACK
                ),
                ft.Container(height=10),
                
                create_stat_item(ft.Icons.WATER_DROP_OUTLINED, "Содержание воды", 0.5),
                ft.Container(height=5),
                create_stat_item(ft.Icons.WB_SUNNY_OUTLINED, "Уровень освещенности", 0.7),
                ft.Container(height=5),
                create_stat_item(ft.Icons.FAVORITE_BORDER, "Состояние растения", 0.4),
            ],
            spacing=15
        )
    )

    # Собираем всё в ListView
    main_scroll = ft.ListView(expand=True)
    main_scroll.controls.append(header)
    main_scroll.controls.append(plant_image)
    main_scroll.controls.append(info_section)
    main_scroll.controls.append(ft.Container(height=40))

    view.controls.append(main_scroll)
    
    return view