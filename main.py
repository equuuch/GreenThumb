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
from views.search_view import SearchView
from urllib.parse import unquote
from views.details_view import DetailsView

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
    page.bgcolor = ft.Colors.WHITE
    page.padding = 0
    
    # Мобильные размеры окна
    page.window_width = 400
    page.window_height = 800

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
                    # Извлекаем ID (последняя часть пути)
                    catalog_id = int(page.route.split("/")[-1])
                    v = ReferenceView(page, navigate, catalog_id, USER_STATE)
                except (ValueError, IndexError):
                    print("ОШИБКА: Неверный ID в ссылке")
                    v = HomeView(page, navigate)

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

            # 4. Стандартные маршруты
            elif page.route == "/user_home":
                v = UserHomeView(page, navigate, USER_STATE)
            
            elif page.route == "/my_plants":
                v = MyPlantsView(page, navigate, USER_STATE)
            
            elif page.route == "/scanner":
                v = ScannerView(page, navigate, USER_STATE)
            
            elif page.route == "/profile":
                v = ProfileView(page, navigate, USER_STATE)
            
            elif page.route == "/analytics":
                v = AnalyticsView(page, navigate) 
            
            elif page.route == "/my_plant_details":
                v = MyPlantDetailsView(page, navigate, USER_STATE)
            
            elif page.route == "/details":
                v = DetailsView(page, navigate)
            
            elif page.route == "/" or page.route == "":
                v = HomeView(page, navigate)
            
            else:
                # Если маршрут не найден, возвращаем на главную
                print(f"DEBUG: Маршрут {page.route} не распознан")
                v = HomeView(page, navigate)

            # --- НАСТРОЙКА NAVBAR ---
            # Скрываем NavBar на Гостевом экране, Авторизации, Деталях и Поиске
            hide_nav_on = ["/", "/auth", "/my_plant_details", "/analytics", "/details", "/search"]
            
            # Также скрываем меню на экране справочника и авторизации с параметром
            is_reference = page.route.startswith("/reference/")
            is_auth = page.route.startswith("/auth")

            if page.route not in hide_nav_on and not is_reference and not is_auth and NavBar:
                def on_nav_click(idx):
                    routes = ["/user_home", "/my_plants", "/scanner", "/profile"]
                    navigate(routes[idx])
                v.bottom_appbar = NavBar(current_index, on_nav_click)
            
            # Добавляем вьюху на страницу
            page.views.append(v)

        except Exception as ex:
            print(f"КРИТИЧЕСКАЯ ОШИБКА РОУТЕРА: {ex}")
            # Вывод ошибки на экран вместо белого пятна
            page.views.append(
                ft.View(
                    controls=[
                        ft.Container(
                            content=ft.Text(f"Ошибка навигации:\n{ex}", color="red", text_align="center"),
                            alignment=ft.Alignment(0, 0),
                            expand=True
                        )
                    ]
                )
            )
        
        page.update()

    # Привязываем обработчик события
    page.on_route_change = handle_route_change
    
    # Стартовый запуск (принудительно вызываем отрисовку "/")
    if page.route == "" or page.route == "/":
        page.route = "/"
    
    handle_route_change(None)

if __name__ == "__main__":
    # assets_dir="assets" обязателен для работы картинок
    ft.run(main, assets_dir="assets")