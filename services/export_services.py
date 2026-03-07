import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont, TTFError
from config import Config

class ExportService:
    @staticmethod
    def _init_pdf_engine():
        # инициализация дежавю санс — самого стабильного шрифта для python pdf. 
        # он гарантированно поддерживает кириллицу и совместим с парсером reportlab. 
        # файл должен лежать по пути assets/fonts/DejaVuSans.ttf.
        font_path = os.path.join(Config.FONTS_DIR, "DejaVuSans.ttf")
        
        if os.path.exists(font_path):
            try:
                # регистрируем шрифт под именем 'DejaVu'
                pdfmetrics.registerFont(TTFont('DejaVu', font_path))
                return 'DejaVu'
            except Exception as e:
                print(f"предупреждение: не удалось загрузить {font_path}: {e}")
                return 'Helvetica'
        
        print("предупреждение: файл шрифта не найден, откат к Helvetica")
        return 'Helvetica'

    @staticmethod
    def create_plant_pdf(data: dict) -> str:
        if not os.path.exists(Config.REPORTS_DIR):
            os.makedirs(Config.REPORTS_DIR, exist_ok=True)

        filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = os.path.join(Config.REPORTS_DIR, filename)
        
        font_name = ExportService._init_pdf_engine()
        doc = SimpleDocTemplate(filepath, pagesize=A4)
        
        # создание стилей с поддержкой выбранного шрифта
        rus_style = ParagraphStyle(
            'RusNormal', 
            fontName=font_name, 
            fontSize=10, 
            leading=12
        )
        title_style = ParagraphStyle(
            'RusTitle', 
            fontName=font_name, 
            fontSize=16, 
            leading=20, 
            alignment=1,
            spaceAfter=20
        )

        elements = []
        
        # 1. заголовок
        elements.append(Paragraph(f"ОТЧЕТ ПО РАСТЕНИЮ: {data['name'].upper()}", title_style))

        # 2. технические данные
        table_data = [
            [Paragraph("Характеристика", rus_style), Paragraph("Значение", rus_style)],
            [Paragraph("Вид", rus_style), Paragraph(data['species'], rus_style)],
            [Paragraph("Латынь", rus_style), Paragraph(data['latin'], rus_style)],
            [Paragraph("Дисциплина полива", rus_style), Paragraph(f"{data['care_data']['score']}%", rus_style)],
            [Paragraph("Общий рост", rus_style), Paragraph(f"{data['growth_data']['delta']} см", rus_style)]
        ]

        main_table = Table(table_data, colWidths=[150, 250])
        main_table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('FONTNAME', (0,0), (-1,-1), font_name),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('LEFTPADDING', (0,0), (-1,-1), 10),
        ]))
        elements.append(main_table)

        # сборка документа
        try:
            doc.build(elements)
            return filepath
        except Exception as e:
            print(f"критическая ошибка сборки pdf: {e}")
            return ""