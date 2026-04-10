from __future__ import annotations

import csv
from html import escape
from pathlib import Path

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
            font_path = Path(__file__).resolve().parents[3] / "fonts" / "DejaVuSans.ttf"
            if font_path.exists():
                pdfmetrics.registerFont(TTFont('DejaVuSans', str(font_path)))
                self.font_name = 'DejaVuSans'
                print(f"Font loaded: {font_path}")
            else:
                print(f"Warning: Font not found at {font_path}")
        except Exception as e:
            print(f"Warning: Could not register DejaVuSans font: {e}")

    def _get_styles(self, styles):
        return {
            'Title': ParagraphStyle(
                'CustomTitle',
                parent=styles['Title'],
                fontName=self.font_name,
                fontSize=16,
                alignment=0,
                spaceAfter=12,
            ),
            'Normal': ParagraphStyle(
                'CustomNormal',
                parent=styles['Normal'],
                fontName=self.font_name,
                fontSize=10,
            ),
        }

    def export_csv(self, headers: list[str], rows: list[dict[str, str]], output_path: str) -> Path:
        path = Path(output_path)
        with path.open("w", encoding="utf-8-sig", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=headers)
            writer.writeheader()
            writer.writerows([{header: row.get(header, "") for header in headers} for row in rows])
        return path

    def export_doc(self, headers: list[str], rows: list[dict[str, str]], output_path: str, title: str) -> Path:
        path = Path(output_path)
        header_html = "".join(f"<th>{escape(header)}</th>" for header in headers)
        row_html = []
        for row in rows:
            cells = "".join(f"<td>{escape(str(row.get(header, '')))}</td>" for header in headers)
            row_html.append(f"<tr>{cells}</tr>")
        html = f"""<html>
<head>
<meta charset="utf-8">
<title>{escape(title)}</title>
<style>
body {{ font-family: 'DejaVu Sans', Arial, sans-serif; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ border: 1px solid #444; padding: 6px; text-align: left; }}
th {{ background: #d9e5f4; }}
</style>
</head>
<body>
<h2>{escape(title)}</h2>
<tr>
<thead><tr>{header_html}</tr></thead>
<tbody>{''.join(row_html)}</tbody>
</table>
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

        # Заголовок
        title_para = Paragraph(title, custom_styles['Title'])
        elements.append(title_para)
        elements.append(Spacer(1, 10))

        # Подготовка данных таблицы
        table_data = [headers]
        for row in rows:
            table_data.append([str(row.get(header, "")) for header in headers])

        table = Table(table_data, repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#335c81")),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('FONTNAME', (0, 0), (-1, 0), self.font_name),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#f7fafc")),
                    ('FONTNAME', (0, 1), (-1, -1), self.font_name),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                ]
            )
        )

        elements.append(table)

        from datetime import datetime
        elements.append(Spacer(1, 20))
        date_info = Paragraph(
            f"Дата экспорта: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}",
            custom_styles['Normal']
        )
        elements.append(date_info)

        document.build(elements)
        return path
