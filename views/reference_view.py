import flet as ft

def ReferenceView(page: ft.Page, nav):
    view = ft.View()
    view.route = "/reference"
    view.bgcolor = ft.Colors.WHITE
    view.padding = 20

    header = ft.Row(
        controls=[
            ft.IconButton(ft.Icons.ARROW_BACK_IOS_NEW, icon_color="black", on_click=lambda _: nav("/scanner")),
            ft.Text(value="Справочник", size=22, weight="bold", color="black", expand=True, text_align="center"),
            ft.Container(width=40) # Заглушка для симметрии
        ]
    )

    view.controls.append(header)
    view.controls.append(ft.Text(value="Здесь будет библиотека растений...", color="black"))
    return view