# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import warnings
from datetime import date, datetime
from decimal import Decimal

import attr
import pytz
from babel.dates import format_date, format_time, get_datetime_format, get_timezone
from babel.numbers import NumberPattern, parse_pattern

FORMAT_STYLE_DECIMAL = "decimal"
FORMAT_STYLE_CURRENCY = "currency"
FORMAT_STYLE_PERCENT = "percent"
FORMAT_STYLE_OPTIONS = set([
    FORMAT_STYLE_DECIMAL,
    FORMAT_STYLE_CURRENCY,
    FORMAT_STYLE_PERCENT,
])

CURRENCY_DISPLAY_SYMBOL = "symbol"
CURRENCY_DISPLAY_CODE = "code"
CURRENCY_DISPLAY_NAME = "name"
CURRENCY_DISPLAY_OPTIONS = set([
    CURRENCY_DISPLAY_SYMBOL,
    CURRENCY_DISPLAY_CODE,
    CURRENCY_DISPLAY_NAME,
])

DATE_STYLE_OPTIONS = set([
    "full",
    "long",
    "medium",
    "short",
    None,
])

TIME_STYLE_OPTIONS = set([
    "full",
    "long",
    "medium",
    "short",
    None,
])


class FluentType(object):
    def format(self, locale):
        raise NotImplementedError()


class FluentNone(FluentType):
    def __init__(self, name=None):
        self.name = name

    def __eq__(self, other):
        return isinstance(other, FluentNone) and self.name == other.name

    def format(self, locale):
        return self.name or "???"


@attr.s
class NumberFormatOptions(object):
    # We follow the Intl.NumberFormat parameter names here,
    # rather than using underscores as per PEP8, so that
    # we can stick to Fluent spec more easily.

    # See https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/NumberFormat
    style = attr.ib(default=FORMAT_STYLE_DECIMAL,
                    validator=attr.validators.in_(FORMAT_STYLE_OPTIONS))
    currency = attr.ib(default=None)
    currencyDisplay = attr.ib(default=CURRENCY_DISPLAY_SYMBOL,
                              validator=attr.validators.in_(CURRENCY_DISPLAY_OPTIONS))
    useGrouping = attr.ib(default=True)
    minimumIntegerDigits = attr.ib(default=None)
    minimumFractionDigits = attr.ib(default=None)
    maximumFractionDigits = attr.ib(default=None)
    minimumSignificantDigits = attr.ib(default=None)
    maximumSignificantDigits = attr.ib(default=None)


class FluentNumber(FluentType):

    default_number_format_options = NumberFormatOptions()

    def __new__(cls,
                value,
                **kwargs):
        self = super(FluentNumber, cls).__new__(cls, value)
        return self._init(value, kwargs)

    def _init(self, value, kwargs):
        self.options = merge_options(NumberFormatOptions,
                                     getattr(value, 'options', self.default_number_format_options),
                                     kwargs)

        if self.options.style == FORMAT_STYLE_CURRENCY and self.options.currency is None:
            raise ValueError("currency must be provided")

        return self

    def format(self, locale):
        if self.options.style == FORMAT_STYLE_DECIMAL:
            base_pattern = locale.decimal_formats.get(None)
            pattern = self._apply_options(base_pattern)
            return pattern.apply(self, locale)
        elif self.options.style == FORMAT_STYLE_PERCENT:
            base_pattern = locale.percent_formats.get(None)
            pattern = self._apply_options(base_pattern)
            return pattern.apply(self, locale)
        elif self.options.style == FORMAT_STYLE_CURRENCY:
            base_pattern = locale.currency_formats['standard']
            pattern = self._apply_options(base_pattern)
            return pattern.apply(self, locale, currency=self.options.currency)

    def _apply_options(self, pattern):
        # We are essentially trying to copy the
        # https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/NumberFormat
        # API using Babel number formatting routines, which is slightly awkward
        # but not too bad as they are both based on Unicode standards.

        # The easiest route is to start from the existing NumberPattern, and
        # then change its attributes so that Babel's number formatting routines
        # do the right thing. The NumberPattern.pattern string then becomes
        # incorrect, but it is not used when formatting, it is only used
        # initially to set the other attributes.
        pattern = clone_pattern(pattern)
        if not self.options.useGrouping:
            pattern.grouping = _UNGROUPED_PATTERN.grouping
        if self.options.style == FORMAT_STYLE_CURRENCY:
            if self.options.currencyDisplay == CURRENCY_DISPLAY_CODE:
                # Not sure of the correct algorithm here, but this seems to
                # work:
                def replacer(s):
                    return s.replace("¤", "¤¤")
                pattern.suffix = (replacer(pattern.suffix[0]),
                                  replacer(pattern.suffix[1]))
                pattern.prefix = (replacer(pattern.prefix[0]),
                                  replacer(pattern.prefix[1]))
            elif self.options.currencyDisplay == CURRENCY_DISPLAY_NAME:
                # No support for this yet - see
                # https://github.com/python-babel/babel/issues/578 But it's
                # better to display something than crash or a generic fallback
                # string, so we just issue a warning and carry on for now.
                warnings.warn("Unsupported currencyDisplayValue {0}, falling back to {1}"
                              .format(CURRENCY_DISPLAY_NAME,
                                      CURRENCY_DISPLAY_SYMBOL))
        if (self.options.minimumSignificantDigits is not None
                or self.options.maximumSignificantDigits is not None):
            # This triggers babel routines into 'significant digits' mode:
            pattern.pattern = '@'
            # We then manually set int_prec, and leave the rest as they are.
            min_digits = (1 if self.options.minimumSignificantDigits is None
                          else self.options.minimumSignificantDigits)
            max_digits = (min_digits if self.options.maximumSignificantDigits is None
                          else self.options.maximumSignificantDigits)
            pattern.int_prec = (min_digits, max_digits)
        else:
            if self.options.minimumIntegerDigits is not None:
                pattern.int_prec = (self.options.minimumIntegerDigits, pattern.int_prec[1])
            if self.options.minimumFractionDigits is not None:
                pattern.frac_prec = (self.options.minimumFractionDigits, pattern.frac_prec[1])
            if self.options.maximumFractionDigits is not None:
                pattern.frac_prec = (pattern.frac_prec[0], self.options.maximumFractionDigits)

        return pattern


def merge_options(options_class, base, kwargs):
    """
    Given an 'options_class', an optional 'base' object to copy from,
    and some keyword arguments, create a new options instance
    """
    if base is not None and not kwargs:
        # We can safely re-use base, because we don't
        # mutate options objects outside this function.
        return base

    retval = options_class()

    if base is not None:
        # We only copy values in `__dict__` to avoid class attributes.
        retval.__dict__.update(base.__dict__)

    # Use the options_class constructor because it might
    # have validators defined for the fields.
    kwarg_options = options_class(**kwargs)
    # Then merge, using only the ones explicitly given as keyword params.
    for k in kwargs.keys():
        setattr(retval, k, getattr(kwarg_options, k))

    return retval


# We want types that inherit from both FluentNumber and a native type,
# so that:
#
# 1) developers can just pass native types if they don't want to specify
#    options, and fluent should handle these the same internally.
#
# 2) if they are using functions in messages, these can be passed FluentNumber
#    instances in place of a native type and will work just the same without
#    modification (in most cases).

class FluentInt(FluentNumber, int):
    pass


class FluentFloat(FluentNumber, float):
    pass


class FluentDecimal(FluentNumber, Decimal):
    pass


def fluent_number(number, **kwargs):
    if isinstance(number, FluentNumber) and not kwargs:
        return number
    if isinstance(number, int):
        return FluentInt(number, **kwargs)
    elif isinstance(number, float):
        return FluentFloat(number, **kwargs)
    elif isinstance(number, Decimal):
        return FluentDecimal(number, **kwargs)
    elif isinstance(number, FluentNone):
        return number
    else:
        raise TypeError("Can't use fluent_number with object {0} for type {1}"
                        .format(number, type(number)))


_UNGROUPED_PATTERN = parse_pattern("#0")


def clone_pattern(pattern):
    return NumberPattern(pattern.pattern,
                         pattern.prefix,
                         pattern.suffix,
                         pattern.grouping,
                         pattern.int_prec,
                         pattern.frac_prec,
                         pattern.exp_prec,
                         pattern.exp_plus)


