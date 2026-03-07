import flet as ft

def HomeView(page: ft.Page):
    view = ft.View(route="/", bgcolor="#F9F9F9", padding=20)
    
    header = ft.Column(
        controls=[
            ft.Text("Добро пожаловать в\nGreenThumb", size=24, weight="bold", color="black"),
            ft.Text("Ознакомьтесь с нашей\nбиблиотекой растений", size=14, color="#6E6E6E")
        ], 
        spacing=5
    )

    def create_plant_card(name, image_path):
        return ft.Container(
            content=ft.Column(
                controls=[
                    # fit="cover" гарантирует, что картинка заполнит квадрат красиво
                    ft.Image(src=image_path, width=150, height=130, fit="cover", border_radius=15),
                    ft.Text(name, weight="bold", size=14, color="black"),
                ], 
                spacing=5
            ),
            bgcolor="white",
            padding=10,
            border_radius=20,
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.BLACK12),
            col={"xs": 6, "sm": 6}
        )

    plants_grid = ft.ResponsiveRow(
        controls=[
            # Указываем пути к файлам из папки assets (обязательно с / в начале)
            create_plant_card("Алоэ", "/aloe1.png"),
            create_plant_card("Хризантема", "/hriz2.png"),
            create_plant_card("Роза", "/roza3.png"),
            create_plant_card("Гибискус", "/gibis4.png"),
        ], 
        spacing=15, 
        run_spacing=15
    )

    action_btn = ft.Container(
        content=ft.Text(
            "Зарегистрируйтесь или войдите,\nчтобы следить за своей коллекцией", 
            color="white", 
            weight="bold", 
            text_align="center"
        ),
        bgcolor="#009753",
        padding=15,
        border_radius=20,
        alignment=ft.Alignment.CENTER,
        on_click=lambda _: page.go("/auth") 
    )

    view.controls.append(
        ft.ListView(
            controls=[
                header,
                ft.Container(height=20),
                plants_grid,
                ft.Container(height=20),
                action_btn,
                ft.Container(height=20),
            ], 
            expand=True
        )
    )

    return view