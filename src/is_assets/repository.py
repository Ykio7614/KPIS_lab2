from __future__ import annotations

import csv
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Iterable

from .config import (
    ALL_VALUES_TOKEN,
    DATE_FIELD_ALIASES,
    DATE_FORMATS,
    DEFAULT_PARAMETER_NAMES,
    NUMERIC_FIELD_ALIASES,
    OBJECT_FIELD,
    TIMESTAMP_FORMAT,
)
from .models import SearchCriterion


INTERNAL_ID_FIELD = "__object_id"


class CsvRepository:
    def __init__(self, data_dir: Path) -> None:
        self.data_dir = Path(data_dir)
        self.objects_path = self.data_dir / "objects.csv"
        self.parameters_path = self.data_dir / "parameters.csv"
        self.logs_path = self.data_dir / "change_log.csv"
        self._ensure_storage()

    def _ensure_storage(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        layout = {
            self.objects_path: ["object_id", "object_name", "created_at", "updated_at"],
            self.parameters_path: ["parameter_id", "object_id", "parameter_name", "parameter_value"],
            self.logs_path: [
                "log_id",
                "object_id",
                "object_name",
                "field_name",
                "old_value",
                "new_value",
                "action",
                "changed_at",
            ],
        }
        for path, headers in layout.items():
            if path.exists():
                continue
            with path.open("w", encoding="utf-8-sig", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=headers)
                writer.writeheader()

    def _read_rows(self, path: Path) -> list[dict[str, str]]:
        with path.open("r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)
            return [dict(row) for row in reader]

    def _write_rows(self, path: Path, rows: Iterable[dict[str, str]], headers: list[str]) -> None:
        with path.open("w", encoding="utf-8-sig", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=headers)
            writer.writeheader()
            writer.writerows(rows)

    def _timestamp(self) -> str:
        return datetime.now().strftime(TIMESTAMP_FORMAT)

    def _next_id(self, rows: list[dict[str, str]], key: str) -> int:
        current = [int(row[key]) for row in rows if row.get(key, "").isdigit()]
        return max(current, default=0) + 1

    def _parse_date(self, value: str) -> datetime | None:
        cleaned = value.strip()
        if not cleaned:
            return None
        for fmt in DATE_FORMATS:
            try:
                return datetime.strptime(cleaned, fmt)
            except ValueError:
                continue
        return None

    def is_date_field(self, field_name: str) -> bool:
        if field_name in DATE_FIELD_ALIASES:
            return True
        rows = self.get_flat_records()
        date_values = [self._parse_date(row.get(field_name, "")) for row in rows if row.get(field_name, "").strip()]
        return bool(date_values) and all(value is not None for value in date_values)

    def is_numeric_field(self, field_name: str) -> bool:
        if field_name in NUMERIC_FIELD_ALIASES:
            return True
        rows = self.get_flat_records()
        numeric_values = [row.get(field_name, "").strip() for row in rows if row.get(field_name, "").strip()]
        if not numeric_values:
            return False
        try:
            for value in numeric_values:
                float(value.replace(",", "."))
        except ValueError:
            return False
        return True

    def get_parameter_names(self) -> list[str]:
        params = self._read_rows(self.parameters_path)
        names = {row["parameter_name"] for row in params if row["parameter_name"].strip()}
        names.update(DEFAULT_PARAMETER_NAMES)
        return sorted(names)

    def get_object_names(self) -> list[str]:
        objects = self._read_rows(self.objects_path)
        return sorted({row["object_name"] for row in objects if row["object_name"].strip()})

    def get_parameter_values(self, parameter_name: str | None = None) -> list[str]:
        params = self._read_rows(self.parameters_path)
        values = []
        for row in params:
            if parameter_name and row["parameter_name"] != parameter_name:
                continue
            value = row["parameter_value"].strip()
            if value:
                values.append(value)
        return sorted(set(values))

    def create_object(self, object_name: str, parameters: list[tuple[str, str]]) -> int:
        timestamp = self._timestamp()
        objects = self._read_rows(self.objects_path)
        params = self._read_rows(self.parameters_path)
        logs = self._read_rows(self.logs_path)

        object_id = self._next_id(objects, "object_id")
        objects.append(
            {
                "object_id": str(object_id),
                "object_name": object_name.strip(),
                "created_at": timestamp,
                "updated_at": timestamp,
            }
        )

        next_parameter_id = self._next_id(params, "parameter_id")
        next_log_id = self._next_id(logs, "log_id")

        for name, value in parameters:
            params.append(
                {
                    "parameter_id": str(next_parameter_id),
                    "object_id": str(object_id),
                    "parameter_name": name.strip(),
                    "parameter_value": value.strip(),
                }
            )
            logs.append(
                {
                    "log_id": str(next_log_id),
                    "object_id": str(object_id),
                    "object_name": object_name.strip(),
                    "field_name": name.strip(),
                    "old_value": "",
                    "new_value": value.strip(),
                    "action": "create",
                    "changed_at": timestamp,
                }
            )
            next_parameter_id += 1
            next_log_id += 1

        self._write_rows(self.objects_path, objects, ["object_id", "object_name", "created_at", "updated_at"])
        self._write_rows(
            self.parameters_path,
            params,
            ["parameter_id", "object_id", "parameter_name", "parameter_value"],
        )
        self._write_rows(
            self.logs_path,
            logs,
            ["log_id", "object_id", "object_name", "field_name", "old_value", "new_value", "action", "changed_at"],
        )
        return object_id

    def get_flat_records(self) -> list[dict[str, str]]:
        objects = self._read_rows(self.objects_path)
        params = self._read_rows(self.parameters_path)
        parameter_names = self.get_parameter_names()

        params_by_object: dict[str, dict[str, str]] = defaultdict(dict)
        for row in params:
            params_by_object[row["object_id"]][row["parameter_name"]] = row["parameter_value"]

        records: list[dict[str, str]] = []
        for obj in objects:
            record = {INTERNAL_ID_FIELD: obj["object_id"], OBJECT_FIELD: obj["object_name"]}
            for parameter_name in parameter_names:
                record[parameter_name] = params_by_object.get(obj["object_id"], {}).get(parameter_name, "")
            records.append(record)
        return records

    def get_display_fields(self) -> list[str]:
        return [OBJECT_FIELD, *self.get_parameter_names()]

    def get_filter_options(self) -> dict[str, list[str]]:
        rows = self.get_flat_records()
        options: dict[str, list[str]] = {}
        for field in self.get_display_fields():
            values = sorted({row.get(field, "").strip() for row in rows if row.get(field, "").strip()})
            options[field] = [ALL_VALUES_TOKEN, *values]
        return options

    def search_records(self, criteria: list[SearchCriterion]) -> list[dict[str, str]]:
        rows = self.get_flat_records()
        result: list[dict[str, str]] = []

        for row in rows:
            matches = True
            for criterion in criteria:
                if not criterion.field:
                    continue
                field_value = row.get(criterion.field, "").strip()
                if self.is_date_field(criterion.field):
                    row_date = self._parse_date(field_value)
                    from_date = self._parse_date(criterion.date_from)
                    to_date = self._parse_date(criterion.date_to)
                    if (criterion.date_from or criterion.date_to) and row_date is None:
                        matches = False
                        break
                    if from_date and row_date and row_date < from_date:
                        matches = False
                        break
                    if to_date and row_date and row_date > to_date:
                        matches = False
                        break
                    if criterion.value and criterion.value != ALL_VALUES_TOKEN and field_value != criterion.value:
                        matches = False
                        break
                else:
                    if criterion.value and criterion.value != ALL_VALUES_TOKEN and field_value != criterion.value:
                        matches = False
                        break
            if matches:
                result.append(row)
        return result

    def update_object(self, object_id: str, values: dict[str, str]) -> None:
        timestamp = self._timestamp()
        objects = self._read_rows(self.objects_path)
        params = self._read_rows(self.parameters_path)
        logs = self._read_rows(self.logs_path)

        target_object = next((row for row in objects if row["object_id"] == object_id), None)
        if target_object is None:
            raise ValueError(f"Объект с id={object_id} не найден")

        next_parameter_id = self._next_id(params, "parameter_id")
        next_log_id = self._next_id(logs, "log_id")

        new_object_name = values.get(OBJECT_FIELD, "").strip()
        if new_object_name and new_object_name != target_object["object_name"]:
            logs.append(
                {
                    "log_id": str(next_log_id),
                    "object_id": object_id,
                    "object_name": new_object_name,
                    "field_name": OBJECT_FIELD,
                    "old_value": target_object["object_name"],
                    "new_value": new_object_name,
                    "action": "update",
                    "changed_at": timestamp,
                }
            )
            next_log_id += 1
            target_object["object_name"] = new_object_name

        current_params = {row["parameter_name"]: row for row in params if row["object_id"] == object_id}
        for field_name in self.get_parameter_names():
            new_value = values.get(field_name, "").strip()
            current_row = current_params.get(field_name)
            old_value = current_row["parameter_value"].strip() if current_row else ""

            if new_value == old_value:
                continue
            if current_row and not new_value:
                params.remove(current_row)
                action = "delete"
            elif current_row:
                current_row["parameter_value"] = new_value
                action = "update"
            elif new_value:
                params.append(
                    {
                        "parameter_id": str(next_parameter_id),
                        "object_id": object_id,
                        "parameter_name": field_name,
                        "parameter_value": new_value,
                    }
                )
                next_parameter_id += 1
                action = "create"
            else:
                continue

            logs.append(
                {
                    "log_id": str(next_log_id),
                    "object_id": object_id,
                    "object_name": target_object["object_name"],
                    "field_name": field_name,
                    "old_value": old_value,
                    "new_value": new_value,
                    "action": action,
                    "changed_at": timestamp,
                }
            )
            next_log_id += 1

        target_object["updated_at"] = timestamp
        self._write_rows(self.objects_path, objects, ["object_id", "object_name", "created_at", "updated_at"])
        self._write_rows(
            self.parameters_path,
            params,
            ["parameter_id", "object_id", "parameter_name", "parameter_value"],
        )
        self._write_rows(
            self.logs_path,
            logs,
            ["log_id", "object_id", "object_name", "field_name", "old_value", "new_value", "action", "changed_at"],
        )

    def delete_objects(self, object_ids: Iterable[str]) -> None:
        ids = {str(item) for item in object_ids}
        if not ids:
            return

        timestamp = self._timestamp()
        objects = self._read_rows(self.objects_path)
        params = self._read_rows(self.parameters_path)
        logs = self._read_rows(self.logs_path)
        next_log_id = self._next_id(logs, "log_id")

        removed_objects = [row for row in objects if row["object_id"] in ids]
        objects = [row for row in objects if row["object_id"] not in ids]
        params = [row for row in params if row["object_id"] not in ids]

        for row in removed_objects:
            logs.append(
                {
                    "log_id": str(next_log_id),
                    "object_id": row["object_id"],
                    "object_name": row["object_name"],
                    "field_name": "*",
                    "old_value": row["object_name"],
                    "new_value": "",
                    "action": "delete_object",
                    "changed_at": timestamp,
                }
            )
            next_log_id += 1

        self._write_rows(self.objects_path, objects, ["object_id", "object_name", "created_at", "updated_at"])
        self._write_rows(
            self.parameters_path,
            params,
            ["parameter_id", "object_id", "parameter_name", "parameter_value"],
        )
        self._write_rows(
            self.logs_path,
            logs,
            ["log_id", "object_id", "object_name", "field_name", "old_value", "new_value", "action", "changed_at"],
        )

    def delete_parameter_for_objects(self, field_name: str, object_ids: Iterable[str]) -> int:
        ids = {str(item) for item in object_ids}
        if field_name == OBJECT_FIELD:
            return 0

        timestamp = self._timestamp()
        object_rows = self._read_rows(self.objects_path)
        objects = {row["object_id"]: row for row in object_rows}
        params = self._read_rows(self.parameters_path)
        logs = self._read_rows(self.logs_path)
        next_log_id = self._next_id(logs, "log_id")

        kept_params: list[dict[str, str]] = []
        removed_count = 0
        for row in params:
            if row["object_id"] in ids and row["parameter_name"] == field_name:
                removed_count += 1
                logs.append(
                    {
                        "log_id": str(next_log_id),
                        "object_id": row["object_id"],
                        "object_name": objects.get(row["object_id"], {}).get("object_name", ""),
                        "field_name": field_name,
                        "old_value": row["parameter_value"],
                        "new_value": "",
                        "action": "delete_parameter",
                        "changed_at": timestamp,
                    }
                )
                next_log_id += 1
                continue
            kept_params.append(row)

        if removed_count:
            for object_id in ids:
                if object_id in objects:
                    objects[object_id]["updated_at"] = timestamp

        self._write_rows(self.objects_path, object_rows, ["object_id", "object_name", "created_at", "updated_at"])
        self._write_rows(
            self.parameters_path,
            kept_params,
            ["parameter_id", "object_id", "parameter_name", "parameter_value"],
        )
        self._write_rows(
            self.logs_path,
            logs,
            ["log_id", "object_id", "object_name", "field_name", "old_value", "new_value", "action", "changed_at"],
        )
        return removed_count

    def get_logs(self) -> list[dict[str, str]]:
        logs = self._read_rows(self.logs_path)
        return sorted(logs, key=lambda row: row["changed_at"], reverse=True)
