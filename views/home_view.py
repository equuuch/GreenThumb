import flet as ft
from database.session import get_db
from database.models import PlantCatalog

def HomeView(page: ft.Page, nav):
    view = ft.View()
    view.route = "/"
    view.bgcolor = "#F9F9F9"
    view.padding = 20
    
    header = ft.Column([
        ft.Text("GreenThumb", size=28, weight="bold", color="#009753"),
        ft.Text("Ваш проводник в мире растений", size=14, color="gray")
    ], spacing=0)

    # ПОИСК
    search_field = ft.TextField(
        hint_text="Найти растение (например, Монстера)...",
        border_radius=15, bgcolor="white",
        prefix_icon=ft.Icons.SEARCH,
        on_submit=lambda e: nav(f"/search?q={e.control.value}")
    )

    def create_card(name, img, cat_id):
        return ft.Container(
            bgcolor="white", padding=15, border_radius=25,
            shadow=ft.BoxShadow(blur_radius=15, color="black12"),
            col={"xs": 6, "sm": 6},
            # Переход по РЕАЛЬНОМУ ID из базы
            on_click=lambda _: nav(f"/reference/{cat_id}"),
            content=ft.Column([
                ft.Image(src=img, height=120, fit="contain"),
                ft.Text(name, weight="bold", size=16, color="black", max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                ft.Text("Справочник", size=12, color="#009753")
            ], horizontal_alignment="center")
        )

    grid = ft.ResponsiveRow(spacing=20)

    # 1. Загружаем первые 4 растения из РЕАЛЬНОЙ БАЗЫ ДАННЫХ
    with next(get_db()) as db:
        popular_plants = db.query(PlantCatalog).limit(4).all()
        
        if not popular_plants:
            # Если база вообще пустая, показываем сообщение
            grid.controls.append(ft.Text("Справочник пока пуст. Воспользуйтесь поиском!", color="gray"))
        else:
            # Если в базе есть растения, создаем карточки на их основе
            # (Картинки пока берем заглушки, так как в PlantCatalog их нет)
            images = ["/aloe.png", "/hrizantema.png", "/rose.png", "/hibiscus.png"]
            
            for i, plant in enumerate(popular_plants):
                # Подставляем картинку по кругу, если растений больше 4
                img_src = images[i % len(images)] 
                
                grid.controls.append(
                    create_card(
                        name=plant.species_name, # Берем реальное имя из БД
                        img=img_src, 
                        cat_id=plant.catalog_id  # Берем реальный ID из БД!
                    )
                )

    cta_btn = ft.ElevatedButton(
        "Зарегистрироваться, чтобы создать сад",
        bgcolor="#009753", color="white",
        width=float("inf"), height=50,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=15)),
        on_click=lambda _: nav("/auth?mode=register")
    )

    lv = ft.ListView(expand=True, spacing=30)
    lv.controls.extend([header, search_field, grid, cta_btn])
    
    view.controls.append(lv)
    return view