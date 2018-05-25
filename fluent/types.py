# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import warnings

from babel.numbers import parse_pattern, NumberPattern


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

    def __new__(cls,
                value,
                **kwargs):
        self = super(FluentNumber, cls).__new__(cls, value)

        if isinstance(value, FluentNumber):
            # Copying existing options if they were specified
            # on the instance only (hence we check '__dict__')
            options = {k: getattr(value, k)
                       for k in FluentNumber.DEFAULTS.keys()
                       if k in value.__dict__}
        else:
            options = {}
        options.update(kwargs)

        for k, v in options.items():
            setattr(self, k, v)

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


class FluentInt(FluentNumber, int):
    pass


class FluentFloat(FluentNumber, float):
    pass


def fluent_number(number, **kwargs):
    if isinstance(number, FluentNumber) and not kwargs:
        return number
    if isinstance(number, int):
        return FluentInt(number, **kwargs)
    elif isinstance(number, float):
        return FluentFloat(number, **kwargs)
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
