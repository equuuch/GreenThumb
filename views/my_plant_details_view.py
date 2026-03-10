import flet as ft

def MyPlantDetailsView(page: ft.Page, nav, user_state):
    view = ft.View()
    view.route = "/my_plant_details"
    view.bgcolor = ft.colors.WHITE
    view.padding = 0

    # Шапка
    header = ft.Container(
        padding=ft.padding.only(top=10, left=10, right=10),
        content=ft.Row([
            ft.IconButton(ft.Icons.ARROW_BACK_IOS_NEW, icon_color="black", on_click=lambda _: nav("/my_plants")),
            ft.Text(value="Статус растения", weight="bold", size=18, color="black", expand=True, text_align="center"),
            ft.IconButton(ft.Icons.MORE_VERT, icon_color="black")
        ])
    )

    # Фото (крупно)
    image_box = ft.Container(
        content=ft.Image(src="/aloe.png", height=350, fit="contain", border_radius=20),
        alignment=ft.Alignment(0, 0),
        padding=20
    )

    # Кастомная полоска самочувствия
    def health_bar(pct):
        green = int(pct * 10)
        gray = 10 - green
        return ft.Row([
            ft.Container(bgcolor="#009753", height=12, expand=green, border_radius=6),
            ft.Container(bgcolor="#EEEEEE", height=12, expand=gray, border_radius=6),
        ], spacing=0)

    # Инфо блок
    info_card = ft.Container(
        padding=30,
        content=ft.Column([
            ft.Text(value="Алоэ Вера", size=30, weight="bold", color="black"),
            ft.Text(value="Самочувствие: Отличное", size=16, color="#009753", weight="w500"),
            ft.Container(height=10),
            ft.Text(value="Уровень здоровья", size=14, color="gray"),
            health_bar(0.85),
            ft.Container(height=20),
            ft.Row([
                ft.Icon(ft.Icons.WB_SUNNY_OUTLINED, color="orange"),
                ft.Text("Нуждается в солнечном свете", color="black")
            ]),
            ft.Row([
                ft.Icon(ft.Icons.WATER_DROP_OUTLINED, color="blue"),
                ft.Text("Полив через 2 дня", color="black")
            ]),
        ], spacing=10)
    )

    view.controls.append(ft.ListView([header, image_box, info_card], expand=True))
    return view