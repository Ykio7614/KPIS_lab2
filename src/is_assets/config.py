from __future__ import annotations

import sys
from pathlib import Path

APP_TITLE = "Система учета объектов ИБ"
DATE_FORMATS = ("%d.%m.%Y", "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y")
TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"
ALL_VALUES_TOKEN = "Все"
OBJECT_FIELD = "Объект"
COUNT_FIELD = "Количество записей"

DEFAULT_PARAMETER_NAMES = [
    "Тип устройства",
    "Имя устройства",
    "IP",
    "MAC",
    "Класс сетевой угрозы",
    "Количество событий",
    "Дата события",
]

DATE_FIELD_ALIASES = {
    "Дата события",
    "Дата",
}

NUMERIC_FIELD_ALIASES = {
    "Количество событий",
}


def resolve_data_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "data"
    return Path(__file__).resolve().parents[2] / "data"


DEFAULT_DATA_DIR = resolve_data_dir()
