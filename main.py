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

# Импорт вьюхи добавления растения
try:
    from views.add_plant_view import AddPlantView
except ImportError:
    AddPlantView = None

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
    
    # УДАЛЕНО: Регистрация Manrope и настройки весов в Theme
    page.fonts = {} 

    page.theme = ft.Theme(
        page_transitions=ft.PageTransitionsTheme(
            android="fadeThrough",
            ios="cupertino",
            windows="fadeThrough",
            macos="zoom",
        )
    )

    # Установка размеров окна
    page.window.width = 400
    page.window.height = 800

    if not hasattr(page, "scan_picker"):
        page.scan_picker = ft.FilePicker()
        page.overlay.append(page.scan_picker)

    # Вспомогательная функция навигации
    def navigate(route_str):
        page.go(route_str)

    # --- ГЛАВНЫЙ ОБРАБОТЧИК МАРШРУТОВ ---
    def handle_route_change(e):
        print(f"DEBUG: Маршрут изменен на: {page.route}")
        
        v = None
        
        # 1. Логика выбора вьюхи
        if page.route.startswith("/reference/"):
            try:
                catalog_id = int(page.route.split("/")[-1])
                v = ReferenceView(page, navigate, catalog_id, USER_STATE)
            except Exception as ex:
                print(f"Ошибка ReferenceView: {ex}")
                page.go("/catalog")
                return

        elif page.route.startswith("/reference_detail/"):
            try:
                catalog_id = int(page.route.split("/")[-1])
                v = ReferenceDetailView(page, navigate, catalog_id, USER_STATE)
            except Exception as ex:
                print(f"Ошибка ReferenceDetailView: {ex}")
                page.go("/catalog")
                return

        elif page.route.startswith("/my_plant_details/"):
            try:
                pid = int(page.route.split("/")[-1])
                v = MyPlantDetailsView(page, navigate, pid, USER_STATE)
            except:
                page.go("/my_plants")
                return

        elif page.route.startswith("/search"):
            query = unquote(page.route.split("q=")[-1]) if "q=" in page.route else ""
            v = SearchView(page, navigate, query, USER_STATE)

        elif page.route.startswith("/auth"):
            is_register = "?mode=register" in page.route
            v = AuthView(page, navigate, USER_STATE, is_register_mode=is_register)

        elif page.route == "/user_home":
            v = UserHomeView(page, navigate, USER_STATE)
        
        elif page.route == "/my_plants":
            v = MyPlantsView(page, navigate, USER_STATE)
        
        elif page.route == "/scanner":
            v = ScannerView(page, navigate, USER_STATE, page.scan_picker)
        
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

        elif page.route == "/" or page.route == "":
            v = HomeView(page, navigate)
        
        if v is None:
            return

        # 2. Управление стеком
        root_routes = ["/", "/user_home", "/catalog", "/my_plants", "/profile"]
        if page.route in root_routes:
            page.views.clear()
        
        if len(page.views) > 0 and page.views[-1].route == page.route:
            return

        # 3. Привязка NavBar
        hide_nav_on = ["/", "/auth", "/analytics", "/details", "/search", "/add_plant", "/catalog"]
        is_details = (
            page.route.startswith("/reference/") or 
            page.route.startswith("/reference_detail/") or 
            page.route.startswith("/my_plant_details/")
        )
        
        if page.route not in hide_nav_on and not is_details and NavBar:
            nav_map = {"/user_home": 0, "/my_plants": 1, "/scanner": 2, "/profile": 3}
            current_index = nav_map.get(page.route, 0)
            
            def on_nav_click(idx):
                routes = ["/user_home", "/my_plants", "/scanner", "/profile"]
                page.go(routes[idx])
                
            v.bottom_appbar = NavBar(current_index, on_nav_click)
        
        # 4. Добавление и отрисовка
        page.views.append(v)
        page.update()

    # --- Обработчик кнопки "Назад" ---
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