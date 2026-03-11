import flet as ft
from database.session import init_db

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
from urllib.parse import unquote

# Попытка импорта NavBar (если файла нет, будет None)
try:
    from components.nav_bar import NavBar
except ImportError:
    NavBar = None

# Глобальный стейт приложения (user_id=None означает Гость)
USER_STATE = {"id": None, "name": "Гость"}

def main(page: ft.Page):
    # 1. Инициализация БД при старте
    init_db()

    page.title = "GreenThumb"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = "white"
    page.padding = 0
    
    # Мобильные размеры окна
    page.window.width = 400
    page.window.height = 800

    # Создаем пикер ОДИН раз и сохраняем его прямо в объект страницы
    if not hasattr(page, "scan_picker"):
        page.scan_picker = ft.FilePicker()
        page.overlay.append(page.scan_picker)

    # --- ФУНКЦИЯ НАВИГАЦИИ ---
    def navigate(route_str):
        page.route = route_str
        handle_route_change(None)

    # --- ГЛАВНЫЙ ОБРАБОТЧИК МАРШРУТОВ ---
    def handle_route_change(e):
        print(f"DEBUG: Текущий маршрут: {page.route}")
        page.views.clear()
        
        # Индекс для нижней навигации (NavBar)
        nav_map = {"/user_home": 0, "/my_plants": 1, "/scanner": 2, "/profile": 3}
        current_index = nav_map.get(page.route, 0)

        try:
            # 1. Логика динамических маршрутов (Справочник /reference/ID)
            if page.route.startswith("/reference/"):
                try:
                    catalog_id = int(page.route.split("/")[-1])
                    v = ReferenceView(page, navigate, catalog_id, USER_STATE)
                except: v = HomeView(page, navigate)
            
            # 2. Логика поиска с ИИ (/search?q=Запрос)
            elif page.route.startswith("/search"):
                try:
                    query = unquote(page.route.split("q=")[-1])
                    v = SearchView(page, navigate, query, USER_STATE)
                except Exception as ex:
                    print(f"ОШИБКА ПОИСКА: {ex}")
                    v = HomeView(page, navigate)

            # 3. Авторизация с поддержкой режима (?mode=register)
            elif page.route.startswith("/auth"):
                is_register = "?mode=register" in page.route
                v = AuthView(page, navigate, USER_STATE, is_register_mode=is_register)
            
            # 4. Детали конкретного растения (/my_plant_details/ID)
            elif page.route.startswith("/my_plant_details/"):
                try:
                    pid = int(page.route.split("/")[-1])
                    v = MyPlantDetailsView(page, navigate, pid, USER_STATE)
                except: v = MyPlantsView(page, navigate, USER_STATE)

            # 5. Стандартные маршруты
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
            
            elif page.route == "/details":
                v = DetailsView(page, navigate)
            
            elif page.route == "/" or page.route == "":
                v = HomeView(page, navigate)
            
            else:
                # Если маршрут не найден, возвращаем на главную
                print(f"DEBUG: Маршрут {page.route} не распознан")
                v = HomeView(page, navigate)

            # --- НАСТРОЙКА NAVBAR ---
            hide_nav_on = ["/", "/auth", "/my_plant_details", "/analytics", "/details", "/search"]
            is_reference = page.route.startswith("/reference/")
            is_plant = page.route.startswith("/my_plant_details/")
            is_auth = page.route.startswith("/auth")

            if page.route not in hide_nav_on and not is_reference and not is_plant and not is_auth and NavBar:
                def on_click(idx):
                    routes = ["/user_home", "/my_plants", "/scanner", "/profile"]
                    navigate(routes[idx])
                v.bottom_appbar = NavBar(current_index, on_click)
            
            # Добавляем вьюху на страницу
            page.views.append(v)

        except Exception as ex:
            print(f"КРИТИЧЕСКАЯ ОШИБКА РОУТЕРА: {ex}")
            page.views.append(
                ft.View(
                    "/error",
                    controls=[ft.Text(f"Ошибка навигации:\n{ex}", color="red", text_align="center")]
                )
            )
        
        page.update()

    # Привязываем обработчик события
    page.on_route_change = handle_route_change
    
    # Стартовый запуск
    if page.route == "" or page.route == "/":
        page.route = "/"
    
    handle_route_change(None)

if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets")