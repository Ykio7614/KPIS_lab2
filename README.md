# Система учета объектов информационной безопасности

Пример реализации по ТЗ на `Python + PyQt6` с четырьмя требуемыми частями:

- модуль ввода;
- модуль поиска/редактирования/удаления;
- модуль визуализации;
- CSV-хранилище данных.

Архитектура подробно описана в [docs/ARCHITECTURE.md](/Users/andrej/Documents/Учеба/kpis/lab2/KPIS_lab2/docs/ARCHITECTURE.md).

## Что реализовано

### 1. Модуль ввода

- GUI-форма создания объекта;
- динамическое добавление параметров;
- автоподсказки по объектам, названиям параметров и их значениям;
- сохранение данных в CSV.

### 2. Модуль поиска

- фильтрация через выпадающие списки;
- логика поиска `AND`;
- поддержка диапазона дат (`с` / `по`);
- чтение данных из CSV;
- результаты в таблице с прокруткой;
- редактирование и сохранение;
- удаление объекта или отдельного параметра;
- экспорт в `DOC`, `CSV`, `PDF`;
- просмотр журнала изменений.

### 3. Модуль визуализации

- чтение данных из CSV;
- выбор типа графика;
- выбор осей `X` и `Y`;
- построение диаграммы;
- экспорт в `JPG`, `JPEG`, `PNG`, `PDF`.

### 4. CSV-хранилище

При первом запуске рядом с приложением создается папка `data`:

- `data/objects.csv`
- `data/parameters.csv`
- `data/change_log.csv`

## Структура проекта

```text
src/main.py                     # точка входа
src/is_assets/repository.py     # CRUD и работа с CSV
src/is_assets/services/         # экспорт
src/is_assets/ui/               # вкладки интерфейса
docs/ARCHITECTURE.md            # описание архитектуры
requirements.txt                # зависимости
```

## Запуск из исходников

### 1. Установить зависимости

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Для Windows:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Запустить приложение

```bash
python3 src/main.py
```

## Сборка в исполняемый файл через PyInstaller

Приложение можно собрать так, чтобы у пользователя не была установлена IDE или Python.

### Установка сборщика

```bash
pip install pyinstaller
```

### Сборка для Windows

```powershell
pyinstaller --noconfirm --clean --windowed --name IBAssetRegistry src/main.py
```

Результат:

- `dist/IBAssetRegistry/IBAssetRegistry.exe`

После первого запуска рядом с `.exe` автоматически появится папка `data` с CSV-файлами.

### Сборка для Linux

```bash
pyinstaller --noconfirm --clean --windowed --name ib-asset-registry src/main.py
```

Результат:

- `dist/ib-asset-registry/ib-asset-registry`

### Сборка в один файл

Если нужен единый исполняемый файл:

```bash
pyinstaller --noconfirm --clean --onefile --windowed --name ib-asset-registry src/main.py
```

В этом режиме папка `data` все равно будет создаваться рядом с исполняемым файлом при запуске.

## Примечания по экспорту

- Кнопка `Выгрузить в DOC` создает файл с расширением `.doc` в HTML-совместимом формате, который корректно открывается в Microsoft Word и LibreOffice Writer.
- Кнопка `Выгрузить в PDF` для таблиц использует `reportlab`.
- Графики экспортируются напрямую из `matplotlib`.

## Как это соотносится с ТЗ

### Разделение на модули

- `Модуль ввода` -> вкладка `Модуль ввода`
- `Модуль поиска` -> вкладка `Модуль поиска`
- `Модуль визуализации` -> вкладка `Модуль визуализации`
- `Хранилище данных` -> слой `CsvRepository` + `data/*.csv`

### Разделение на слои

- `UI` -> `src/is_assets/ui`
- `Логика и CRUD` -> `src/is_assets/repository.py`
- `Экспорт` -> `src/is_assets/services/export_service.py`
- `Хранилище` -> CSV в папке `data`

## Возможные доработки

- добавить шаблоны отчетов `DOCX`;
- заменить CSV на SQLite с сохранением того же UI;
- добавить авторизацию пользователей;
- добавить импорт начальных данных из Excel/CSV.
