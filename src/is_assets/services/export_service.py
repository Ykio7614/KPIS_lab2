from __future__ import annotations

import csv
from html import escape
from pathlib import Path
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


class ExportService:
    def __init__(self):
        self.font_name = 'Helvetica'
        try:
            possible_paths = [
                Path(__file__).resolve().parent.parent / "fonts" / "DejaVuSans.ttf",
                Path("fonts/DejaVuSans.ttf"),
                Path("C:/Windows/Fonts/arial.ttf"),
                Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
            ]

            for font_path in possible_paths:
                if font_path.exists():
                    pdfmetrics.registerFont(TTFont('CustomFont', str(font_path)))
                    self.font_name = 'CustomFont'
                    print(f"Font loaded: {font_path}")
                    break
            else:
                print(f"Warning: No Russian font found. Using default.")
        except Exception as e:
            print(f"Warning: Could not register font: {e}")

    def _get_styles(self, styles):
        return {
            'Title': ParagraphStyle(
                'CustomTitle',
                parent=styles['Title'],
                fontName=self.font_name,
                fontSize=16,
                alignment=1,
                spaceAfter=12,
                textColor=colors.HexColor("#2c3e50")
            ),
            'Heading': ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontName=self.font_name,
                fontSize=12,
                alignment=0,
                spaceAfter=8,
                textColor=colors.HexColor("#34495e")
            ),
            'Normal': ParagraphStyle(
                'CustomNormal',
                parent=styles['Normal'],
                fontName=self.font_name,
                fontSize=10,
                alignment=0,
            ),
            'Date': ParagraphStyle(
                'CustomDate',
                parent=styles['Normal'],
                fontName=self.font_name,
                fontSize=9,
                alignment=1,
                textColor=colors.HexColor("#7f8c8d")
            ),
        }

    def export_csv(self, headers: list[str], rows: list[dict[str, str]], output_path: str) -> Path:
        """Экспорт в CSV с правильным форматированием"""
        path = Path(output_path)
        with path.open("w", encoding="utf-8-sig", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=headers, delimiter=';')
            writer.writeheader()
            writer.writerows([{header: row.get(header, "") for header in headers} for row in rows])
        return path

    def export_doc(self, headers: list[str], rows: list[dict[str, str]], output_path: str, title: str) -> Path:
        """Экспорт в DOC (HTML с CSS для печати)"""
        path = Path(output_path)

        header_html = "".join(f"<th>{escape(header)}</th>" for header in headers)

        row_html = []
        for row in rows:
            cells = "".join(f"<td>{escape(str(row.get(header, '')))}</td>" for header in headers)
            row_html.append(f"<tr>{cells}</tr>")

        html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="utf-8">
    <title>{escape(title)}</title>
    <style>
        body {{
            font-family: 'DejaVu Sans', 'Arial', 'Helvetica', sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h2 {{
            color: #2c3e50;
            text-align: center;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        .info {{
            text-align: center;
            color: #7f8c8d;
            margin-bottom: 20px;
            font-size: 12px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
            font-size: 14px;
        }}
        th {{
            background-color: #3498db;
            color: white;
            padding: 10px;
            text-align: center;
            border: 1px solid #2980b9;
            font-weight: bold;
        }}
        td {{
            padding: 8px;
            text-align: center;
            border: 1px solid #ddd;
        }}
        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        tr:hover {{
            background-color: #f0f0f0;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            padding-top: 10px;
            border-top: 1px solid #ddd;
            color: #7f8c8d;
            font-size: 11px;
        }}
        @media print {{
            body {{ margin: 0; padding: 0; }}
            .container {{ box-shadow: none; padding: 0; }}
            th {{ background-color: #ddd; color: black; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h2>{escape(title)}</h2>
        <div class="info">
            Дата формирования: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}<br>
            Всего записей: {len(rows)}
        </div>
        <table>
            <thead>
                <tr>{header_html}</tr>
            </thead>
            <tbody>
                {''.join(row_html)}
            </tbody>
        </table>
    </div>
</body>
</html>
"""
        path.write_text(html, encoding="utf-8")
        return path

    def export_pdf(self, headers: list[str], rows: list[dict[str, str]], output_path: str, title: str) -> Path:
        path = Path(output_path)

        document = SimpleDocTemplate(
            str(path),
            pagesize=landscape(A4),
            rightMargin=10 * mm,
            leftMargin=10 * mm,
            topMargin=15 * mm,
            bottomMargin=15 * mm
        )

        styles = getSampleStyleSheet()
        custom_styles = self._get_styles(styles)

        elements = []

        title_para = Paragraph(title, custom_styles['Title'])
        elements.append(title_para)
        elements.append(Spacer(1, 5))

        date_para = Paragraph(
            f"Дата формирования: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}",
            custom_styles['Date']
        )
        elements.append(date_para)
        elements.append(Spacer(1, 10))

        table_data = [headers]

        for row in rows:
            formatted_row = []
            for header in headers:
                value = str(row.get(header, ""))
                if len(value) > 50:
                    value = value[:47] + "..."
                formatted_row.append(value)
            table_data.append(formatted_row)

        table = Table(table_data, repeatRows=1)

        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#3498db")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), self.font_name),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
            ('BOLD', (0, 0), (-1, 0), 1),
            ('FONTNAME', (0, 1), (-1, -1), self.font_name),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 1), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#bdc3c7")),
            ('PADDING', (0, 0), (-1, -1), 6),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.HexColor("#f9f9f9")]),
        ])

        table.setStyle(table_style)
        elements.append(table)

        elements.append(Spacer(1, 15))
        count_para = Paragraph(
            f"Всего записей: {len(rows)}",
            custom_styles['Date']
        )
        elements.append(count_para)
        document.build(elements)
        return path
