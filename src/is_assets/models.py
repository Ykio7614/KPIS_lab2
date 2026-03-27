from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class SearchCriterion:
    field: str
    value: str = ""
    date_from: str = ""
    date_to: str = ""

    def has_value(self) -> bool:
        return bool(self.value.strip() or self.date_from.strip() or self.date_to.strip())

