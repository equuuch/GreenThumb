import flet as ft
from database.session import init_db
from views.home_view import HomeView
from views.user_home_view import UserHomeView
from views.my_plants_view import MyPlantsView
from views.details_view import DetailsView
from views.auth_view import AuthView
from views.scanner_view import ScannerView
from views.reference_view import ReferenceView
from views.profile_view import ProfileView
from views.analytics_view import AnalyticsView
from views.my_plant_details_view import MyPlantDetailsView
from components.nav_bar import NavBar

USER_STATE = {"id": None, "name": "Гость"}

def main(page: ft.Page):
    init_db()

    page.title = "GreenThumb"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = "#F9F9F9"
    page.padding = 0
    
    # Настройки адаптива для браузера
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
            if page.route == "/auth":
                v = AuthView(page, navigate, USER_STATE)
            elif page.route == "/user_home":
                v = UserHomeView(page, navigate, USER_STATE)
            elif page.route == "/my_plants":
                v = MyPlantsView(page, navigate)
            elif page.route == "/my_plant_details":
                v = MyPlantDetailsView(page, navigate, USER_STATE)
            elif page.route == "/scanner":
                v = ScannerView(page, navigate)
            elif page.route == "/profile":
                v = ProfileView(page, navigate, USER_STATE)
            elif page.route == "/analytics":
                v = AnalyticsView(page, navigate)
            elif page.route == "/details":
                v = DetailsView(page, navigate)
            elif page.route == "/reference":
                v = ReferenceView(page, navigate)
            else:
                v = HomeView(page, navigate)

            # Прячем меню на гостевой, авторизации и деталях
            no_nav = ["/", "/auth", "/details", "/analytics", "/reference", "/my_plant_details"]
            
            if page.route not in no_nav:
                def on_click(idx):
                    r = ["/user_home", "/my_plants", "/scanner", "/profile"]
                    navigate(r[idx])
                v.bottom_appbar = NavBar(current_index, on_click)
            
            page.views.append(v)
            page.update()
        except Exception as ex:
            print(f"Router Error: {ex}")

    page.on_route_change = handle_route_change
    navigate("/")

if __name__ == "__main__":
    # Просто убираем view=ft.AppView.WEB_BROWSER
    ft.run(main, assets_dir="assets")