@attr.s
class DateFormatOptions(object):
    # Parameters.
    # See https://projectfluent.org/fluent/guide/functions.html#datetime

    # Developer only
    timeZone = attr.ib(default=None)

    # Other
    hour12 = attr.ib(default=None)
    weekday = attr.ib(default=None)
    era = attr.ib(default=None)
    year = attr.ib(default=None)
    month = attr.ib(default=None)
    day = attr.ib(default=None)
    hour = attr.ib(default=None)
    minute = attr.ib(default=None)
    second = attr.ib(default=None)
    timeZoneName = attr.ib(default=None)

    # See https://github.com/tc39/proposal-ecma402-datetime-style
    dateStyle = attr.ib(default=None,
                        validator=attr.validators.in_(DATE_STYLE_OPTIONS))
    timeStyle = attr.ib(default=None,
                        validator=attr.validators.in_(TIME_STYLE_OPTIONS))


_SUPPORTED_DATETIME_OPTIONS = ['dateStyle', 'timeStyle', 'timeZone']


class FluentDateType(FluentType):
    # We need to match signature of `__init__` and `__new__` due to the way
    # some Python implementation (e.g. PyPy) implement some methods.
    # So we leave those alone, and implement another `_init_options`
    # which is called from other constructors.
    def _init_options(self, dt_obj, kwargs):
        if 'timeStyle' in kwargs and not isinstance(self, datetime):
            raise TypeError("timeStyle option can only be specified for datetime instances, not date instance")

        self.options = merge_options(DateFormatOptions,
                                     getattr(dt_obj, 'options', None),
                                     kwargs)
        for k in kwargs:
            if k not in _SUPPORTED_DATETIME_OPTIONS:
                warnings.warn("FluentDateType option {0} is not yet supported".format(k))

    def format(self, locale):
        if isinstance(self, datetime):
            selftz = _ensure_datetime_tzinfo(self, tzinfo=self.options.timeZone)
        else:
            selftz = self

        if self.options.dateStyle is None and self.options.timeStyle is None:
            return format_date(selftz, format='medium', locale=locale)
        elif self.options.dateStyle is None and self.options.timeStyle is not None:
            return format_time(selftz, format=self.options.timeStyle, locale=locale)
        elif self.options.dateStyle is not None and self.options.timeStyle is None:
            return format_date(selftz, format=self.options.dateStyle, locale=locale)
        else:
            # Both date and time. Logic copied from babel.dates.format_datetime,
            # with modifications.
            # Which datetime format do we pick? We arbitrarily pick dateStyle.

            return (get_datetime_format(self.options.dateStyle, locale=locale)
                    .replace("'", "")
                    .replace('{0}', format_time(selftz, self.options.timeStyle, tzinfo=None,
                                                locale=locale))
                    .replace('{1}', format_date(selftz, self.options.dateStyle, locale=locale))
                    )


def _ensure_datetime_tzinfo(dt, tzinfo=None):
    """
    Ensure the datetime passed has an attached tzinfo.
    """
    # Adapted from babel's function.
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=pytz.UTC)
    if tzinfo is not None:
        dt = dt.astimezone(get_timezone(tzinfo))
        if hasattr(tzinfo, 'normalize'):  # pytz
            dt = tzinfo.normalize(datetime)
    return dt


class FluentDate(FluentDateType, date):
    @classmethod
    def from_date(cls, dt_obj, **kwargs):
        obj = cls(dt_obj.year, dt_obj.month, dt_obj.day)
        obj._init_options(dt_obj, kwargs)
        return obj


class FluentDateTime(FluentDateType, datetime):
    @classmethod
    def from_date_time(cls, dt_obj, **kwargs):
        obj = cls(dt_obj.year, dt_obj.month, dt_obj.day,
                  dt_obj.hour, dt_obj.minute, dt_obj.second,
                  dt_obj.microsecond, tzinfo=dt_obj.tzinfo)
        obj._init_options(dt_obj, kwargs)
        return obj


def fluent_date(dt, **kwargs):
    if isinstance(dt, FluentDateType) and not kwargs:
        return dt
    if isinstance(dt, datetime):
        return FluentDateTime.from_date_time(dt, **kwargs)
    elif isinstance(dt, date):
        return FluentDate.from_date(dt, **kwargs)
    elif isinstance(dt, FluentNone):
        return dt
    else:
        raise TypeError("Can't use fluent_date with object {0} of type {1}"
                        .format(dt, type(dt)))
