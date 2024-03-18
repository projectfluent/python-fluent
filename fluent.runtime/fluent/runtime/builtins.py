from typing import Any, Callable

from .types import FluentType, fluent_date, fluent_number

NUMBER = fluent_number
DATETIME = fluent_date


BUILTINS: dict[str, Callable[[Any], FluentType]] = {
    "NUMBER": NUMBER,
    "DATETIME": DATETIME,
}
