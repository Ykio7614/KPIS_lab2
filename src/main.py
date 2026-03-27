from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication

from is_assets.config import APP_TITLE, DEFAULT_DATA_DIR
from is_assets.repository import CsvRepository
from is_assets.services.export_service import ExportService
from is_assets.ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_TITLE)

    repository = CsvRepository(DEFAULT_DATA_DIR)
    export_service = ExportService()
    window = MainWindow(repository, export_service)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
