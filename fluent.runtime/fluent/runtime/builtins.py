from typing import Any, Callable, Dict
from typing_extensions import Final

from .types import FluentType, fluent_date, fluent_number

NUMBER: Final = fluent_number
DATETIME: Final = fluent_date


BUILTINS: Dict[str, Callable[[Any], FluentType]] = {
    'NUMBER': NUMBER,
    'DATETIME': DATETIME,
}
