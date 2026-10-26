from collections.abc import Mapping
from typing import Any


# The item of a list answered by an API whose field has the value, such as the schema of one implementation.
def find(items: list[dict[str, Any]], field: str, value: object) -> dict[str, Any]:
    for item in items:
        if item[field] == value:
            return item
    raise OSError(f"no {field} {value}")


# The fields of an *arr schema, a list of {name, value}, with the given values set by name.
def with_values(fields: list[dict[str, Any]], values: Mapping[str, object]) -> list[dict[str, Any]]:
    return [{**field, "value": values[field["name"]]} if field["name"] in values else field for field in fields]
