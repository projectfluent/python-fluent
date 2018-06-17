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
FORMAT_STYLES = set([FORMAT_STYLE_DECIMAL,
                     FORMAT_STYLE_CURRENCY,
                     FORMAT_STYLE_PERCENT])

CURRENCY_DISPLAY_SYMBOL = "symbol"
CURRENCY_DISPLAY_CODE = "code"
CURRENCY_DISPLAY_NAME = "name"
CURRENCY_DISPLAY_OPTIONS = set([
    CURRENCY_DISPLAY_SYMBOL,
    CURRENCY_DISPLAY_CODE,
    CURRENCY_DISPLAY_NAME,
])


class FluentNumber(object):
    # We follow the Intl.NumberFormat parameter names here,
    # rather than using underscores as per PEP8, so that
    # we can stick to Fluent spec more easily.

    # See https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/NumberFormat

    style = FORMAT_STYLE_DECIMAL
    currency = None
    currencyDisplay = CURRENCY_DISPLAY_SYMBOL
    useGrouping = True
    minimumIntegerDigits = None
    minimumFractionDigits = None
    maximumFractionDigits = None
    minimumSignificantDigits = None
    maximumSignificantDigits = None

    DEFAULTS = dict(style=style,
                    currency=currency,
                    currencyDisplay=currencyDisplay,
                    useGrouping=useGrouping,
                    minimumIntegerDigits=minimumIntegerDigits,
                    minimumFractionDigits=minimumFractionDigits,
                    maximumFractionDigits=maximumFractionDigits,
                    minimumSignificantDigits=minimumSignificantDigits,
                    maximumSignificantDigits=maximumSignificantDigits,
                    )

    _ALLOWED_KWARGS = DEFAULTS.keys()

    def __new__(cls,
                value,
                **kwargs):
        self = super(FluentNumber, cls).__new__(cls, value)

        if isinstance(value, FluentNumber):
            copy_instance_attributes(value, self)

        assign_kwargs(self, self._ALLOWED_KWARGS, kwargs)

        if all(getattr(self, k) == v
               for k, v in FluentNumber.DEFAULTS.items()
               if k not in ['style', 'currency']):
            # Shortcut to avoid needing to create NumberPattern later on
            self.defaults = True
        else:
            self.defaults = False

        if self.style not in FORMAT_STYLES:
            raise ValueError("style must be one of: {0}"
                             .format(", ".join(sorted(FORMAT_STYLES))))
        if self.style == FORMAT_STYLE_CURRENCY and self.currency is None:
            raise ValueError("currency must be provided")

        if (self.currencyDisplay is not None and
                self.currencyDisplay not in CURRENCY_DISPLAY_OPTIONS):
            raise ValueError("currencyDisplay must be one of: {0}"
                             .format(", ".join(sorted(CURRENCY_DISPLAY_OPTIONS))))

        return self

    def format(self, locale):
        if self.style == FORMAT_STYLE_DECIMAL:
            base_pattern = locale.decimal_formats.get(None)
            pattern = self._apply_options(base_pattern)
            return pattern.apply(self, locale)
        elif self.style == FORMAT_STYLE_PERCENT:
            base_pattern = locale.percent_formats.get(None)
            pattern = self._apply_options(base_pattern)
            return pattern.apply(self, locale)
        elif self.style == FORMAT_STYLE_CURRENCY:
            base_pattern = locale.currency_formats['standard']
            pattern = self._apply_options(base_pattern)
            return pattern.apply(self, locale, currency=self.currency)

    def _apply_options(self, pattern):
        if self.defaults:
            return pattern
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
        if not self.useGrouping:
            pattern.grouping = _UNGROUPED_PATTERN.grouping
        if self.style == FORMAT_STYLE_CURRENCY:
            if self.currencyDisplay == CURRENCY_DISPLAY_CODE:
                # Not sure of the correct algorithm here, but this seems to
                # work:
                def replacer(s):
                    return s.replace("¤", "¤¤")
                pattern.suffix = (replacer(pattern.suffix[0]),
                                  replacer(pattern.suffix[1]))
                pattern.prefix = (replacer(pattern.prefix[0]),
                                  replacer(pattern.prefix[1]))
            elif self.currencyDisplay == CURRENCY_DISPLAY_NAME:
                # No support for this yet - see
                # https://github.com/python-babel/babel/issues/578 But it's
                # better to display something than crash or a generic fallback
                # string, so we just issue a warning and carry on for now.
                warnings.warn("Unsupported currencyDisplayValue {0}, falling back to {1}"
                              .format(CURRENCY_DISPLAY_NAME,
                                      CURRENCY_DISPLAY_SYMBOL))
        if (self.minimumSignificantDigits is not None
                or self.maximumSignificantDigits is not None):
            # This triggers babel routines into 'significant digits' mode:
            pattern.pattern = '@'
            # We then manually set int_prec, and leave the rest as they are.
            min_digits = (1 if self.minimumSignificantDigits is None
                          else self.minimumSignificantDigits)
            max_digits = (min_digits if self.maximumSignificantDigits is None
                          else self.maximumSignificantDigits)
            pattern.int_prec = (min_digits, max_digits)
        else:
            if self.minimumIntegerDigits is not None:
                pattern.int_prec = (self.minimumIntegerDigits, pattern.int_prec[1])
            if self.minimumFractionDigits is not None:
                pattern.frac_prec = (self.minimumFractionDigits, pattern.frac_prec[1])
            if self.maximumFractionDigits is not None:
                pattern.frac_prec = (pattern.frac_prec[0], self.maximumFractionDigits)

        return pattern


