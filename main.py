import flet as ft
from database.session import init_db
from urllib.parse import unquote

# --- ИМПОРТЫ ВЬЮХ ---
from views.home_view import HomeView
from views.user_home_view import UserHomeView
from views.my_plants_view import MyPlantsView
from views.auth_view import AuthView
from views.scanner_view import ScannerView
from views.profile_view import ProfileView
from views.reference_view import ReferenceView
from views.reference_detail_view import ReferenceDetailView
from views.analytics_view import AnalyticsView
from views.my_plant_details_view import MyPlantDetailsView
from views.details_view import DetailsView
from views.search_view import SearchView
from views.calendar_view import CalendarView
from views.notifications_view import NotificationsView
from views.catalog_view import CatalogView 

try:
    from views.add_plant_view import AddPlantView
except ImportError as e:
    print(f"ОШИБКА ИМПОРТА AddPlantView: {e}")
    AddPlantView = None

try:
    from components.nav_bar import NavBar
except ImportError:
    NavBar = None

# Глобальный стейт приложения
USER_STATE = {"id": 1, "name": "Пользователь"}

def main(page: ft.Page):
    init_db()

    page.title = "GreenThumb"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = "white"
    page.padding = 0
    
    page.theme = ft.Theme(
        page_transitions=ft.PageTransitionsTheme(
            android="fadeThrough",
            ios="cupertino",
            windows="fadeThrough"
        )
    )

    page.window.width = 400
    page.window.height = 800

    if not hasattr(page, "scan_picker"):
        page.scan_picker = ft.FilePicker()
        page.overlay.append(page.scan_picker)

    def navigate(route_str):
        page.go(route_str)

    # --- ГЛАВНЫЙ ОБРАБОТЧИК МАРШРУТОВ ---
    def handle_route_change(e):
        print(f"DEBUG: Маршрут изменен на: {page.route}")
        
        # КРИТИЧЕСКИЙ ФИКС: Очищаем глобальные бары страницы при каждой смене роута
        page.navigation_bar = None
        page.bottom_app_bar = None
        
        v = None
        
        try:
            # 1. Логика динамических маршрутов
            if page.route.startswith("/reference/"):
                catalog_id = int(page.route.split("/")[-1])
                v = ReferenceView(page, navigate, catalog_id, USER_STATE)

            elif page.route.startswith("/reference_detail/"):
                catalog_id = int(page.route.split("/")[-1])
                v = ReferenceDetailView(page, navigate, catalog_id, USER_STATE)

            elif page.route.startswith("/my_plant_details/"):
                pid = int(page.route.split("/")[-1])
                v = MyPlantDetailsView(page, navigate, pid, USER_STATE)

            elif page.route.startswith("/search"):
                query = unquote(page.route.split("q=")[-1]) if "q=" in page.route else ""
                v = SearchView(page, navigate, query, USER_STATE)

            # 2. Логика статических маршрутов
            elif page.route.startswith("/auth"):
                is_register = "?mode=register" in page.route
                v = AuthView(page, navigate, USER_STATE, is_register_mode=is_register)

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
                    page.go("/scanner")
                    return
            
            elif page.route == "/catalog":
                v = CatalogView(page, navigate, USER_STATE)
            
            elif page.route == "/profile":
                v = ProfileView(page, navigate, USER_STATE)

            elif page.route == "/calendar":
                v = CalendarView(page, navigate, USER_STATE)

            elif page.route == "/notifications":
                v = NotificationsView(page, navigate, USER_STATE)
                
            elif page.route == "/analytics":
                v = AnalyticsView(page, navigate, USER_STATE)
                
            elif page.route == "/details":
                v = DetailsView(page, navigate)

            elif page.route in ["/", ""]:
                v = HomeView(page, navigate)

        except Exception as route_ex:
            print(f"Критическая ошибка роутинга: {route_ex}")
            v = UserHomeView(page, navigate, USER_STATE)

        if v is None: return

        # --- УПРАВЛЕНИЕ СТЕКОМ ---
        root_routes = ["/", "/user_home", "/catalog", "/my_plants", "/profile"]
        if page.route in root_routes:
            page.views.clear()
        
        if len(page.views) > 0 and page.views[-1].route == page.route:
            return

        # --- ЛОГИКА НАВБАРА ---
        hide_nav_on = ["/", "/auth", "/analytics", "/details", "/search", "/add_plant"]
        
        is_details = (
            page.route.startswith("/reference/") or 
            page.route.startswith("/reference_detail/") or 
            page.route.startswith("/my_plant_details/") or
            page.route.startswith("/auth") # Доп. проверка для безопасности
        )

        if page.route in hide_nav_on or is_details or not NavBar:
            v.bottom_appbar = None
            # Дублируем очистку глобально
            page.bottom_app_bar = None 
        else:
            nav_map = {"/user_home": 0, "/my_plants": 1, "/scanner": 2, "/profile": 3}
            current_index = nav_map.get(page.route, 0)
            
            def on_nav_click(idx):
                routes = ["/user_home", "/my_plants", "/scanner", "/profile"]
                page.go(routes[idx])
            
            # Назначаем бар именно вьюхе
            v.bottom_appbar = NavBar(current_index, on_nav_click)
        
        # --- ДОБАВЛЕНИЕ И ОБНОВЛЕНИЕ ---
        page.views.append(v)
        page.update()

    def handle_view_pop(e):
        if len(page.views) > 1:
            page.views.pop()
            top_view = page.views[-1]
            page.route = top_view.route
            page.update()
        else:
            page.go("/")

    page.on_route_change = handle_route_change
    page.on_view_pop = handle_view_pop
    
    page.go(page.route or "/")

if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets")