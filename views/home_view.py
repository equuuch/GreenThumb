import flet as ft

def HomeView(page: ft.Page, nav):
    view = ft.View()
    view.route = "/"
    view.bgcolor = "#F9F9F9"
    view.padding = 20
    
    header = ft.Column(
        controls=[
            ft.Text("Добро пожаловать в\nGreenThumb", size=24, weight="bold", color="black"),
            ft.Text("Ознакомьтесь с нашей\nбиблиотекой растений", size=14, color="#6E6E6E")
        ],
        spacing=5
    )

    def create_card(name, img):
        return ft.Container(
            bgcolor="white", padding=10, border_radius=20,
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.BLACK12),
            col={"xs": 6, "sm": 6},
            content=ft.Column(controls=[
                ft.Image(src=img, width=150, height=130, fit="cover", border_radius=15),
                ft.Text(name, weight="bold", size=14, color="black"),
            ])
        )

    grid = ft.ResponsiveRow(spacing=15, run_spacing=15)
    grid.controls.append(create_card("Алоэ", "/aloe.png"))
    grid.controls.append(create_card("Хризантема", "/hrizantema.png"))
    grid.controls.append(create_card("Роза", "/rose.png"))
    grid.controls.append(create_card("Гибискус", "/hibiscus.png"))

    btn = ft.Container(
        bgcolor="#009753", padding=15, border_radius=20, alignment=ft.Alignment(0, 0),
        on_click=lambda _: nav("/auth"),
        content=ft.Text("Зарегистрируйтесь или войдите,\nчтобы следить за своей коллекцией", color="white", weight="bold", text_align="center")
    )

    lv = ft.ListView(expand=True)
    lv.controls.append(header)
    lv.controls.append(ft.Container(height=20))
    lv.controls.append(grid)
    lv.controls.append(ft.Container(height=20))
    lv.controls.append(btn)

    view.controls.append(lv)
    return view