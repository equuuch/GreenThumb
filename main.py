import flet as ft
from views.home_view import HomeView
from views.user_home_view import UserHomeView
from views.my_plants_view import MyPlantsView
from views.details_view import DetailsView
from views.auth_view import AuthView
from components.nav_bar import NavBar

def main(page: ft.Page):
    page.title = "GreenThumb"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = "#F9F9F9"
    page.padding = 0

    # 1. РОУТЕР
    def router(route):
        page.route = route
        render_view(None)

    # 2. ПЕРЕХОДНИК МЕНЮ
    def on_nav_change(index):
        home_route = "/user_home" if page.route == "/user_home" else "/"
        routes = [home_route, "/my_plants", "/details", "/profile"]
        router(routes[index])

    # 3. ЛОГИКА ОТРИСОВКИ
    def render_view(e):
        page.views.clear()
        
        nav_map = {
            "/": 0, "/user_home": 0, 
            "/my_plants": 1, "/details": 2, "/profile": 3
        }
        current_index = nav_map.get(page.route, 0)

        if page.route == "/auth":
            view = AuthView(page)
        elif page.route == "/user_home":
            view = UserHomeView(page)
        elif page.route == "/my_plants":
            view = MyPlantsView(page)
        elif page.route == "/details":
            view = DetailsView(page)
        elif page.route == "/profile":
            view = ft.View(route="/profile", controls=[ft.Text("Профиль", size=30, color="black")], bgcolor="#F9F9F9")
        else:
            view = HomeView(page)
        
        if page.route not in ["/", "/auth"]:
            view.bottom_appbar = NavBar(current_index, on_nav_change)
        
        page.views.append(view)
        page.update()

    page.go = router 
    router("/")

if __name__ == "__main__":
    # ВАЖНО: Добавили assets_dir="assets"
    ft.app(target=main, assets_dir="assets")