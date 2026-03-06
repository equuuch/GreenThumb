import flet as ft
from components.nav_bar import NavBar

# Импорт экранов
from views.home_view import HomeView
from views.my_plants_view import MyPlantsView
from views.catalog_view import CatalogView
from views.profile_view import ProfileView
from views.auth_view import AuthView
from views.notify_view import NotificationsView
from views.add_plant_view import AddPlantView
from views.details_view import DetailsView

BG_COLOR = "#F9F9F9"

@ft.component
def App():
    route, set_route = ft.use_state(ft.context.page.route or "/")
    tab_index, set_tab_index = ft.use_state(0)

    def handle_route_change(e):
        set_route(e.route)
        if e.route == "/": set_tab_index(0)
        elif e.route == "/my_plants": set_tab_index(1)
        elif e.route == "/catalog": set_tab_index(2)
        elif e.route == "/profile": set_tab_index(3)

    ft.context.page.on_route_change = handle_route_change

    def on_nav_change(e):
        index = e.control.selected_index
        set_tab_index(index)
        if index == 0: ft.context.page.go("/")
        elif index == 1: ft.context.page.go("/my_plants")
        elif index == 2: ft.context.page.go("/catalog")
        elif index == 3: ft.context.page.go("/profile")

    def get_content():
        if route == "/": return HomeView()
        if route == "/my_plants": return MyPlantsView()
        if route == "/catalog": return CatalogView()
        if route == "/profile": return ProfileView()
        if route == "/auth": return AuthView()
        if route == "/notifications": return NotificationsView()
        if route == "/add_plant": return AddPlantView()
        if route == "/details": return DetailsView()
        return ft.Text(f"Страница {route} не найдена", color="black")

    view = ft.View(route=route)
    view.bgcolor = BG_COLOR
    view.padding = 0
    
    if route in ["/", "/my_plants", "/catalog", "/profile"]:
        view.navigation_bar = NavBar(
            selected_index=tab_index, 
            on_change_callback=on_nav_change
        )
    
    view.controls.append(ft.Container(content=get_content(), expand=True))
    return view

def main(page: ft.Page):
    page.title = "GreenThumb"
    # Оставляем только базовые цвета, которые точно не упадут
    page.theme = ft.Theme(
        color_scheme=ft.ColorScheme(
            primary="white",      # Цвет текста активной вкладки
            secondary="#009753"   # Цвет кружка (индикатора)
        )
    )
    page.bgcolor = BG_COLOR
    page.render_views(App)

if __name__ == "__main__":
    ft.run(main)