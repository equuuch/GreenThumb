import flet as ft

@ft.component
def NavBar(selected_index: int, on_change_callback):
    return ft.NavigationBar(
        selected_index=selected_index,
        bgcolor="#6E6E6E",  # Темно-зеленый фон
        on_change=on_change_callback,
        destinations=[
            ft.NavigationBarDestination(
                icon=ft.Icon(ft.Icons.HOME_OUTLINED, color="white"), 
                selected_icon=ft.Icon(ft.Icons.HOME, color="green"), 
                label="Сад"
            ),
            ft.NavigationBarDestination(
                icon=ft.Icon(ft.Icons.ECO_OUTLINED, color="white"), 
                selected_icon=ft.Icon(ft.Icons.ECO, color="white"), 
                label="Растения"
            ),
            ft.NavigationBarDestination(
                icon=ft.Icon(ft.Icons.QR_CODE_SCANNER, color="white"), 
                label="Сканер"
            ),
            ft.NavigationBarDestination(
                icon=ft.Icon(ft.Icons.PERSON_OUTLINE, color="white"), 
                selected_icon=ft.Icon(ft.Icons.PERSON, color="white"), 
                label="Профиль"
            ),
        ],
    )