from __future__ import annotations

from typing import Callable

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCompleter,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class ParameterRow(QWidget):
    remove_requested = pyqtSignal(QWidget)

    def __init__(
        self,
        name_provider: Callable[[], list[str]],
        value_provider: Callable[[str | None], list[str]],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._name_provider = name_provider
        self._value_provider = value_provider

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Название параметра")
        self.value_edit = QLineEdit()
        self.value_edit.setPlaceholderText("Значение параметра")
        self.remove_button = QPushButton("Удалить строку")

        layout.addWidget(self.name_edit, 2)
        layout.addWidget(self.value_edit, 2)
        layout.addWidget(self.remove_button)

        self.remove_button.clicked.connect(lambda: self.remove_requested.emit(self))
        self.name_edit.textChanged.connect(self.refresh_completers)
        self.refresh_completers()

    def refresh_completers(self) -> None:
        name_completer = QCompleter(self._name_provider(), self)
        name_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.name_edit.setCompleter(name_completer)

        value_completer = QCompleter(self._value_provider(self.name_edit.text().strip() or None), self)
        value_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.value_edit.setCompleter(value_completer)

    def get_data(self) -> tuple[str, str]:
        return self.name_edit.text().strip(), self.value_edit.text().strip()

    def clear(self) -> None:
        self.name_edit.clear()
        self.value_edit.clear()


class InputTab(QWidget):
    data_changed = pyqtSignal()

    def __init__(self, repository, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.repository = repository
        self.parameter_rows: list[ParameterRow] = []

        root_layout = QVBoxLayout(self)
        root_layout.setSpacing(12)

        header = QLabel(
            "Создайте объект учета и добавьте произвольный набор параметров. "
            "Подсказки в полях формируются автоматически по уже сохраненным данным."
        )
        header.setWordWrap(True)
        root_layout.addWidget(header)

        form_layout = QFormLayout()
        self.object_name_edit = QLineEdit()
        self.object_name_edit.setPlaceholderText("Например: Отдел кадров")
        form_layout.addRow("Объект / подразделение", self.object_name_edit)
        root_layout.addLayout(form_layout)

        parameters_label = QLabel("Параметры объекта")
        parameters_label.setStyleSheet("font-weight: 600;")
        root_layout.addWidget(parameters_label)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.StyledPanel)
        self.parameters_container = QWidget()
        self.parameters_layout = QVBoxLayout(self.parameters_container)
        self.parameters_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_area.setWidget(self.parameters_container)
        root_layout.addWidget(self.scroll_area, 1)

        actions = QHBoxLayout()
        self.add_parameter_button = QPushButton("Добавить параметр")
        self.save_button = QPushButton("Сохранить объект")
        self.clear_button = QPushButton("Очистить форму")
        actions.addWidget(self.add_parameter_button)
        actions.addStretch(1)
        actions.addWidget(self.clear_button)
        actions.addWidget(self.save_button)
        self.skeleton_button = QPushButton("🦴 Загрузить скелет")
        self.skeleton_button.setToolTip("Загрузить предустановленные параметры")
        self.skeleton_button.clicked.connect(self.load_skeleton)
        actions.insertWidget(0, self.skeleton_button)
        root_layout.addLayout(actions)

        self.add_parameter_button.clicked.connect(self.add_parameter_row)
        self.clear_button.clicked.connect(self.reset_form)
        self.save_button.clicked.connect(self.save_object)

        self.refresh_autocomplete()
        self.add_parameter_row()

    def _object_completer(self) -> None:
        completer = QCompleter(self.repository.get_object_names(), self)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.object_name_edit.setCompleter(completer)

    def refresh_autocomplete(self) -> None:
        self._object_completer()
        for row in self.parameter_rows:
            row.refresh_completers()

    def add_parameter_row(self) -> None:
        row = ParameterRow(self.repository.get_parameter_names, self.repository.get_parameter_values, self)
        row.remove_requested.connect(self.remove_parameter_row)
        self.parameter_rows.append(row)
        self.parameters_layout.addWidget(row)
        row.refresh_completers()

    def remove_parameter_row(self, row: QWidget) -> None:
        if len(self.parameter_rows) == 1:
            QMessageBox.information(self, "Удаление недоступно", "Должна оставаться хотя бы одна строка параметра.")
            return
        self.parameter_rows.remove(row)
        row.setParent(None)
        row.deleteLater()

    def reset_form(self) -> None:
        self.object_name_edit.clear()
        while len(self.parameter_rows) > 1:
            row = self.parameter_rows.pop()
            row.setParent(None)
            row.deleteLater()
        self.parameter_rows[0].clear()
        self.refresh_autocomplete()

    def save_object(self) -> None:
        object_name = self.object_name_edit.text().strip()
        if not object_name:
            QMessageBox.warning(self, "Ошибка ввода", "Укажите название объекта.")
            return

        parameters: list[tuple[str, str]] = []
        seen_names: set[str] = set()
        for row in self.parameter_rows:
            name, value = row.get_data()
            if not name and not value:
                continue
            if not name or not value:
                QMessageBox.warning(self, "Ошибка ввода", "У каждого параметра должны быть заполнены название и значение.")
                return
            if name in seen_names:
                QMessageBox.warning(self, "Ошибка ввода", f"Параметр «{name}» указан несколько раз.")
                return
            seen_names.add(name)
            parameters.append((name, value))

        if not parameters:
            QMessageBox.warning(self, "Ошибка ввода", "Добавьте хотя бы один параметр.")
            return

        self.repository.create_object(object_name, parameters)
        self.reset_form()
        self.refresh_autocomplete()
        QMessageBox.information(self, "Сохранено", "Объект и его параметры сохранены в CSV.")
        self.data_changed.emit()

 def load_skeleton(self):
        """Загружает шаблон с предустановленными параметрами"""
        skeleton_parameters = [
            ("Тип устройства", ""),
            ("Имя устройства", ""),
            ("IP-адрес", ""),
            ("MAC-адрес", ""),
            ("Класс сетевой угрозы", ""),
            ("Количество событий", ""),
            ("Дата события", ""),
        ]

        for row in self.parameter_rows[:]:
            row.setParent(None)
            row.deleteLater()
        self.parameter_rows.clear()

        for param_name, default_value in skeleton_parameters:
            self.add_parameter_row()
            current_row = self.parameter_rows[-1]
            current_row.name_edit.setText(param_name)
            current_row.value_edit.setText(default_value)

        self.refresh_autocomplete()
        QMessageBox.information(
            self,
            "Скелет загружен",
            f"Загружено {len(skeleton_parameters)} предустановленных параметров.\n"
            "Вы можете изменять значения и добавлять новые параметры."
        )

