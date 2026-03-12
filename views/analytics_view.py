import flet as ft
from database.session import SessionLocal
from database.models import GrowthLog, Plant
from sqlalchemy import select
import traceback

def AnalyticsView(page: ft.Page, nav, user_state):
    view = ft.View()
    view.route = "/analytics"
    view.bgcolor = "#F9F9F9"
    # Прячем системный скролл, чтобы не было полосы справа
    view.scroll = ft.ScrollMode.HIDDEN 

    try:
        u_id = int(user_state.get("id", 0))
    except (ValueError, TypeError):
        u_id = 0
    
    chart_container = ft.Container(expand=True)
    history_container = ft.Column(spacing=10, scroll=ft.ScrollMode.ADAPTIVE, expand=True)
    
    state = {"selected_card": None}

    def on_log_click(e):
        if state["selected_card"]:
            state["selected_card"].bgcolor = "white"
            state["selected_card"].border = None
            state["selected_card"].update()
        
        e.control.bgcolor = ft.Colors.with_opacity(0.1, "#009753")
        e.control.border = ft.border.all(2, "#009753")
        state["selected_card"] = e.control
        e.control.update()

    def update_chart(e=None):
        selected_plant_id = plant_dropdown.value
        db_inner = SessionLocal()
        data_points = []
        max_y = 10.0
        history_container.controls.clear()

        try:
            # Загружаем логи
            query = select(GrowthLog).order_by(GrowthLog.measured_at.desc())
            if selected_plant_id and selected_plant_id != "all":
                query = query.where(GrowthLog.plant_id == int(selected_plant_id))
            else:
                query = query.join(Plant).where(Plant.user_id == u_id)

            logs = db_inner.scalars(query).all()

            if logs:
                sorted_logs = sorted(logs, key=lambda x: x.measured_at)
                for i, log in enumerate(sorted_logs):
                    val = round(float(log.height), 1) if log.height else 0.0
                    
                    # Настраиваем стиль всплывающей подсказки (тултипа)
                    data_points.append(
                        ft.LineChartDataPoint(
                            x=float(i + 1), 
                            y=val,
                            tooltip=f"{val}", 
                            tooltip_style=ft.TextStyle(
                                color=ft.colors.WHITE, # Белый текст
                                size=14,
                                weight=ft.FontWeight.BOLD
                            )
                        )
                    )
                    
                    if val > max_y: max_y = val + 10.0
                
                # Заполняем историю
                history_container.controls.append(ft.Text("История замеров:", weight="bold", size=16))
                for log in logs[:10]:
                    fmt_h = f"{float(log.height):.1f}"
                    history_container.controls.append(
                        ft.Container(
                            content=ft.Row([
                                ft.Icon(ft.Icons.CALENDAR_MONTH, size=18, color="grey700"),
                                ft.Column([
                                    ft.Text(f"{log.measured_at.strftime('%d.%m.%Y')}", size=14, weight="w500"),
                                    ft.Text("Замер зафиксирован", size=11, color="grey500"),
                                ], spacing=0, expand=True),
                                ft.Text(f"{fmt_h} см", size=16, weight="bold", color="#009753")
                            ]),
                            padding=15, bgcolor="white", border_radius=15,
                            on_click=on_log_click,
                            shadow=ft.BoxShadow(blur_radius=5, color="black12")
                        )
                    )

            if not data_points:
                chart_container.content = ft.Text("Нет данных для отображения", color="grey")
            else:
                chart_container.content = ft.LineChart(
                    data_series=[ft.LineChartData(
                        data_points=data_points,
                        stroke_width=3,
                        color="#009753",
                        curved=True,
                        point=True,
                        below_line_bgcolor=ft.Colors.with_opacity(0.1, "#009753"),
                    )],
                    left_axis=ft.ChartAxis(
                        labels=[ft.ChartAxisLabel(value=float(i), label=ft.Text(str(i), size=11, color="grey")) 
                                for i in range(0, int(max_y) + 5, 20)],
                        labels_size=30,
                    ),
                    bottom_axis=ft.ChartAxis(
                        labels=[ft.ChartAxisLabel(value=float(i+1), label=ft.Text(str(i+1), size=11, color="grey")) 
                                for i in range(len(data_points))],
                        labels_size=25,
                    ),
                    horizontal_grid_lines=ft.ChartGridLines(color="grey100", width=1),
                    vertical_grid_lines=ft.ChartGridLines(color="grey100", width=1),
                    border=ft.border.all(1, "grey100"),
                    min_y=0,
                    max_y=float(max_y),
                    expand=True,
                    interactive=True, 
                    tooltip_bgcolor="#009753" # Зеленый фон плашки
                )
            page.update()
        except Exception as ex:
            traceback.print_exc()
            print(f"Ошибка в AnalyticsView: {ex}")
        finally:
            db_inner.close()

    # Дропдаун с растениями
    db = SessionLocal()
    plant_options = [ft.dropdown.Option(key="all", text="Все растения")]
    try:
        user_plants = db.scalars(select(Plant).where(Plant.user_id == u_id)).all()
        for p in user_plants:
            plant_options.append(ft.dropdown.Option(key=str(p.plant_id), text=p.custom_name))
    finally:
        db.close()

    plant_dropdown = ft.Dropdown(
        label="Растение",
        options=plant_options, value="all",
        on_change=update_chart,
        border_radius=15, bgcolor="white",
        prefix_icon=ft.Icons.SEARCH,
        focused_border_color="#009753", # Зеленая обводка при клике
        focused_color="#009753"         # Зеленый текст лейбла при клике
    )

    # --- AppBar с ЧЕРНОЙ кнопкой назад ---
    view.controls.append(
        ft.AppBar(
            title=ft.Text("Аналитика"), 
            bgcolor="white",
            leading=ft.IconButton(
                icon=ft.Icons.ARROW_BACK_IOS_NEW_ROUNDED,
                icon_color=ft.Colors.BLACK, # Кнопка стала черной
                on_click=lambda _: page.go("/user_home")
            )
        )
    )
    
    info_hint = ft.Container(
        content=ft.Row([
            ft.Icon(ft.Icons.INFO_OUTLINE, color=ft.colors.BLUE_GREY_400, size=22),
            ft.Text(
                "Для более точного и детального графика рекомендуем регулярно фиксировать изменения роста.",
                size=12,
                color=ft.colors.BLUE_GREY_600,
                expand=True,
            )
        ]),
        bgcolor=ft.colors.BLUE_GREY_50,
        padding=12,
        border_radius=15,
        margin=ft.padding.only(top=15, bottom=5)
    )
    
    view.controls.append(
        ft.Container(
            padding=20, expand=True,
            content=ft.Column([
                ft.Text("Динамика роста", size=26, weight="bold"),
                ft.Text("График изменения высоты", size=14, color="grey500"),
                ft.Container(height=10),
                plant_dropdown,
                ft.Container(height=15),
                ft.Container(
                    content=chart_container,
                    bgcolor="white", 
                    padding=ft.padding.only(left=5, right=20, top=20, bottom=5),
                    border_radius=25, 
                    height=280, 
                    shadow=ft.BoxShadow(blur_radius=15, color="black12")
                ),
                info_hint,
                ft.Container(height=15),
                ft.Container(content=history_container, expand=True) 
            ], spacing=0)
        )
    )

    update_chart()
    return view