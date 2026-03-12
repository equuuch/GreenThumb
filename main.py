import flet as ft
from database.session import init_db
from urllib.parse import unquote
import time

# Импорты вьюх
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
from views.calendar_view import CalendarView
from views.notifications_view import NotificationsView
# Добавлена вьюшка каталога
from views.catalog_view import CatalogView 

# Импорт вьюхи добавления растения
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
    
    page.theme = ft.Theme(
        page_transitions=ft.PageTransitionsTheme(
            android="fadeThrough",
            ios="cupertino",
            windows="fadeThrough",
            macos="zoom",
        )
    )

    # Мобильные размеры окна
    page.window.width = 400
    page.window.height = 800

    if not hasattr(page, "scan_picker"):
        page.scan_picker = ft.FilePicker()
        page.overlay.append(page.scan_picker)

    # --- ФУНКЦИЯ НАВИГАЦИИ ---
    def navigate(route_str):
        page.route = route_str
        page.go(route_str)
        page.update()

    # --- ГЛАВНЫЙ ОБРАБОТЧИК МАРШРУТОВ ---
    def handle_route_change(e):
        print(f"DEBUG: Текущий маршрут: {page.route}")
        
        # Полная очистка стека перед созданием новой вьюхи
        page.views.clear()
        
        # Карта индексов для NavBar
        nav_map = {"/user_home": 0, "/my_plants": 1, "/scanner": 2, "/profile": 3}
        current_index = nav_map.get(page.route, 0)

        try:
            # 2. Динамические маршруты
            if page.route.startswith("/reference/"):
                try:
                    catalog_id = int(page.route.split("/")[-1])
                    v = ReferenceView(page, navigate, catalog_id, USER_STATE)
                except Exception as ex_ref: 
                    print(f"ОШИБКА В РОУТЕ REFERENCE: {ex_ref}")
                    v = HomeView(page, navigate)
            
            elif page.route.startswith("/search"):
                try:
                    query = unquote(page.route.split("q=")[-1])
                    v = SearchView(page, navigate, query, USER_STATE)
                except: 
                    v = HomeView(page, navigate)

            elif page.route.startswith("/auth"):
                is_register = "?mode=register" in page.route
                v = AuthView(page, navigate, USER_STATE, is_register_mode=is_register)
            
            elif page.route.startswith("/my_plant_details/"):
                pid = int(page.route.split("/")[-1])
                v = MyPlantDetailsView(page, navigate, pid, USER_STATE)

            # 3. Стандартные маршруты
            elif page.route == "/user_home":
                v = UserHomeView(page, navigate, USER_STATE)
            
            elif page.route == "/my_plants":
                time.sleep(0.05)
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

            elif page.route == "/calendar":
                v = CalendarView(page, navigate, USER_STATE)

            elif page.route == "/notifications":
                v = NotificationsView(page, navigate, USER_STATE)
            
            # Роут для справочника (каталога)
            elif page.route == "/catalog":
                v = CatalogView(page, navigate, USER_STATE)
            
            # ИСПРАВЛЕННЫЙ РОУТ АНАЛИТИКИ (с передачей USER_STATE)
            elif page.route == "/analytics":
                v = AnalyticsView(page, navigate, USER_STATE) 
            
            elif page.route == "/details":
                v = DetailsView(page, navigate)
            
            elif page.route == "/" or page.route == "":
                v = HomeView(page, navigate)
            
            else:
                v = HomeView(page, navigate)

            # --- ЛОГИКА NAVBAR ---
            # Скрываем на логине, интро, формах добавления и справочнике
            hide_nav_on = ["/", "/auth", "/analytics", "/details", "/search", "/add_plant", "/catalog"]
            is_reference = page.route.startswith("/reference/")
            is_plant = page.route.startswith("/my_plant_details/")
            is_auth = page.route.startswith("/auth")

            if page.route not in hide_nav_on and not is_reference and not is_plant and not is_auth and NavBar:
                def on_nav_click(idx):
                    routes = ["/user_home", "/my_plants", "/scanner", "/profile"]
                    navigate(routes[idx])
                v.bottom_appbar = NavBar(current_index, on_nav_click)
            
            page.views.append(v)

        except Exception as ex:
            print(f"ОШИБКА РОУТИНГА: {ex}")
            page.views.append(ft.View("/error", controls=[ft.Text(f"Ошибка: {ex}")]))
        
        page.update()

    # --- ОБРАБОТЧИК КНОПКИ НАЗАД ---
    def handle_view_pop(e):
        if len(page.views) > 1:
            page.views.pop()
            top_view = page.views[-1]
            page.go(top_view.route)
        else:
            page.go("/")

    page.on_route_change = handle_route_change
    page.on_view_pop = handle_view_pop
    
    page.go(page.route or "/")

if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets")