import flet as ft

def NavBar(selected_index: int, on_change_callback):
    
    def tab_clicked(e):
        print(f"Клик по вкладке {e.control.data}") # Проверка в терминале
        on_change_callback(e.control.data)

    def create_tab(index, icon_unselected, icon_selected, label):
        is_active = selected_index == index
        color = "#009753" if is_active else "black"
        icon = icon_selected if is_active else icon_unselected
        
        return ft.Container(
            data=index,
            bgcolor="transparent", # ВОТ РЕШЕНИЕ: теперь вся зона вокруг иконки кликабельна
            content=ft.Column([
                ft.Icon(icon, color=color, size=26),
                ft.Text(label, color=color, size=11, weight="bold" if is_active else "normal")
            ], spacing=2, alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            expand=True,
            on_click=tab_clicked
        )

    return ft.BottomAppBar(
        content=ft.Container(
            content=ft.Row([
                create_tab(0, ft.Icons.HOME_OUTLINED, ft.Icons.HOME, "Главная"),
                create_tab(1, ft.Icons.ECO_OUTLINED, ft.Icons.ECO, "Растения"),
                create_tab(2, ft.Icons.QR_CODE_SCANNER, ft.Icons.QR_CODE_SCANNER, "Сканировать"),
                create_tab(3, ft.Icons.PERSON_OUTLINE, ft.Icons.PERSON, "Профиль"),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.only(top=10, bottom=5)
        ),
        bgcolor="#E8E8E8",
        padding=0
    )