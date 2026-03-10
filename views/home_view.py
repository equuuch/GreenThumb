import flet as ft

def HomeView(page: ft.Page, nav):
    view = ft.View()
    view.route = "/"
    view.bgcolor = "#F9F9F9"
    view.padding = 20
    
    header = ft.Column([
        ft.Text("GreenThumb", size=28, weight="bold", color="#009753"),
        ft.Text("Ваш проводник в мире растений", size=14, color="gray")
    ], spacing=0)

    # ПОИСК (Заглушка для Smart Search)
    search_field = ft.TextField(
        hint_text="Найти растение (например, Монстера)...",
        border_radius=15, bgcolor="white",
        prefix_icon=ft.Icons.SEARCH,
        on_submit=lambda e: nav(f"/search?q={e.control.value}")
    )

    def create_card(name, img, cat_id):
        return ft.Container(
            bgcolor="white", padding=15, border_radius=25,
            shadow=ft.BoxShadow(blur_radius=15, color=ft.Colors.BLACK_12),
            col={"xs": 6, "sm": 6},
            # Переход по ID
            on_click=lambda _: nav(f"/reference/{cat_id}"),
            content=ft.Column([
                ft.Image(src=img, height=120, fit="contain"),
                ft.Text(name, weight="bold", size=16, color="black"),
                ft.Text("Справочник", size=12, color="#009753")
            ], horizontal_alignment="center")
        )

    # Сетка популярных растений (ID 1, 2, 3 должны быть в базе)
    grid = ft.ResponsiveRow(spacing=20, controls=[
        create_card("Алоэ", "/aloe.png", 1),
        create_card("Хризантема", "/hrizantema.png", 2),
        create_card("Роза", "/rose.png", 3),
        create_card("Ландыш", "/aloe.png", 4),
    ])

    cta_btn = ft.ElevatedButton(
        "Зарегистрироваться, чтобы создать сад",
        bgcolor="#009753", color="white",
        width=float("inf"), height=50,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=15)),
        on_click=lambda _: nav("/auth")
    )

    lv = ft.ListView(expand=True, spacing=30)
    lv.controls.extend([header, search_field, grid, cta_btn])
    
    view.controls.append(lv)
    return view