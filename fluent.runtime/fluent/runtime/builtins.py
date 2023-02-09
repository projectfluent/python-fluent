from typing import Any, Callable, Dict
from .types import FluentType, fluent_date, fluent_number

NUMBER = fluent_number
DATETIME = fluent_date


BUILTINS: Dict[str, Callable[[Any], FluentType]] = {
    'NUMBER': NUMBER,
    'DATETIME': DATETIME,
}
