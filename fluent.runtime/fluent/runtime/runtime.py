# Runtime functions for compiled messages

from datetime import date, datetime
from decimal import Decimal

import six

from .errors import FluentCyclicReferenceError, FluentFormatError, FluentReferenceError
from .types import FluentNone, FluentType, fluent_date, fluent_number

__all__ = ['handle_argument_with_escaper', 'handle_output_with_escaper', 'handle_argument',
           'handle_output', 'FluentCyclicReferenceError', 'FluentReferenceError',
           'FluentFormatError', 'FluentNone']


text_type = six.text_type

RETURN_TYPES = {
    'handle_argument': object,
    'handle_output': text_type,
    'FluentReferenceError': FluentReferenceError,
    'FluentFormatError': FluentFormatError,
    'FluentNone': FluentNone,
}


def handle_argument_with_escaper(arg, name, output_type, locale, errors):
    # This needs to be synced with resolver.handle_variable_reference
    if isinstance(arg, output_type):
        return arg
    if isinstance(arg, text_type):
        return arg
    elif isinstance(arg, (int, float, Decimal)):
        return fluent_number(arg)
    elif isinstance(arg, (date, datetime)):
        return fluent_date(arg)
    errors.append(TypeError("Unsupported external type: {0}, {1}"
                            .format(name, type(arg))))
    return name


def handle_argument(arg, name, locale, errors):
    # handle_argument_with_escaper specialized to null escaper
    # This needs to be synced with resolver.handle_variable_reference
    if isinstance(arg, text_type):
        return arg
    elif isinstance(arg, (int, float, Decimal)):
        return fluent_number(arg)
    elif isinstance(arg, (date, datetime)):
        return fluent_date(arg)
    errors.append(TypeError("Unsupported external type: {0}, {1}"
                            .format(name, type(arg))))
    return name


def handle_output_with_escaper(val, output_type, escaper_escape, locale, errors):
    if isinstance(val, output_type):
        return val
    elif isinstance(val, text_type):
        return escaper_escape(val)
    elif isinstance(val, FluentType):
        return escaper_escape(val.format(locale))
    else:
        # The only way for this branch to run is whem functions return
        # objects of the wrong type.
        raise TypeError("Cannot handle object {0} of type {1}"
                        .format(val, type(val).__name__))


def handle_output(val, locale, errors):
    # handle_output_with_escaper specialized to null_escaper
    if isinstance(val, text_type):
        return val
    elif isinstance(val, FluentType):
        return val.format(locale)
    else:
        # The only way for this branch to run is when functions return
        # objects of the wrong type.
        raise TypeError("Cannot handle object {0} of type {1}"
                        .format(val, type(val).__name__))
