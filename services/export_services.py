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
    @staticmethod
    def create_plant_pdf(data: dict) -> str:
        if not os.path.exists(Config.REPORTS_DIR):
            os.makedirs(Config.REPORTS_DIR)

        file_name = f"Report_{data['name']}_{datetime.now().strftime('%Y%m%d')}.pdf"
        file_path = os.path.join(Config.REPORTS_DIR, file_name)

        doc = SimpleDocTemplate(file_path, pagesize=A4)
        
        # Регистрируем шрифт для поддержки кириллицы
        font_path = os.path.join(Config.FONTS_DIR, "DejaVuSans.ttf")
        pdfmetrics.registerFont(TTFont('DejaVu', font_path))
        
        styles = {
            'Title': ParagraphStyle('Title', fontName='DejaVu', fontSize=18, alignment=1, spaceAfter=20),
            'Normal': ParagraphStyle('Normal', fontName='DejaVu', fontSize=10, leading=14),
            'Heading': ParagraphStyle('Heading', fontName='DejaVu', fontSize=12, weight='bold', spaceBefore=10),
            'Advice': ParagraphStyle('Advice', fontName='DejaVu', fontSize=11, leftIndent=20, italic=True, color=colors.darkgreen)
        }

        elements = []

        # Заголовок
        elements.append(Paragraph(f"Отчет по растению: {data['name']}", styles['Title']))
        elements.append(Paragraph(f"Сформирован: {data['report_date']}", styles['Normal']))
        elements.append(Spacer(1, 12))

        # Основная таблица данных
        table_data = [
            [Paragraph("Параметр", styles['Normal']), Paragraph("Значение", styles['Normal'])],
            ["Вид:", data['species']],
            ["Латынь:", data['latin']],
            ["Дата добавления:", data['added_at']],
            ["Текущий рост:", data['current_height']],
            ["Прогресс роста:", data['growth_delta']],
            ["Дисциплина ухода:", data['discipline_score']],
        ]

        t = Table(table_data, colWidths=[150, 250])
        t.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgreen),
            ('FONTNAME', (0, 0), (-1, -1), 'DejaVu'),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(t)
        
        # Блок рекомендаций
        elements.append(Spacer(1, 20))
        elements.append(Paragraph("Анализ и рекомендации агронома:", styles['Heading']))
        elements.append(Spacer(1, 5))
        elements.append(Paragraph(data['advice'], styles['Advice']))

        doc.build(elements)
        return file_path