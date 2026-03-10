import flet as ft

# --- Константы стиля ---
BG_COLOR = "#F9F9F9"
ACCENT_COLOR = "#1E5631"
CARD_RADIUS = 20

def main(page: ft.Page):
    page.title = "GreenThumb"
    page.bgcolor = BG_COLOR
    page.window_width = 390
    page.window_height = 844
    page.padding = 0

    # Шаблон для создания View (избавляет от ошибок с multiple values)
    def create_base_view(route, controls_list):
        v = ft.View(route=route)
        v.bgcolor = BG_COLOR
        v.padding = 20
        v.controls = controls_list
        return v

    def route_change(e):
        page.views.clear()
        
        if page.route == "/auth":
            # Экран авторизации
            page.views.append(create_base_view("/auth", [
                ft.Container(height=100),
                ft.Text("GreenThumb", size=32, weight="bold", color=ACCENT_COLOR),
                ft.TextField(label="Почта", border_radius=CARD_RADIUS),
                ft.TextField(label="Пароль", password=True, border_radius=CARD_RADIUS),
                ft.FilledButton("Войти", on_click=lambda _: page.go("/")),
            ]))
        else:
            # Главная
            page.views.append(create_base_view("/", [
                ft.Text("Главная: Твой сад", size=24, weight="bold", color=ft.colors.BLACK),
                ft.Button("Выйти", on_click=lambda _: page.go("/auth"))
            ]))
            
        page.update()

    page.on_route_change = route_change
    page.go("/auth")

ft.run(main)