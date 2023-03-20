from datetime import date, datetime
from decimal import Decimal
from typing import Any, TypeVar, Union, overload
from typing_extensions import Final

from fluent.syntax.ast import MessageReference, TermReference

from .errors import FluentReferenceError
from .types import FluentDate, FluentDateTime, FluentDecimal, FluentFloat, FluentInt

TERM_SIGIL: Final = '-'
ATTRIBUTE_SEPARATOR: Final = '.'


_T = TypeVar('_T')


@overload
def native_to_fluent(val: int) -> FluentInt:  # type: ignore[misc]
    ...


@overload
def native_to_fluent(val: float) -> FluentFloat:  # type: ignore[misc]
    ...


@overload
def native_to_fluent(val: Decimal) -> FluentDecimal:  # type: ignore[misc]
    ...


@overload
def native_to_fluent(val: datetime) -> FluentDateTime:  # type: ignore[misc]
    ...


@overload
def native_to_fluent(val: date) -> FluentDate:  # type: ignore[misc]
    ...


@overload
def native_to_fluent(val: _T) -> _T:
    ...


def native_to_fluent(val: Any) -> Any:
    """
    Convert a python type to a Fluent Type.
    """
    if isinstance(val, int):
        return FluentInt(val)
    if isinstance(val, float):
        return FluentFloat(val)
    if isinstance(val, Decimal):
        return FluentDecimal(val)

    if isinstance(val, datetime):
        return FluentDateTime.from_date_time(val)
    if isinstance(val, date):
        return FluentDate.from_date(val)
    return val


def reference_to_id(ref: Union[MessageReference, TermReference]) -> str:
    """
    Returns a string reference for a MessageReference or TermReference
    AST node.

    e.g.
       message
       message.attr
       -term
       -term.attr
    """
    start: str
    if isinstance(ref, TermReference):
        start = TERM_SIGIL + ref.id.name
    else:
        start = ref.id.name

    if ref.attribute:
        return ''.join([start, ATTRIBUTE_SEPARATOR, ref.attribute.name])
    return start


def unknown_reference_error_obj(ref_id: str) -> FluentReferenceError:
    if ATTRIBUTE_SEPARATOR in ref_id:
        return FluentReferenceError(f"Unknown attribute: {ref_id}")
    if ref_id.startswith(TERM_SIGIL):
        return FluentReferenceError(f"Unknown term: {ref_id}")
    return FluentReferenceError(f"Unknown message: {ref_id}")
