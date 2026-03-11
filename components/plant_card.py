import flet as ft

def PlantCard(plant_name, image_url, status_text="healthy", on_click_action=None):
    # Логика цвета иконки капли (зеленый если ок, красный если нужен полив)
    water_icon_color = "#009753" if status_text == "healthy" else "red400"

    return ft.Container(
        width=165,
        bgcolor="white",
        border_radius=15,
        on_click=on_click_action, # Переход к деталям растения
        shadow=ft.BoxShadow(
            blur_radius=15,
            color=ft.Colors.with_opacity(0.1, "black"),
            offset=ft.Offset(0, 5)
        ),
        content=ft.Column(
            spacing=0,
            controls=[
                # Верхняя часть: Картинка
                ft.Container(
                    height=130,
                    content=ft.Image(
                        src=image_url,
                        fit=ft.ImageFit.COVER,
                        border_radius=ft.border_radius.only(top_left=15, top_right=15)
                    ),
                ),
                # Нижняя часть: Инфо
                ft.Container(
                    padding=ft.padding.only(left=12, right=12, top=10, bottom=12),
                    content=ft.Column(
                        spacing=8,
                        controls=[
                            ft.Text(
                                plant_name, 
                                size=15, 
                                weight="bold", 
                                color="black",
                                font_family="Montserrat" # Используем твой шрифт из GreenThumb
                            ),
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Icon(ft.Icons.WATER_DROP_OUTLINED, size=18, color=water_icon_color),
                                    ft.Icon(ft.Icons.WB_SUNNY_OUTLINED, size=18, color="grey400"),
                                    ft.Icon(ft.Icons.FAVORITE_BORDER, size=18, color="grey400"),
                                ]
                            )
                        ]
                    )
                )
            ]
        )
    )