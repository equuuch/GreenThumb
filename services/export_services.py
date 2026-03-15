import os
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from config import Config
from datetime import datetime

class ExportService:
    """сервисный слой инкапсулирующий логику низкоуровневого формирования аналитической документации в формате pdf"""

    @staticmethod
    def create_plant_pdf(data: dict) -> str:
        """алгоритм бинарного рендеринга документа на основе агрегированных данных о жизненном цикле растения"""
        
        # блок подготовки файловой инфраструктуры: проверка наличия целевой директории и её автоматическое создание для предотвращения ошибок ввода-вывода
        if not os.path.exists(Config.REPORTS_DIR):
            os.makedirs(Config.REPORTS_DIR)

        # формирование уникального пути к файлу с использованием динамического имени и временной метки для обеспечения уникальности имен в файловой системе
        file_name = f"Report_{data['name']}_{datetime.now().strftime('%Y%m%d')}.pdf"
        file_path = os.path.join(Config.REPORTS_DIR, file_name)

        # инициализация базового шаблона документа формата а4 с использованием объектной модели библиотеки reportlab для прямого построения pdf-структуры
        doc = SimpleDocTemplate(file_path, pagesize=A4)
        
        # регистрация внешнего true type шрифта dejavusans для реализации полноценной поддержки кириллицы, так как базовые шрифты pdf ограничены кодировкой latin-1
        font_path = os.path.join(Config.FONTS_DIR, "DejaVuSans.ttf")
        pdfmetrics.registerFont(TTFont('DejaVu', font_path))
        
        # декларативное описание стилей оформления: настройка кегля, интерлиньяжа, выравнивания и цветовых акцентов для различных логических блоков документа
        styles = {
            'Title': ParagraphStyle('Title', fontName='DejaVu', fontSize=18, alignment=1, spaceAfter=20),
            'Normal': ParagraphStyle('Normal', fontName='DejaVu', fontSize=10, leading=14),
            'Heading': ParagraphStyle('Heading', fontName='DejaVu', fontSize=12, weight='bold', spaceBefore=10),
            'Advice': ParagraphStyle('Advice', fontName='DejaVu', fontSize=11, leftIndent=20, italic=True, color=colors.darkgreen)
        }

        # создание буферного списка для накопления элементов визуальной структуры документа перед финальной сборкой
        elements = []

        # добавление в очередь рендеринга главных информационных блоков: названия растения и точного времени формирования отчетного документа
        elements.append(Paragraph(f"Отчет по растению: {data['name']}", styles['Title']))
        elements.append(Paragraph(f"Сформирован: {data['report_date']}", styles['Normal']))
        elements.append(Spacer(1, 12)) # вставка технического пустого пространства для соблюдения визуальных отступов

        # формирование структуры табличных данных: консолидация биологических параметров, статистики роста и показателей дисциплины ухода
        table_data = [
            [Paragraph("Параметр", styles['Normal']), Paragraph("Значение", styles['Normal'])],
            ["Вид:", data['species']],
            ["Латынь:", data['latin']],
            ["Дата добавления:", data['added_at']],
            ["Текущий рост:", data['current_height']],
            ["Прогресс роста:", data['growth_delta']],
            ["Дисциплина ухода:", data['discipline_score']],
        ]

        # инициализация графического компонента таблицы с жестким распределением ширины колонок для корректного позиционирования на листе
        t = Table(table_data, colWidths=[150, 250])
        
        # применение комплексного стиля оформления таблицы: отрисовка сетки, управление шрифтами и заливка фона заголовка для улучшения читаемости
        t.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey), # построение координатной сетки ячеек
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgreen), # цветовое выделение первой строки
            ('FONTNAME', (0, 0), (-1, -1), 'DejaVu'), # установка зарегистрированного шрифта для всей таблицы
            ('PADDING', (0, 0), (-1, -1), 6), # настройка внутренних полей для предотвращения слипания текста с границами
        ]))
        elements.append(t)
        
        # блок визуализации аналитического заключения: вставка разделителя и вывод текстовых рекомендаций от системы на основе данных мониторинга
        elements.append(Spacer(1, 20))
        elements.append(Paragraph("Анализ и рекомендации агронома:", styles['Heading']))
        elements.append(Spacer(1, 5))
        elements.append(Paragraph(data['advice'], styles['Advice']))

        # финальный процесс компиляции всех элементов в единый бинарный поток и физическая запись документа на диск устройства
        doc.build(elements)
        
        # возврат абсолютного или относительного пути к созданному файлу для его последующего открытия системными средствами просмотра pdf
        return file_path