from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..config import ALL_VALUES_TOKEN, OBJECT_FIELD
from ..models import SearchCriterion
from ..repository import INTERNAL_ID_FIELD
from .logs_dialog import LogsDialog


class SearchConditionRow(QWidget):
    remove_requested = pyqtSignal(QWidget)

    def __init__(self, repository, parent=None) -> None:
        super().__init__(parent)
        self.repository = repository

        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.field_combo = QComboBox()
        self.value_combo = QComboBox()
        self.from_edit = QLineEdit()
        self.to_edit = QLineEdit()
        self.remove_button = QPushButton("Убрать")

        self.from_edit.setPlaceholderText("с")
        self.to_edit.setPlaceholderText("по")

        layout.addWidget(QLabel("Поле"), 0, 0)
        layout.addWidget(self.field_combo, 0, 1)
        layout.addWidget(QLabel("Значение"), 0, 2)
        layout.addWidget(self.value_combo, 0, 3)
        layout.addWidget(QLabel("Диапазон дат"), 0, 4)
        layout.addWidget(self.from_edit, 0, 5)
        layout.addWidget(self.to_edit, 0, 6)
        layout.addWidget(self.remove_button, 0, 7)

        self.field_combo.currentTextChanged.connect(self.refresh_values)
        self.remove_button.clicked.connect(lambda: self.remove_requested.emit(self))
        self.reload_fields()

    def reload_fields(self) -> None:
        current_field = self.field_combo.currentText()
        self.field_combo.blockSignals(True)
        self.field_combo.clear()
        self.field_combo.addItems(self.repository.get_display_fields())
        self.field_combo.blockSignals(False)
        if current_field:
            index = self.field_combo.findText(current_field)
            if index >= 0:
                self.field_combo.setCurrentIndex(index)
        self.refresh_values()

    def refresh_values(self) -> None:
        field_name = self.field_combo.currentText()
        options = self.repository.get_filter_options().get(field_name, [ALL_VALUES_TOKEN])
        current_value = self.value_combo.currentText()
        self.value_combo.clear()
        self.value_combo.addItems(options)
        if current_value:
            index = self.value_combo.findText(current_value)
            if index >= 0:
                self.value_combo.setCurrentIndex(index)

        is_date = self.repository.is_date_field(field_name)
        self.from_edit.setVisible(is_date)
        self.to_edit.setVisible(is_date)

    def criterion(self) -> SearchCriterion:
        return SearchCriterion(
            field=self.field_combo.currentText(),
            value=self.value_combo.currentText(),
            date_from=self.from_edit.text().strip(),
            date_to=self.to_edit.text().strip(),
        )

    def reset(self) -> None:
        self.value_combo.setCurrentIndex(0)
        self.from_edit.clear()
        self.to_edit.clear()


