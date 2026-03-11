import flet as ft
from database.session import init_db
from views.home_view import HomeView
from views.user_home_view import UserHomeView
from views.my_plants_view import MyPlantsView
from views.auth_view import AuthView
from views.scanner_view import ScannerView
from views.profile_view import ProfileView
from views.reference_view import ReferenceView
from views.analytics_view import AnalyticsView
from views.my_plant_details_view import MyPlantDetailsView
from views.details_view import DetailsView
from views.search_view import SearchView
from urllib.parse import unquote

try:
    from components.nav_bar import NavBar
except ImportError:
    NavBar = None

USER_STATE = {"id": None, "name": "Гость"}

def main(page: ft.Page):
    init_db()

    page.title = "GreenThumb"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = "white"
    page.padding = 0
    
    page.window.width = 400
    page.window.height = 800

    # Создаем пикер ОДИН раз и сохраняем его прямо в объект страницы
    if not hasattr(page, "scan_picker"):
        page.scan_picker = ft.FilePicker()
        page.overlay.append(page.scan_picker)

    def navigate(route_str):
        page.route = route_str
        handle_route_change(None)

    def handle_route_change(e):
        print(f"DEBUG: Маршрут -> {page.route}")
        
        page.views.clear()
        
        # Очищаем всё, КРОМЕ нашего пикера
        for control in page.overlay[:]:
            if control != page.scan_picker:
                page.overlay.remove(control)
        
        nav_map = {"/user_home": 0, "/my_plants": 1, "/scanner": 2, "/profile": 3}
        current_index = nav_map.get(page.route, 0)

        try:
            if page.route.startswith("/reference/"):
                try:
                    catalog_id = int(page.route.split("/")[-1])
                    v = ReferenceView(page, navigate, catalog_id, USER_STATE)
                except: v = HomeView(page, navigate)
            
            elif page.route.startswith("/search"):
                try:
                    query = unquote(page.route.split("q=")[-1])
                    v = SearchView(page, navigate, query, USER_STATE)
                except: v = HomeView(page, navigate)
            
            elif page.route.startswith("/auth"):
                v = AuthView(page, navigate, USER_STATE, is_register_mode=("?mode=register" in page.route))
            
            elif page.route == "/user_home":
                v = UserHomeView(page, navigate, USER_STATE)
            
            elif page.route == "/my_plants":
                v = MyPlantsView(page, navigate, USER_STATE)
            
            elif page.route == "/scanner":
                # Передаем стабильный пикер из page
                v = ScannerView(page, navigate, USER_STATE, page.scan_picker)
            
            elif page.route == "/profile":
                v = ProfileView(page, navigate, USER_STATE)
            
            elif page.route == "/analytics":
                v = AnalyticsView(page, navigate) 
            
            elif page.route == "/my_plant_details":
                v = MyPlantDetailsView(page, navigate, USER_STATE)
            
            elif page.route == "/details":
                v = DetailsView(page, navigate)
            
            else:
                v = HomeView(page, navigate)

            hide_nav = ["/", "/auth", "/my_plant_details", "/analytics", "/details", "/search"]
            if page.route not in hide_nav and not page.route.startswith("/reference/") and NavBar:
                def on_click(idx):
                    routes = ["/user_home", "/my_plants", "/scanner", "/profile"]
                    navigate(routes[idx])
                v.bottom_appbar = NavBar(current_index, on_click)
            
            page.views.append(v)

        except Exception as ex:
            print(f"ОШИБКА НАВИГАЦИИ: {ex}")
            page.views.append(ft.View("/error", controls=[ft.Text(f"Ошибка: {ex}", color="red")]))
        
        page.update()

    page.on_route_change = handle_route_change
    page.go("/")

if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets")