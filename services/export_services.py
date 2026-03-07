import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from config import Config

class ExportService:
    @staticmethod
    def _init_pdf_engine():
        # настройка движка генерации документов. 
        # стандартные шрифты pdf не поддерживают кириллицу, поэтому 
        # мы принудительно регистрируем шрифт freesans. 
        # файл шрифта должен находиться в assets/fonts/FreeSans.ttf.
        font_path = os.path.join(Config.FONTS_DIR, "FreeSans.ttf")
        if os.path.exists(font_path):
            pdfmetrics.registerFont(TTFont('FreeSans', font_path))
            return 'FreeSans'
        return 'Helvetica'

    @staticmethod
    def create_plant_pdf(data: dict) -> str:
        # генерация строгого технического отчета в формате pdf. 
        # документ строится по сетке a4 и включает в себя: заголовок, 
        # паспортную таблицу характеристик и детальный журнал всех изменений. 
        # использование TableStyle обеспечивает профессиональный вид с сеткой и заливкой.
        
        if not os.path.exists(Config.REPORTS_DIR):
            os.makedirs(Config.REPORTS_DIR, exist_ok=True)

        filename = f"report_{datetime.now().strftime('%H%M%S')}.pdf"
        filepath = os.path.join(Config.REPORTS_DIR, filename)
        
        font = ExportService._init_pdf_engine()
        doc = SimpleDocTemplate(filepath, pagesize=A4)
        styles = getSampleStyleSheet()
        
        # стиль для русского текста
        normal_style = ParagraphStyle('Rus', fontName=font, fontSize=10, leading=12)
        header_style = ParagraphStyle('RusH', fontName=font, fontSize=16, leading=20, alignment=1)

        elements = []

        # 1. заголовок
        elements.append(Paragraph(f"ТЕХНИЧЕСКИЙ ОТЧЕТ: {data['name'].upper()}", header_style))
        elements.append(Spacer(1, 20))

        # 2. таблица характеристик (строгий стиль)
        table_data = [
            [Paragraph("Параметр", normal_style), Paragraph("Значение", normal_style)],
            [Paragraph("Биологический вид", normal_style), Paragraph(data['species'], normal_style)],
            [Paragraph("Латинское название", normal_style), Paragraph(data['latin'], normal_style)],
            [Paragraph("Дисциплина ухода", normal_style), Paragraph(f"{data['care_data']['score']}%", normal_style)],
            [Paragraph("Общий прирост", normal_style), Paragraph(f"{data['growth_data']['delta']} см", normal_style)]
        ]

        main_table = Table(table_data, colWidths=[150, 250])
        main_table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('PADDING', (0,0), (-1,-1), 6)
        ]))
        elements.append(main_table)
        elements.append(Spacer(1, 25))

        # 3. журнал замеров
        elements.append(Paragraph("ЖУРНАЛ МОНИТОРИНГА РОСТА", normal_style))
        elements.append(Spacer(1, 10))

        log_rows = [[Paragraph("Дата", normal_style), Paragraph("Высота", normal_style), Paragraph("Заметка", normal_style)]]
        for log in data['history']:
            log_rows.append([
                Paragraph(log.measured_at.strftime("%d.%m.%Y"), normal_style),
                Paragraph(f"{log.height} см", normal_style),
                Paragraph(log.note or "-", normal_style)
            ])

        log_table = Table(log_rows, colWidths=[80, 80, 240])
        log_table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
        ]))
        elements.append(log_table)

        # сборка файла
        try:
            doc.build(elements)
            return filepath
        except Exception as e:
            print(f"Ошибка сохранения PDF: {e}")
            return ""