class SearchTab(QWidget):
    data_changed = pyqtSignal()
    COLUMN_ORDER = ["Объект", "Тип устройства", "Имя устройства", "IP-адрес",
                    "MAC-адрес", "Класс сетевой угрозы", "Количество событий", "Дата события"]

    def __init__(self, repository, export_service, parent=None) -> None:
        super().__init__(parent)
        self.repository = repository
        self.export_service = export_service
        self.filter_rows: list[SearchConditionRow] = []
        self.current_records: list[dict[str, str]] = []
        self.display_fields = self.repository.get_display_fields()
        self.edit_mode = False
        self._export_headers: list[str] = []

        root = QVBoxLayout(self)

        hint = QLabel(
            "Поиск работает по логике AND. Для удаления объектов выделите строки или несколько столбцов, "
            "а для удаления одного параметра выделите ячейки только в нужном столбце."
        )
        hint.setWordWrap(True)
        root.addWidget(hint)

        self.filters_layout = QVBoxLayout()
        root.addLayout(self.filters_layout)

        filter_actions = QHBoxLayout()
        self.add_filter_button = QPushButton("Добавить фильтр")
        self.show_button = QPushButton("Показать")
        self.reset_button = QPushButton("Сброс поиска")
        self.logs_button = QPushButton("Журнал изменений")
        filter_actions.addWidget(self.add_filter_button)
        filter_actions.addWidget(self.show_button)
        filter_actions.addWidget(self.reset_button)
        filter_actions.addStretch(1)
        filter_actions.addWidget(self.logs_button)
        root.addLayout(filter_actions)

        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectItems)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setStretchLastSection(True)
        root.addWidget(self.table, 1)

        row_actions = QHBoxLayout()
        self.edit_button = QPushButton("Редактировать")
        self.delete_button = QPushButton("Удалить")
        self.export_doc_button = QPushButton("Выгрузить в DOC")
        self.export_csv_button = QPushButton("Выгрузить в CSV")
        self.export_pdf_button = QPushButton("Выгрузить в PDF")
        row_actions.addWidget(self.edit_button)
        row_actions.addWidget(self.delete_button)
        row_actions.addStretch(1)
        row_actions.addWidget(self.export_doc_button)
        row_actions.addWidget(self.export_csv_button)
        row_actions.addWidget(self.export_pdf_button)
        root.addLayout(row_actions)

        edit_actions = QHBoxLayout()
        self.cancel_button = QPushButton("Отменить")
        self.save_button = QPushButton("Сохранить")
        edit_actions.addStretch(1)
        edit_actions.addWidget(self.cancel_button)
        edit_actions.addWidget(self.save_button)
        root.addLayout(edit_actions)

        self.cancel_button.hide()
        self.save_button.hide()

        self.add_filter_button.clicked.connect(self.add_filter_row)
        self.show_button.clicked.connect(self.perform_search)
        self.reset_button.clicked.connect(self.reset_filters)
        self.logs_button.clicked.connect(self.show_logs)
        self.edit_button.clicked.connect(self.enter_edit_mode)
        self.cancel_button.clicked.connect(self.cancel_edit_mode)
        self.save_button.clicked.connect(self.save_changes)
        self.delete_button.clicked.connect(self.delete_selected)
        self.export_csv_button.clicked.connect(lambda: self.export_results("csv"))
        self.export_doc_button.clicked.connect(lambda: self.export_results("doc"))
        self.export_pdf_button.clicked.connect(lambda: self.export_results("pdf"))

        self.add_filter_row()
        self.perform_search()

    def add_filter_row(self) -> None:
        row = SearchConditionRow(self.repository, self)
        row.remove_requested.connect(self.remove_filter_row)
        self.filter_rows.append(row)
        self.filters_layout.addWidget(row)

    def remove_filter_row(self, row: QWidget) -> None:
        if len(self.filter_rows) == 1:
            QMessageBox.information(self, "Фильтр", "Должен оставаться хотя бы один фильтр.")
            return
        self.filter_rows.remove(row)
        row.setParent(None)
        row.deleteLater()

    def refresh_data(self) -> None:
        self.display_fields = self.repository.get_display_fields()
        for row in self.filter_rows:
            row.reload_fields()
        self.perform_search()

    def reset_filters(self) -> None:
        while len(self.filter_rows) > 1:
            row = self.filter_rows.pop()
            row.setParent(None)
            row.deleteLater()
        self.filter_rows[0].reload_fields()
        self.filter_rows[0].reset()
        self.perform_search()

    def collect_criteria(self) -> list[SearchCriterion]:
        criteria: list[SearchCriterion] = []
        for row in self.filter_rows:
            criterion = row.criterion()
            if criterion.has_value() or row.field_combo.currentText():
                criteria.append(criterion)
        return criteria

    def perform_search(self) -> None:
        self.current_records = self.repository.search_records(self.collect_criteria())
        self.populate_table(self.current_records)
        self.exit_edit_mode()

    def populate_table(self, records: list[dict[str, str]]) -> None:
        self.table.clear()
        self.table.setRowCount(len(records))
        self.table.setColumnCount(len(self.display_fields))
        self.table.setHorizontalHeaderLabels(self.display_fields)

        for row_index, record in enumerate(records):
            for column_index, field_name in enumerate(self.display_fields):
                item = QTableWidgetItem(record.get(field_name, ""))
                item.setData(Qt.ItemDataRole.UserRole, record.get(INTERNAL_ID_FIELD, ""))
                self.table.setItem(row_index, column_index, item)

    def enter_edit_mode(self) -> None:
        if not self.current_records:
            QMessageBox.information(self, "Редактирование", "Нет данных для редактирования.")
            return
        self.edit_mode = True
        self.table.setEditTriggers(
            QTableWidget.EditTrigger.DoubleClicked
            | QTableWidget.EditTrigger.SelectedClicked
            | QTableWidget.EditTrigger.EditKeyPressed
        )
        self.cancel_button.show()
        self.save_button.show()

    def exit_edit_mode(self) -> None:
        self.edit_mode = False
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.cancel_button.hide()
        self.save_button.hide()

    def cancel_edit_mode(self) -> None:
        self.populate_table(self.current_records)
        self.exit_edit_mode()

    def _row_state(self, row_index: int) -> tuple[str, dict[str, str]]:
        object_id = self.table.item(row_index, 0).data(Qt.ItemDataRole.UserRole)
        values = {}
        for column_index, field_name in enumerate(self.display_fields):
            item = self.table.item(row_index, column_index)
            values[field_name] = item.text().strip() if item else ""
        return str(object_id), values

    def save_changes(self) -> None:
        if not self.edit_mode:
            return
        answer = QMessageBox.question(
            self,
            "Сохранить изменения",
            "Сохранить изменения в CSV?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        for row_index in range(self.table.rowCount()):
            object_id, values = self._row_state(row_index)
            if not values.get(OBJECT_FIELD):
                QMessageBox.warning(self, "Ошибка", "Поле «Объект» не может быть пустым.")
                return
            self.repository.update_object(object_id, values)

        self.refresh_data()
        QMessageBox.information(self, "Сохранено", "Изменения сохранены.")
        self.data_changed.emit()

    def _selected_row_ids(self) -> list[str]:
        rows: set[int] = {index.row() for index in self.table.selectedIndexes()}
        ids = []
        for row in rows:
            item = self.table.item(row, 0)
            if item is not None:
                ids.append(str(item.data(Qt.ItemDataRole.UserRole)))
        return ids

    def _selected_headers(self) -> list[str]:
        columns = sorted({index.column() for index in self.table.selectedIndexes()})
        return [self.display_fields[column] for column in columns]

    def delete_selected(self) -> None:
        object_ids = self._selected_row_ids()
        selected_headers = self._selected_headers()

        if not object_ids:
            QMessageBox.information(self, "Удаление", "Выделите данные в таблице.")
            return

        if len(selected_headers) == 1 and selected_headers[0] != OBJECT_FIELD:
            header = selected_headers[0]
            answer = QMessageBox.question(
                self,
                "Удаление параметра",
                f"Удалить параметр «{header}» у выделенных объектов?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
            removed = self.repository.delete_parameter_for_objects(header, object_ids)
            QMessageBox.information(self, "Удаление", f"Удалено значений параметра: {removed}.")
        else:
            answer = QMessageBox.question(
                self,
                "Удаление объекта",
                "Удалить выделенные объекты целиком?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
            self.repository.delete_objects(object_ids)
            QMessageBox.information(self, "Удаление", f"Удалено объектов: {len(set(object_ids))}.")

        self.refresh_data()
        self.data_changed.emit()

    def _get_ordered_headers(self) -> list[str]:
        ordered = [field for field in self.COLUMN_ORDER if field in self.display_fields]
        for field in self.display_fields:
            if field not in ordered:
                ordered.append(field)
        return ordered

    def _rows_for_export(self) -> list[dict[str, str]]:
        """Подготовка данных для экспорта с правильным порядком колонок"""
        ordered_fields = self._get_ordered_headers()
        self._export_headers = ordered_fields

        rows = []
        for record in self.current_records:
            row = {}
            for field in ordered_fields:
                row[field] = record.get(field, "")
            rows.append(row)
        return rows

    def export_results(self, export_type: str) -> None:
        """Экспорт результатов поиска в файл"""
        if not self.current_records:
            QMessageBox.information(self, "Экспорт", "Нет данных для выгрузки.")
            return

        filters = {
            "csv": ("CSV files (*.csv)", "results.csv"),
            "doc": ("DOC files (*.doc)", "results.doc"),
            "pdf": ("PDF files (*.pdf)", "results.pdf"),
        }
        file_filter, default_name = filters[export_type]
        path, _ = QFileDialog.getSaveFileName(self, "Сохранить файл", default_name, file_filter)
        if not path:
            return

        rows = self._rows_for_export()
        headers = getattr(self, '_export_headers', list(self.display_fields))
        title = "Результаты поиска объектов информационной безопасности"

        try:
            if export_type == "csv":
                self.export_service.export_csv(headers, rows, path)
            elif export_type == "doc":
                self.export_service.export_doc(headers, rows, path, title)
            else:  # pdf
                self.export_service.export_pdf(headers, rows, path, title)
            QMessageBox.information(self, "Экспорт", f"Файл успешно сохранён: {path}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить файл: {e}")

    def show_logs(self) -> None:
        dialog = LogsDialog(self.repository, self)
        dialog.exec()
