from typing import Callable

from .types import FluentType, fluent_date, fluent_number

NUMBER = fluent_number
DATETIME = fluent_date


BUILTINS: dict[str, Callable[..., FluentType]] = {
    "NUMBER": NUMBER,
    "DATETIME": DATETIME,
}
