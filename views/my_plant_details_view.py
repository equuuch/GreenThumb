import flet as ft
from database.session import get_db
from database.models import Plant, CareCalendar
from sqlalchemy.orm import joinedload
from datetime import datetime
import time
from services.plant_services import PlantService

def MyPlantDetailsView(page: ft.Page, nav, plant_id, user_state):
    """
    модуль детальной информации о растении пользователя.
    реализует логику отображения метрик состояния, редактирования данных и управления жизненным циклом экземпляра.
    """
    view = ft.View()
    view.route = f"/my_plant_details/{plant_id}"
    view.bgcolor = "white"
    view.padding = 0

    # 1. блок извлечения данных из реляционной базы данных.
    with next(get_db()) as db:
        # принудительное обновление объектов сессии для исключения использования устаревшего кэша.
        db.expire_all() 
        # выполнение запроса с использованием joinedload (eager loading) для оптимизации: 
        # связанные справочные данные загружаются одним sql-запросом.
        plant = db.query(Plant).options(
            joinedload(Plant.catalog_info)
        ).filter(Plant.plant_id == plant_id).first()

        if not plant:
            return ft.View(controls=[ft.Text("Растение не найдено")])

        # извлечение параметров экземпляра и метаданных вида из каталога.
        p_custom_name = plant.custom_name
        p_image_url = plant.image_url
        p_last_watered = plant.last_watered_at
        p_user_light = plant.user_light_level
        p_status = plant.status_text
        
        cat_info = plant.catalog_info
        p_species_name = cat_info.species_name if cat_info else "Неизвестный вид"
        p_def_interval = cat_info.default_watering_interval if (cat_info and cat_info.default_watering_interval) else 3
        p_def_light = cat_info.default_light_level if cat_info else 0.5

        # --- алгоритм расчета уровня влажности ---
        # вычисляет остаточный процент влаги на основе времени, прошедшего с момента последнего полива.
        interval_days = p_def_interval
        water_val = 0.5 
        if p_last_watered:
            interval_sec = interval_days * 24 * 3600
            diff_sec = (datetime.now() - p_last_watered).total_seconds()
            # нормирование значения в диапазоне [0.0, 1.0] для визуализации в прогресс-баре.
            water_val = max(0.0, min(1.0, 1.0 - (diff_sec / interval_sec)))

        # приоритетное использование пользовательской настройки освещенности над эталонной.
        light_val = p_user_light if p_user_light is not None else p_def_light
        # упрощенный расчет индекса здоровья на основе критического порога влаги.
        health_val = 1.0 if water_val > 0.2 else 0.4

    # --- инициализация компонентов визуальной шкалы ---
    # расчет веса контейнеров (expand) для имитации заполнения шкалы (пропорция 100).
    current_fill_weight = int(water_val * 100)
    water_bar_fill = ft.Container(
        # динамическое изменение цвета: зеленый (норма), желтый (предупреждение), красный (критично).
        bgcolor="#009753" if water_val > 0.6 else "#FFC107" if water_val > 0.3 else "#FF5252",
        height=10, expand=max(1, current_fill_weight), border_radius=5,
        animate=ft.animation.Animation(800, ft.AnimationCurve.DECELERATE) # плавная анимация при изменении.
    )
    water_bar_empty = ft.Container(expand=100 - max(1, current_fill_weight))

    # --- логика взаимодействия через модальные окна (bottom sheets) ---

    def open_growth_sheet(e):
        """метод отрисовки интерфейса фиксации физического прогресса растения."""
        height_input = ft.TextField(
            label="Высота (см)", 
            keyboard_type=ft.KeyboardType.NUMBER,
            border_color="#009753",
            focused_border_color="#004D40"
        )
        note_input = ft.TextField(label="Заметка", multiline=True)

        def save_measurement(e):
            """обработчик сохранения замера. интегрирует данные в журнал роста (growth_logs)."""
            if not height_input.value:
                height_input.error_text = "Введите высоту"
                page.update()
                return
            
            try:
                h_val = float(height_input.value.replace(",", "."))
                with next(get_db()) as db:
                    # вызов метода сервиса для атомарной записи данных и обновления статуса растения.
                    log, err = PlantService.add_measurement(
                        db=db, plant_id=plant_id, height=h_val, note=note_input.value
                    )
                    if err: return
                
                # закрытие интерфейса ввода и визуальное подтверждение операции.
                page.bottom_sheet.open = False
                page.snack_bar = ft.SnackBar(ft.Text("Замер успешно добавлен!"), bgcolor="#009753")
                page.snack_bar.open = True
                page.update()
                time.sleep(0.5)
                nav("/analytics") # переход в раздел графиков для визуализации тренда.
            except ValueError:
                height_input.error_text = "Нужно число"
                page.update()

        page.bottom_sheet = ft.BottomSheet(
            ft.Container(
                padding=30, bgcolor="white",
                border_radius=ft.border_radius.only(top_left=20, top_right=20),
                content=ft.Column([
                    ft.Text("Новый замер роста", size=20, weight="bold"),
                    height_input, note_input,
                    ft.ElevatedButton("Сохранить результат", on_click=save_measurement, bgcolor="#009753", color="white", width=float("inf"))
                ], tight=True, spacing=20)
            )
        )
        page.bottom_sheet.open = True
        page.update()

    def show_edit_sheet(e):
        """модуль управления конфигурацией и жизненным циклом растения."""
        name_input = ft.TextField(label="Название", value=p_custom_name, border_color="#009753")
        light_slider = ft.Slider(min=0, max=1, divisions=10, value=light_val, active_color="#FFC107")

        def save_changes(e):
            """фиксация изменений метаданных растения в базе данных."""
            with next(get_db()) as db:
                plant_db = db.query(Plant).filter(Plant.plant_id == plant_id).first()
                if plant_db:
                    plant_db.custom_name = name_input.value
                    plant_db.user_light_level = light_slider.value
                    db.commit()
            page.bottom_sheet.open = False
            page.update()
            nav(f"/my_plant_details/{plant_id}") 

        def handle_archive(e):
            """логика «мягкого» удаления: перевод растения в архив и отмена будущих задач."""
            with next(get_db()) as db:
                success, err = PlantService.archive_plant(db, plant_id, reason="убрано пользователем")
                if success:
                    page.bottom_sheet.open = False
                    page.snack_bar = ft.SnackBar(ft.Text("Растение перенесено в архив"), bgcolor="#455A64")
                    page.snack_bar.open = True
                    page.update()
                    time.sleep(1)
                    nav("/my_plants")

        def handle_delete_click(e):
            """процедура безвозвратного удаления данных и физических файлов изображений."""
            def final_delete(e):
                with next(get_db()) as db:
                    # вызов метода сервиса для удаления записи и очистки файловой системы.
                    success, err = PlantService.delete_plant_permanently(db, plant_id)
                    if success:
                        confirm_dialog.open = False
                        page.bottom_sheet.open = False
                        page.snack_bar = ft.SnackBar(ft.Text("Растение безвозвратно удалено"), bgcolor="#D32F2F")
                        page.snack_bar.open = True
                        page.update()
                        time.sleep(1)
                        nav("/my_plants")
            
            # реализация паттерна подтверждения (confirmation dialog) для деструктивных действий.
            confirm_dialog = ft.AlertDialog(
                title=ft.Text("Удаление"),
                content=ft.Text(f"Вы уверены, что хотите полностью удалить '{p_custom_name}'? Это действие нельзя отменить."),
                actions=[
                    ft.TextButton("Отмена", on_click=lambda _: setattr(confirm_dialog, "open", False)),
                    ft.ElevatedButton("Да, удалить", bgcolor="red", color="white", on_click=final_delete),
                ]
            )
            page.overlay.append(confirm_dialog)
            confirm_dialog.open = True
            page.update()

        # сборка интерфейса редактирования в формате выплывающей панели.
        page.bottom_sheet = ft.BottomSheet(
            ft.Container(
                padding=30, bgcolor="white",
                border_radius=ft.border_radius.only(top_left=20, top_right=20),
                content=ft.Column([
                    ft.Row([
                        ft.Text("Редактирование", size=20, weight="bold"),
                        ft.IconButton(ft.Icons.CLOSE, on_click=lambda _: setattr(page.bottom_sheet, "open", False))
                    ], alignment="spaceBetween"),
                    name_input,
                    ft.Text("Освещенность", size=14, color="grey"),
                    light_slider,
                    ft.ElevatedButton("Сохранить изменения", on_click=save_changes, bgcolor="#009753", color="white", width=float("inf"), height=50),
                    
                    # блок кнопок управления статусом.
                    ft.Row([
                        ft.TextButton(
                            icon=ft.Icons.ARCHIVE_OUTLINED,
                            icon_color="blue-grey-400",
                            content=ft.Text("В архив", color="blue-grey-400"),
                            on_click=handle_archive,
                            expand=True
                        ),
                        ft.TextButton(
                            icon=ft.Icons.DELETE_FOREVER_OUTLINED,
                            icon_color="red-400",
                            content=ft.Text("Удалить", color="red-400"),
                            on_click=handle_delete_click,
                            expand=True
                        ),
                    ], spacing=10)
                ], tight=True, spacing=15)
            )
        )
        page.bottom_sheet.open = True
        page.update()

    # --- обработка процедур ухода ---

    def handle_watering(e):
        """метод подтверждения выполнения задачи полива. синхронизирует состояние бд и ui."""
        e.control.disabled = True # предотвращение дублирования транзакций.
        e.control.content = ft.ProgressRing(width=20, height=20, color="white", stroke_width=2)
        page.update()

        with next(get_db()) as db:
            plant_db = db.query(Plant).filter(Plant.plant_id == plant_id).first()
            if plant_db:
                # обновление временной метки последнего ухода.
                plant_db.last_watered_at = datetime.now()
                # поиск и закрытие соответствующей записи в календаре задач.
                task = db.query(CareCalendar).filter(
                    CareCalendar.plant_id == plant_id,
                    CareCalendar.task_type == "watering",
                    CareCalendar.is_completed == False
                ).first()
                if task:
                    task.is_completed = True
                    task.completion_date = datetime.now()
                db.commit()

        # реактивное обновление визуальных шкал после завершения транзакции.
        water_bar_fill.expand = 100
        water_bar_fill.bgcolor = "#009753"
        page.snack_bar = ft.SnackBar(ft.Text("Растение полито!"), bgcolor="#009753")
        page.snack_bar.open = True
        page.update()
        time.sleep(1.2)
        nav("/my_plants")

    def create_stat(label, icon, val, custom_fill=None, custom_empty=None):
        """универсальный визуальный компонент для рендеринга метрик со шкалой прогресса."""
        color = "#009753" if val > 0.6 else "#FFC107" if val > 0.3 else "#FF5252"
        safe_val = max(1, int(val * 100))
        # использование механизма expand для пропорционального деления ширины контейнера.
        fill = custom_fill if custom_fill else ft.Container(bgcolor=color, height=10, expand=safe_val, border_radius=5)
        empty = custom_empty if custom_empty else ft.Container(expand=100 - safe_val)

        return ft.Column([
            ft.Row([ft.Icon(icon, size=18, color=color), ft.Text(label, size=14, weight="w600")], spacing=10),
            ft.Container(bgcolor="#F0F0F0", height=10, border_radius=5, content=ft.Row([fill, empty], spacing=0)),
            ft.Container(height=10)
        ])

    # --- финальная компоновка визуальной структуры (layout) ---

    clean_img_path = p_image_url.replace("\\", "/") if p_image_url else None
    img_src = clean_img_path if clean_img_path else "aloe.png"

    # шапка экрана: использование Stack для наложения кнопок навигации на медиа-контент.
    header = ft.Stack([
        ft.Image(src=img_src, fit=ft.ImageFit.COVER, width=400, height=400),
        ft.Container(
            padding=ft.padding.only(top=40, left=15, right=15),
            content=ft.Row([
                ft.IconButton(ft.Icons.ARROW_BACK_IOS_NEW, icon_color="black", bgcolor="white70", on_click=lambda _: nav("/my_plants")),
                ft.IconButton(ft.Icons.EDIT_OUTLINED, icon_color="black", bgcolor="white70", on_click=show_edit_sheet)
            ], alignment="spaceBetween")
        )
    ])

    # основной контейнер информации с использованием эффекта перекрытия (отрицательный margin).
    content = ft.Container(
        bgcolor="white", padding=ft.padding.all(30),
        border_radius=ft.border_radius.only(top_left=35, top_right=35),
        margin=ft.margin.only(top=-40),
        expand=True,
        content=ft.Column([
            ft.Row([
                ft.Column([
                    ft.Text(p_custom_name, size=28, weight="bold"),
                    ft.Text(p_species_name, size=16, color="grey600"),
                ]),
                # визуальный бейдж текущего статуса физического развития.
                ft.Container(content=ft.Text(p_status, size=10, color="white"), bgcolor="#009753", padding=8, border_radius=10)
            ], alignment="spaceBetween"),
            
            ft.Divider(height=40, color="transparent"),
            
            # рендеринг динамических шкал состояния.
            create_stat("Уровень влаги", ft.Icons.WATER_DROP_OUTLINED, water_val, water_bar_fill, water_bar_empty),
            create_stat("Состояние здоровья", ft.Icons.FAVORITE_OUTLINE, health_val),
            create_stat("Уровень света", ft.Icons.WB_SUNNY_OUTLINED, light_val),
            
            ft.Container(
                content=ft.Row([
                    ft.Column([
                        ft.Text("История роста", size=18, weight="bold"),
                        ft.Text("Добавьте замер для графика", size=12, color="grey"),
                    ]),
                    ft.IconButton(ft.Icons.ADD_CHART_ROUNDED, icon_color="#009753", on_click=open_growth_sheet)
                ], alignment="spaceBetween"),
                margin=ft.margin.only(top=10, bottom=10)
            ),

            # основной элемент управления для подтверждения полива.
            ft.ElevatedButton(
                content=ft.Text("Отметить полив", size=16, weight="bold"),
                bgcolor="#009753", color="white", height=55, width=float("inf"),
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=15)),
                on_click=handle_watering
            )
        ], scroll=ft.ScrollMode.ADAPTIVE)
    )

    # результирующая сборка вьюхи в единый прокручиваемый список.
    view.controls.append(ft.ListView([header, content], expand=True, padding=0))
    return view