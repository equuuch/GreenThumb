import flet as ft

def MyPlantsView(page: ft.Page, nav):
    view = ft.View()
    view.route = "/my_plants"
    view.bgcolor = "#F9F9F9"
    view.padding = 20

    header = ft.Row(
        controls=[
            ft.IconButton(ft.Icons.ARROW_BACK_IOS_NEW, icon_size=20, icon_color="black", on_click=lambda _: nav("/user_home")),
            ft.Text(value="Мои растения", size=22, weight="bold", color="black", expand=True, text_align="center"),
            ft.IconButton(ft.Icons.ADD, icon_size=24, icon_color="black"),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
    )

    def create_card(name, img):
        return ft.Container(
            bgcolor="white", padding=10, border_radius=20,
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.BLACK12),
            col={"xs": 6, "sm": 6},
            # ТЕПЕРЬ ВЕДЕТ НА НОВЫЙ ЭКРАН ДЕТАЛЕЙ:
            on_click=lambda _: nav("/my_plant_details"),
            content=ft.Column([
                ft.Image(src=img, width=150, height=120, fit="cover", border_radius=15),
                ft.Text(value=name, weight="bold", size=14, color="black"),
                ft.Row([
                    ft.Icon(ft.Icons.WATER_DROP_OUTLINED, size=16, color="#009753"),
                    ft.Icon(ft.Icons.WB_SUNNY_OUTLINED, size=16, color="#6E6E6E"),
                    ft.Icon(ft.Icons.FAVORITE, size=16, color="#D32F2F"),
                ], spacing=10)
            ], spacing=5)
        )

    grid = ft.ResponsiveRow(spacing=15, run_spacing=15)
    grid.controls.append(create_card("Алоэ", "/aloe.png"))
    grid.controls.append(create_card("Тюльпан", "/rose.png"))
    grid.controls.append(create_card("Ромашка", "/hrizantema.png"))
    grid.controls.append(create_card("Хризантема", "/hibiscus.png"))

    view.controls.append(ft.ListView([header, ft.Container(height=20), grid], expand=True))
    return view