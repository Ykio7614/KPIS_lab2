from __future__ import annotations

from PyQt6.QtWidgets import QMainWindow, QTabWidget

from ..config import APP_TITLE
from .input_tab import InputTab
from .search_tab import SearchTab
from .visualization_tab import VisualizationTab


class MainWindow(QMainWindow):
    def __init__(self, repository, export_service, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(APP_TITLE)
        self.resize(1320, 820)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.input_tab = InputTab(repository, self)
        self.search_tab = SearchTab(repository, export_service, self)
        self.visualization_tab = VisualizationTab(repository, self)

        self.tabs.addTab(self.input_tab, "Модуль ввода")
        self.tabs.addTab(self.search_tab, "Модуль поиска")
        self.tabs.addTab(self.visualization_tab, "Модуль визуализации")

        self.input_tab.data_changed.connect(self.refresh_dependent_tabs)
        self.search_tab.data_changed.connect(self.refresh_dependent_tabs)

    def refresh_dependent_tabs(self) -> None:
        self.input_tab.refresh_autocomplete()
        self.search_tab.refresh_data()
        self.visualization_tab.refresh_data()

