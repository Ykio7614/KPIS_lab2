from __future__ import annotations

from PyQt6.QtWidgets import QDialog, QHeaderView, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout


class LogsDialog(QDialog):
    def __init__(self, repository, parent=None) -> None:
        super().__init__(parent)
        self.repository = repository
        self.setWindowTitle("Журнал изменений")
        self.resize(920, 480)

        layout = QVBoxLayout(self)
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.table)

        close_button = QPushButton("Закрыть")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)

        self.load_data()

    def load_data(self) -> None:
        rows = self.repository.get_logs()
        headers = ["changed_at", "action", "object_name", "field_name", "old_value", "new_value"]
        titles = ["Дата/время", "Действие", "Объект", "Поле", "Старое значение", "Новое значение"]

        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(titles)
        self.table.setRowCount(len(rows))

        for row_index, row in enumerate(rows):
            for column_index, header in enumerate(headers):
                self.table.setItem(row_index, column_index, QTableWidgetItem(row.get(header, "")))

