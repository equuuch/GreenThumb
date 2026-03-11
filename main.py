import flet as ft
from database.session import init_db
from urllib.parse import unquote

# Импорты ваших вьюх
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

# Импорт новой вьюхи добавления растения
try:
    from views.add_plant_view import AddPlantView
except ImportError:
    AddPlantView = None
    print("ВНИМАНИЕ: Файл views/add_plant_view.py не найден!")

# Попытка импорта NavBar
try:
    from components.nav_bar import NavBar
except ImportError:
    NavBar = None

# Глобальный стейт приложения
USER_STATE = {"id": None, "name": "Гость"}

def main(page: ft.Page):
    # 1. Инициализация БД
    init_db()

    page.title = "GreenThumb"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = "white"
    page.padding = 0
    
    # Мобильные размеры окна
    page.window.width = 400
    page.window.height = 800

    if not hasattr(page, "scan_picker"):
        page.scan_picker = ft.FilePicker()
        page.overlay.append(page.scan_picker)

    # --- ФУНКЦИЯ НАВИГАЦИИ ---
    def navigate(route_str):
        # Используем go, но без ручного вызова handle_route_change
        page.go(route_str)

    # --- ГЛАВНЫЙ ОБРАБОТЧИК МАРШРУТОВ ---
    def handle_route_change(e):
        print(f"DEBUG: Текущий маршрут: {page.route}")
        page.views.clear()
        
        nav_map = {"/user_home": 0, "/my_plants": 1, "/scanner": 2, "/profile": 3}
        current_index = nav_map.get(page.route, 0)

        try:
            # 1. Динамические маршруты
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
                is_register = "?mode=register" in page.route
                v = Auth_view = AuthView(page, navigate, USER_STATE, is_register_mode=is_register)
            
            elif page.route.startswith("/my_plant_details/"):
                pid = int(page.route.split("/")[-1])
                v = MyPlantDetailsView(page, navigate, pid, USER_STATE)

            # 2. Стандартные маршруты
            elif page.route == "/user_home":
                v = UserHomeView(page, navigate, USER_STATE)
            
            elif page.route == "/my_plants":
                v = MyPlantsView(page, navigate, USER_STATE)
            
            elif page.route == "/scanner":
                v = ScannerView(page, navigate, USER_STATE, page.scan_picker)
            
            elif page.route == "/add_plant":
                if AddPlantView:
                    v = AddPlantView(page, navigate, USER_STATE)
                else:
                    v = ft.View("/error", controls=[ft.Text("Ошибка: AddPlantView не найден")])
            
            elif page.route == "/profile":
                v = ProfileView(page, navigate, USER_STATE)
            
            elif page.route == "/analytics":
                v = AnalyticsView(page, navigate) 
            
            elif page.route == "/details":
                v = DetailsView(page, navigate)
            
            elif page.route == "/" or page.route == "":
                v = HomeView(page, navigate)
            
            else:
                v = HomeView(page, navigate)

            # --- ВОЗВРАТ СТАРОЙ ЛОГИКИ NAVBAR ---
            hide_nav_on = ["/", "/auth", "/my_plant_details", "/analytics", "/details", "/search", "/add_plant"]
            is_reference = page.route.startswith("/reference/")
            is_plant = page.route.startswith("/my_plant_details/")
            is_auth = page.route.startswith("/auth")

            if page.route not in hide_nav_on and not is_reference and not is_plant and not is_auth and NavBar:
                def on_click(idx):
                    routes = ["/user_home", "/my_plants", "/scanner", "/profile"]
                    navigate(routes[idx])
                v.bottom_appbar = NavBar(current_index, on_click)
            
            page.views.append(v)

        except Exception as ex:
            print(f"ОШИБКА: {ex}")
            page.views.append(ft.View("/error", controls=[ft.Text(f"Ошибка: {ex}")]))
        
        page.update()

    page.on_route_change = handle_route_change
    page.go(page.route or "/")

if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets")