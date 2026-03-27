from __future__ import annotations

from collections import Counter, defaultdict

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PyQt6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..config import COUNT_FIELD


class VisualizationTab(QWidget):
    def __init__(self, repository, parent=None) -> None:
        super().__init__(parent)
        self.repository = repository
        self.figure = Figure(figsize=(8, 4), tight_layout=True)
        self.canvas = FigureCanvasQTAgg(self.figure)
        self._has_chart = False

        layout = QVBoxLayout(self)
        controls = QHBoxLayout()

        self.chart_type_combo = QComboBox()
        self.chart_type_combo.addItems(["Столбчатая диаграмма", "Линейный график", "Круговая диаграмма"])
        self.x_axis_combo = QComboBox()
        self.y_axis_combo = QComboBox()
        self.y_axis_combo.addItem(COUNT_FIELD)

        controls.addWidget(QLabel("Тип графика"))
        controls.addWidget(self.chart_type_combo)
        controls.addWidget(QLabel("Ось X"))
        controls.addWidget(self.x_axis_combo)
        controls.addWidget(QLabel("Ось Y"))
        controls.addWidget(self.y_axis_combo)
        layout.addLayout(controls)

        buttons = QHBoxLayout()
        self.build_button = QPushButton("Построить")
        self.reset_button = QPushButton("Построить заново")
        self.export_jpg_button = QPushButton("Выгрузить в JPG")
        self.export_jpeg_button = QPushButton("Выгрузить в JPEG")
        self.export_png_button = QPushButton("Выгрузить в PNG")
        self.export_pdf_button = QPushButton("Выгрузить в PDF")
        buttons.addWidget(self.build_button)
        buttons.addWidget(self.reset_button)
        buttons.addStretch(1)
        buttons.addWidget(self.export_jpg_button)
        buttons.addWidget(self.export_jpeg_button)
        buttons.addWidget(self.export_png_button)
        buttons.addWidget(self.export_pdf_button)
        layout.addLayout(buttons)
        layout.addWidget(self.canvas, 1)

        self.build_button.clicked.connect(self.build_chart)
        self.reset_button.clicked.connect(self.reset_chart)
        self.export_jpg_button.clicked.connect(lambda: self.export_chart("jpg"))
        self.export_jpeg_button.clicked.connect(lambda: self.export_chart("jpeg"))
        self.export_png_button.clicked.connect(lambda: self.export_chart("png"))
        self.export_pdf_button.clicked.connect(lambda: self.export_chart("pdf"))

        self.refresh_data()
        self._update_export_state()

    def refresh_data(self) -> None:
        fields = self.repository.get_display_fields()
        current_x = self.x_axis_combo.currentText()
        current_y = self.y_axis_combo.currentText()

        self.x_axis_combo.clear()
        self.x_axis_combo.addItems(fields)

        self.y_axis_combo.clear()
        self.y_axis_combo.addItem(COUNT_FIELD)
        self.y_axis_combo.addItems(fields)

        if current_x:
            index = self.x_axis_combo.findText(current_x)
            if index >= 0:
                self.x_axis_combo.setCurrentIndex(index)
        if current_y:
            index = self.y_axis_combo.findText(current_y)
            if index >= 0:
                self.y_axis_combo.setCurrentIndex(index)

    def _aggregate(self, x_field: str, y_field: str) -> tuple[list[str], list[float], str]:
        rows = self.repository.get_flat_records()
        rows = [row for row in rows if row.get(x_field, "").strip()]
        if not rows:
            return [], [], ""

        if y_field == COUNT_FIELD:
            counts = Counter(row[x_field] for row in rows)
            return list(counts.keys()), [float(value) for value in counts.values()], "Количество записей"

        if self.repository.is_numeric_field(y_field):
            aggregated: dict[str, float] = defaultdict(float)
            for row in rows:
                x_value = row.get(x_field, "").strip()
                y_value = row.get(y_field, "").strip()
                if not x_value or not y_value:
                    continue
                aggregated[x_value] += float(y_value.replace(",", "."))
            return list(aggregated.keys()), list(aggregated.values()), f"Сумма значений поля «{y_field}»"

        counts = Counter(row[x_field] for row in rows if row.get(y_field, "").strip())
        return list(counts.keys()), [float(value) for value in counts.values()], f"Частота непустых значений поля «{y_field}»"

    def build_chart(self) -> None:
        x_field = self.x_axis_combo.currentText()
        y_field = self.y_axis_combo.currentText()
        chart_type = self.chart_type_combo.currentText()

        x_values, y_values, description = self._aggregate(x_field, y_field)
        if not x_values:
            QMessageBox.information(self, "Визуализация", "Недостаточно данных для построения диаграммы.")
            return

        self.figure.clear()
        axis = self.figure.add_subplot(111)
        axis.grid(axis="y", alpha=0.25)

        if chart_type == "Столбчатая диаграмма":
            axis.bar(x_values, y_values, color="#3b82f6")
        elif chart_type == "Линейный график":
            axis.plot(x_values, y_values, marker="o", linewidth=2, color="#0f766e")
        else:
            axis.pie(y_values, labels=x_values, autopct="%1.1f%%", startangle=90)
            axis.axis("equal")

        axis.set_title(f"{chart_type}: {description}")
        if chart_type != "Круговая диаграмма":
            axis.set_xlabel(x_field)
            axis.set_ylabel(y_field)
            axis.tick_params(axis="x", rotation=20)

        self.canvas.draw()
        self._has_chart = True
        self._update_export_state()

    def reset_chart(self) -> None:
        self.figure.clear()
        self.canvas.draw()
        self._has_chart = False
        self._update_export_state()

    def _update_export_state(self) -> None:
        for button in [
            self.export_jpg_button,
            self.export_jpeg_button,
            self.export_png_button,
            self.export_pdf_button,
        ]:
            button.setEnabled(self._has_chart)

    def export_chart(self, extension: str) -> None:
        if not self._has_chart:
            QMessageBox.information(self, "Экспорт", "Сначала постройте диаграмму.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить диаграмму",
            f"chart.{extension}",
            f"{extension.upper()} files (*.{extension})",
        )
        if not path:
            return
        self.figure.savefig(path, dpi=200, bbox_inches="tight")
        QMessageBox.information(self, "Экспорт", "Диаграмма сохранена.")

