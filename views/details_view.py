import flet as ft

def DetailsView(page: ft.Page):
    view = ft.View(route="/details", bgcolor="white", padding=0)
    
    # 1. ДОБАВЛЯЕМ ПРОКРУТКУ: теперь меню 100% не обрежется и будет доступно
    view.scroll = ft.ScrollMode.AUTO 

    # Шапка экрана
    header = ft.Container(
        content=ft.Row(
            controls=[
                ft.IconButton(ft.Icons.ARROW_BACK_IOS_NEW, icon_color="black", on_click=lambda _: page.push_route("/")),
                ft.Text("GreenThumb", weight="bold", size=18, color="black", expand=True, text_align="center"),
                ft.IconButton(ft.Icons.INFO_OUTLINE, icon_color="black")
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        ),
        padding=ft.padding.only(top=10, left=10, right=10)
    )

    # Картинка растения
    image_section = ft.Container(
        content=ft.Image(
            src="https://picsum.photos/400/400?15", 
            height=250,
            fit="contain"
        ),
        alignment=ft.Alignment.CENTER,
        padding=20
    )

    # Вспомогательная функция для генерации строк меню
    def create_stat(icon, text, value_pct=None):
        stat_controls =[ft.Text(text, color="black", size=14, weight="w500")]
        
        # ТОЛСТЫЙ КАСТОМНЫЙ ПРОГРЕСС-БАР как на макете (из 2-х контейнеров)
        if value_pct is not None:
            left_width = int(value_pct * 100)
            right_width = 100 - left_width
            custom_bar = ft.Row(
                controls=[
                    # Зеленая часть
                    ft.Container(expand=left_width, bgcolor="#009753", height=14, border_radius=10),
                    # Белая часть
                    ft.Container(expand=right_width, bgcolor="white", height=14, border_radius=10),
                ],
                spacing=0
            )
            stat_controls.append(custom_bar)
            
        return ft.Row(
            controls=[
                ft.Icon(icon, color="#009753", size=24),
                ft.Column(controls=stat_controls, spacing=5, expand=True)
            ],
            spacing=15,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )

    # Нижнее серое меню с показателями
    info_card = ft.Container(
        content=ft.Column(
            controls=[
                # Индикатор свайпа (маленькая белая полоска сверху карточки)
                ft.Container(
                    width=40, height=4, border_radius=2, bgcolor="white",
                    margin=ft.margin.only(bottom=10)
                ),
                # Заголовок Ландыш
                ft.Row(
                    controls=[
                        ft.Text("Ландыш", size=26, weight="bold", color="black"),
                        ft.Container(
                            width=24, height=24, border_radius=12, bgcolor="white",
                            content=ft.Container(width=10, height=10, border_radius=5, bgcolor="#009753"),
                            alignment=ft.Alignment.CENTER
                        )
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                ),
                ft.Container(height=10),
                
                # Пункты меню
                create_stat(ft.Icons.WATER_DROP_OUTLINED, "Содержание воды", 0.4),
                ft.Container(height=10),
                create_stat(ft.Icons.WB_SUNNY_OUTLINED, "Уровень освещенности", 0.7),
                ft.Container(height=10),
                create_stat(ft.Icons.FAVORITE_BORDER, "Состояние растения", 0.35),
                
                # Отступ снизу, чтобы нижняя панель навигации ничего не перекрывала
                ft.Container(height=80)
            ],
            spacing=10,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER # Выравнивает полоску свайпа по центру
        ),
        bgcolor="#E8E8E8",
        padding=30,
        border_radius=ft.border_radius.only(top_left=30, top_right=30),
        shadow=ft.BoxShadow(blur_radius=20, color=ft.Colors.BLACK12),
    )

    # Собираем экран (убрали expand=True, чтобы элементы выстраивались естественно)
    view.controls.append(
        ft.Column(
            controls=[header, image_section, info_card],
            spacing=0
        )
    )

    return view