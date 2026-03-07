import flet as ft

def MyPlantsView(page: ft.Page):
    view = ft.View(route="/my_plants", bgcolor="#F9F9F9", padding=20)
    
    header = ft.Row([
        ft.IconButton(icon=ft.Icons.ARROW_BACK_IOS_NEW, icon_size=20, icon_color="black", on_click=lambda _: page.push_route("/")),
        ft.Text("Мои растения", size=22, weight="bold", color="black", expand=True, text_align="center"),
        ft.IconButton(icon=ft.Icons.ADD, icon_size=24, icon_color="black"),
    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

    def create_my_plant_card(name, image_path):
        return ft.Container(
            content=ft.Column([
                ft.Image(src=image_path, width=150, height=120, fit="cover", border_radius=15),
                ft.Text(name, weight="bold", size=14, color="black"),
                ft.Row([
                    ft.Icon(ft.Icons.WATER_DROP, size=16, color="#009753"),
                    ft.Icon(ft.Icons.WB_SUNNY_OUTLINED, size=16, color="#6E6E6E"),
                    ft.Icon(ft.Icons.FAVORITE_BORDER, size=16, color="#D32F2F"),
                ], spacing=10, alignment=ft.MainAxisAlignment.START)
            ], spacing=5),
            bgcolor="white",
            padding=10,
            border_radius=20,
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.BLACK12),
            col={"xs": 6, "sm": 6}
        )

    plants_grid = ft.ResponsiveRow([
        create_my_plant_card("Алоэ", "https://picsum.photos/150/150?11"),
        create_my_plant_card("Тюльпан", "https://picsum.photos/150/150?12"),
        create_my_plant_card("Ромашка", "https://picsum.photos/150/150?13"),
        create_my_plant_card("Хризантема", "https://picsum.photos/150/150?14"),
    ], spacing=15, run_spacing=15)

    view.controls.append(
        ft.ListView([
            header,
            ft.Container(height=20),
            plants_grid,
            ft.Container(height=20),
        ], expand=True)
    )
    return view