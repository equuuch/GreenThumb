import flet as ft
from database.session import init_db
from views.home_view import HomeView
from views.user_home_view import UserHomeView
from views.my_plants_view import MyPlantsView
from views.auth_view import AuthView
from views.scanner_view import ScannerView
from views.profile_view import ProfileView
from components.nav_bar import NavBar

# Глобальный стейт приложения
USER_STATE = {"id": None, "name": "Гость"}

def main(page: ft.Page):
    init_db()
    page.title = "GreenThumb"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = ft.Colors.WHITE
    page.window_width = 400
    page.window_height = 800

    def navigate(route_str):
        page.route = route_str
        handle_route_change(None)

    def handle_route_change(e):
        page.views.clear()
        nav_map = {"/user_home": 0, "/my_plants": 1, "/scanner": 2, "/profile": 3}
        current_index = nav_map.get(page.route, 0)

        try:
            # ПЕРЕДАЧА USER_STATE ВО ВСЕ НУЖНЫЕ ВЬЮХИ
            if page.route == "/auth":
                v = AuthView(page, navigate, USER_STATE)
            elif page.route == "/user_home":
                v = UserHomeView(page, navigate, USER_STATE)
            elif page.route == "/my_plants":
                v = MyPlantsView(page, navigate, USER_STATE)
            elif page.route == "/scanner":
                v = ScannerView(page, navigate, USER_STATE)
            elif page.route == "/profile":
                v = ProfileView(page, navigate, USER_STATE)
            else:
                v = HomeView(page, navigate)

            # Настройка NavBar
            no_nav = ["/", "/auth"]
            if page.route not in no_nav:
                def on_click(idx):
                    r = ["/user_home", "/my_plants", "/scanner", "/profile"]
                    navigate(r[idx])
                v.bottom_appbar = NavBar(current_index, on_click)
            
            page.views.append(v)
        except Exception as ex:
            print(f"ОШИБКА РОУТЕРА: {ex}")
            page.views.append(ft.View(controls=[ft.Text(f"Ошибка: {ex}")]))
        
        page.update()

    page.on_route_change = handle_route_change
    if page.route == "" or page.route == "/":
        page.route = "/"
    handle_route_change(None)

if __name__ == "__main__":
    ft.run(main, assets_dir="assets")