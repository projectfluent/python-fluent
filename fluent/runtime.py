# Runtime functions for compiled messages

from datetime import date, datetime
from decimal import Decimal

import six

from fluent.exceptions import FluentReferenceError
from .types import fluent_date, fluent_number

__all__ = ['handle_argument', 'FluentReferenceError']


text_type = six.text_type


def handle_argument(arg, name, locale, errors):
    if isinstance(arg, text_type):
        return arg
    elif isinstance(arg, (int, float, Decimal)):
        return fluent_number(arg).format(locale)
    elif isinstance(arg, (date, datetime)):
        return fluent_date(arg).format(locale)
    errors.append(TypeError("Unsupported external type: {0}, {1}"
                            .format(name, type(arg))))
    return name