def copy_instance_attributes(from_instance, to_instance):
    # We only copy values in `__dict__`, to avoid class attributes.
    to_instance.__dict__.update(from_instance.__dict__)


def assign_kwargs(to_instance, allowed_args, kwargs):
    for k, v in kwargs.items():
        if k not in allowed_args:
            raise TypeError("Illegal keyword argument {0}".format(k))
        setattr(to_instance, k, v)


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
    dateStyle = attr.ib(default=None)
    timeStyle = attr.ib(default=None)


_SUPPORTED_DATETIME_OPTIONS = ['dateStyle', 'timeStyle', 'timeZone']


class FluentDateType(object):
    # We need an explicit options object
    # to avoid name clashes with attributes on date/datetime

    def _init(self, dt_obj, kwargs):
        if 'timeStyle' in kwargs and not isinstance(self, datetime):
            raise TypeError("timeStyle option can only be specified for datetime instances, not date instance")

        options = DateFormatOptions()
        if isinstance(dt_obj, FluentDateType):
            copy_instance_attributes(dt_obj.options, options)
        # Use the DateFormatOptions constructor because it might
        # have validators defined for the fields.
        kwarg_options = DateFormatOptions(**kwargs)
        # Then merge, using only the ones explicitly given as keyword params.
        for k in kwargs.keys():
            setattr(options, k, getattr(kwarg_options, k))

            if k not in _SUPPORTED_DATETIME_OPTIONS:
                warnings.warn("FluentDateType option {0} is not yet supported".format(k))

        self.options = options

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
    def __new__(cls,
                dt_obj,
                **kwargs):
        self = super(FluentDate, cls).__new__(
            cls,
            dt_obj.year, dt_obj.month, dt_obj.day)
        self._init(dt_obj, kwargs)
        return self


class FluentDateTime(FluentDateType, datetime):
    def __new__(cls,
                dt_obj,
                **kwargs):
        self = super(FluentDateTime, cls).__new__(
            cls,
            dt_obj.year, dt_obj.month, dt_obj.day,
            dt_obj.hour, dt_obj.minute, dt_obj.second,
            dt_obj.microsecond, tzinfo=dt_obj.tzinfo)

        self._init(dt_obj, kwargs)
        return self


def fluent_date(dt, **kwargs):
    if isinstance(dt, FluentDateType) and not kwargs:
        return dt
    if isinstance(dt, datetime):
        return FluentDateTime(dt, **kwargs)
    elif isinstance(dt, date):
        return FluentDate(dt, **kwargs)
    else:
        raise TypeError("Can't use fluent_date with object {0} of type {1}"
                        .format(dt, type(dt)))