from __future__ import annotations

import csv
from html import escape
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


class ExportService:
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
body {{ font-family: Arial, sans-serif; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ border: 1px solid #444; padding: 6px; text-align: left; }}
th {{ background: #d9e5f4; }}
</style>
</head>
<body>
<h2>{escape(title)}</h2>
<table>
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
        document = SimpleDocTemplate(str(path), pagesize=landscape(A4))
        styles = getSampleStyleSheet()
        elements = [Paragraph(title, styles["Title"]), Spacer(1, 12)]
        table_data = [headers]
        for row in rows:
            table_data.append([str(row.get(header, "")) for header in headers])

        table = Table(table_data, repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#335c81")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f7fafc")),
                ]
            )
        )
        elements.append(table)
        document.build(elements)
        return path

