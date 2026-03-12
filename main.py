import flet as ft
import os
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

# Безопасные импорты
try:
    from views.add_plant_view import AddPlantView
except ImportError as e:
    print(f"Предупреждение: AddPlantView не найден: {e}")
    AddPlantView = None

try:
    from components.nav_bar import NavBar
except ImportError:
    print("Предупреждение: Компонент NavBar не найден")
    NavBar = None

# Глобальный стейт (id: 1 для тестов)
USER_STATE = {"id": 1, "name": "Пользователь"}

def main(page: ft.Page):
    # 1. Инициализация базы данных
    init_db()

    # 2. Настройка страницы
    page.title = "GreenThumb"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = "white"
    page.padding = 0
    
    # Создаем папку для загрузок, если её нет (для WEB-версии)
    upload_path = os.path.join("assets", "uploads")
    if not os.path.exists(upload_path):
        os.makedirs(upload_path, exist_ok=True)

    page.theme = ft.Theme(
        font_family="Montserrat",
        page_transitions=ft.PageTransitionsTheme(
            android="fadeThrough",
            ios="cupertino",
            windows="fadeThrough"
        )
    )

    page.window.width = 400
    page.window.height = 800

    # --- ГЛОБАЛЬНЫЙ FILEPICKER ---
    # Важно: он должен быть в overlay для доступа из любой вьюхи
    if not hasattr(page, "scan_picker"):
        page.scan_picker = ft.FilePicker()
        page.overlay.append(page.scan_picker)

    def navigate(route_str):
        page.go(route_str)

    # --- ГЛАВНЫЙ ОБРАБОТЧИК МАРШРУТОВ ---
    def handle_route_change(e):
        print(f"DEBUG: Маршрут: {page.route}")
        
        page.navigation_bar = None
        page.bottom_app_bar = None
        
        v = None
        current_route = page.route
        
        try:
            # А. Динамические маршруты
            if current_route.startswith("/reference/"):
                catalog_id = int(current_route.split("/")[-1])
                v = ReferenceView(page, navigate, catalog_id, USER_STATE)

            elif current_route.startswith("/reference_detail/"):
                catalog_id = int(current_route.split("/")[-1])
                v = ReferenceDetailView(page, navigate, catalog_id, USER_STATE)

            elif current_route.startswith("/my_plant_details/"):
                pid = int(current_route.split("/")[-1])
                v = MyPlantDetailsView(page, navigate, pid, USER_STATE)

            elif current_route.startswith("/search"):
                query = unquote(current_route.split("q=")[-1]) if "q=" in current_route else ""
                v = SearchView(page, navigate, query, USER_STATE)

            # Б. Статические маршруты
            elif current_route.startswith("/auth"):
                is_register = "?mode=register" in current_route
                v = AuthView(page, navigate, USER_STATE, is_register_mode=is_register)

            elif current_route == "/user_home":
                v = UserHomeView(page, navigate, USER_STATE)
            
            elif current_route == "/my_plants":
                v = MyPlantsView(page, navigate, USER_STATE)
            
            elif current_route == "/scanner":
                # Передаем page.scan_picker как global_picker
                v = ScannerView(page, navigate, USER_STATE, page.scan_picker)

            elif current_route == "/add_plant":
                if AddPlantView:
                    v = AddPlantView(page, navigate, USER_STATE)
                else:
                    # Если вьюха добавления не готова, возвращаем на сканер
                    page.snack_bar = ft.SnackBar(ft.Text("Ошибка: AddPlantView не импортирован"))
                    page.snack_bar.open = True
                    v = ScannerView(page, navigate, USER_STATE, page.scan_picker)
            
            elif current_route == "/catalog":
                v = CatalogView(page, navigate, USER_STATE)
            
            elif current_route == "/profile":
                v = ProfileView(page, navigate, USER_STATE)

            elif current_route == "/calendar":
                v = CalendarView(page, navigate, USER_STATE)

            elif current_route == "/notifications":
                v = NotificationsView(page, navigate, USER_STATE)
                
            elif current_route == "/analytics":
                v = AnalyticsView(page, navigate, USER_STATE)
                
            elif current_route == "/details":
                v = DetailsView(page, navigate)

            elif current_route in ["/", ""]:
                v = HomeView(page, navigate)

        except Exception as route_ex:
            print(f"Критическая ошибка роутинга: {route_ex}")
            v = UserHomeView(page, navigate, USER_STATE)

        if v is None: return

        # --- УПРАВЛЕНИЕ СТЕКОМ ---
        root_routes = ["/", "/user_home", "/catalog", "/my_plants", "/profile"]
        if current_route in root_routes:
            page.views.clear()
        
        if len(page.views) > 0 and page.views[-1].route == current_route:
            return

        # --- НАВБАР (NavBar) ---
        hide_nav_on = ["/", "/analytics", "/details", "/search", "/add_plant", "/auth"]
        
        is_detail_page = (
            current_route.startswith("/reference") or 
            current_route.startswith("/my_plant_details") or
            current_route.startswith("/auth")
        )

        if is_detail_page or current_route in hide_nav_on or not NavBar:
            v.bottom_appbar = None
        else:
            nav_map = {"/user_home": 0, "/my_plants": 1, "/scanner": 2, "/profile": 3}
            active_index = nav_map.get(current_route, 0)
            
            def on_nav_click(idx):
                target_routes = ["/user_home", "/my_plants", "/scanner", "/profile"]
                if 0 <= idx < len(target_routes):
                    page.go(target_routes[idx])
            
            v.bottom_appbar = NavBar(active_index, on_nav_click)
        
        page.views.append(v)
        page.update()

    def handle_view_pop(e):
        if len(page.views) > 1:
            page.views.pop()
            top_view = page.views[-1]
            page.route = top_view.route
            page.update()
        else:
            page.go("/user_home")

    page.on_route_change = handle_route_change
    page.on_view_pop = handle_view_pop
    
    page.go(page.route or "/")

if __name__ == "__main__":
    # upload_dir важен для корректной работы ScannerView в Web-режиме
    ft.app(
        target=main, 
        assets_dir="assets",
        upload_dir="assets/uploads",
    )