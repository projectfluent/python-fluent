from __future__ import absolute_import, unicode_literals

from datetime import date, datetime
from decimal import Decimal

from fluent.syntax.ast import Term, TermReference

from .types import FluentInt, FluentFloat, FluentDecimal, FluentDate, FluentDateTime
from .errors import FluentReferenceError

TERM_SIGIL = '-'
ATTRIBUTE_SEPARATOR = '.'


def ast_to_id(ast):
    """
    Returns a string reference for a Term or Message
    """
    if isinstance(ast, Term):
        return TERM_SIGIL + ast.id.name
    return ast.id.name


def native_to_fluent(val):
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


def reference_to_id(ref, ignore_attributes=False):
    """
    Returns a string reference for a MessageReference or TermReference
    AST node.

    e.g.
       message
       message.attr
       -term
       -term.attr
    """
    if isinstance(ref, TermReference):
        start = TERM_SIGIL + ref.id.name
    else:
        start = ref.id.name

    if not ignore_attributes and ref.attribute:
        return ''.join([start, ATTRIBUTE_SEPARATOR, ref.attribute.name])
    return start


def unknown_reference_error_obj(ref_id):
    if ATTRIBUTE_SEPARATOR in ref_id:
        return FluentReferenceError("Unknown attribute: {0}".format(ref_id))
    if ref_id.startswith(TERM_SIGIL):
        return FluentReferenceError("Unknown term: {0}".format(ref_id))
    return FluentReferenceError("Unknown message: {0}".format(ref_id))
