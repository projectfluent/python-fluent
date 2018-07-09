# Runtime functions for compiled messages

from datetime import date, datetime
from decimal import Decimal

import six

from fluent.exceptions import FluentCyclicReferenceError, FluentReferenceError

from .types import FluentNone, FluentType, fluent_date, fluent_number

__all__ = ['handle_argument', 'handle_output', 'FluentCyclicReferenceError', 'FluentReferenceError', 'FluentNone']


text_type = six.text_type

RETURN_TYPES = {
    'handle_argument': object,
    'handle_output': text_type,
    'FluentReferenceError': FluentReferenceError,
    'FluentNone': FluentNone,
}


def handle_argument(arg, name, locale, errors):
    if isinstance(arg, text_type):
        return arg
    elif isinstance(arg, (int, float, Decimal)):
        return fluent_number(arg)
    elif isinstance(arg, (date, datetime)):
        return fluent_date(arg)
    errors.append(TypeError("Unsupported external type: {0}, {1}"
                            .format(name, type(arg))))
    return name


def handle_output(val, locale, errors):
    if isinstance(val, text_type):
        return val
    elif isinstance(val, FluentType):
        return val.format(locale)
    else:
        # TODO - tests for this branch, check it is the same
        # as for interpreter
        errors.append(TypeError("Cannot output object {0} of type {1}"
                                .format(val, type(val))))
