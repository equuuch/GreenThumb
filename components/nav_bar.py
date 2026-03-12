import flet as ft

def NavBar(selected_index: int, on_change_callback):
    
    def tab_clicked(e):
        try:
            idx = int(e.control.data)
            on_change_callback(idx)
        except:
            pass

    def create_tab(index, icon_unselected, icon_selected, label):
        is_active = (selected_index == index)
        active_color = "#009753"
        inactive_color = "black"
        
        target_color = active_color if is_active else inactive_color
        target_icon = icon_selected if is_active else icon_unselected
        
        icon_obj = ft.Icon(target_icon, color=target_color, size=26)
        
        tab_content = ft.Column(
            controls=[
                icon_obj,
                ft.Text(value=label, color=target_color, size=11, weight="bold" if is_active else "normal")
            ],
            spacing=2,
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )

        return ft.Container(
            data=index,
            bgcolor="transparent",
            content=tab_content,
            expand=True,
            on_click=tab_clicked
        )

    nav_row = ft.Row(
        controls=[
            create_tab(0, ft.Icons.HOME_OUTLINED, ft.Icons.HOME, "Главная"),
            create_tab(1, ft.Icons.ECO_OUTLINED, ft.Icons.ECO, "Растения"),
            create_tab(2, ft.Icons.QR_CODE_SCANNER, ft.Icons.QR_CODE_SCANNER, "Сканировать"),
            create_tab(3, ft.Icons.PERSON_OUTLINE, ft.Icons.PERSON, "Профиль"),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
    )

    # ВОЗВРАЩАЕМ BottomAppBar
    return ft.BottomAppBar(
        content=ft.Container(
            content=nav_row,
            padding=ft.padding.only(top=10, bottom=10, left=10, right=10),
            bgcolor="#E8E8E8", # Цвет фона здесь
        ),
        bgcolor="#E8E8E8", # И здесь для надежности
        height=80,
    )