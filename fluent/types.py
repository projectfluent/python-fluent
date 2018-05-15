from babel.numbers import parse_pattern, NumberPattern


FORMAT_STYLE_DECIMAL = "decimal"
FORMAT_STYLE_CURRENCY = "currency"
FORMAT_STYLE_PERCENT = "percent"
FORMAT_STYLES = set([FORMAT_STYLE_DECIMAL,
                     FORMAT_STYLE_CURRENCY,
                     FORMAT_STYLE_PERCENT])


class FluentNumber(object):
    # We follow the Intl.NumberFormat parameter names here,
    # rather than using underscores as per PEP8, so that
    # we can stick to Fluent spec more easily.

    # See https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/NumberFormat

    style = FORMAT_STYLE_DECIMAL
    currency = None
    currencyDisplay = None
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
        # It's easiest to start from an existing one.
        pattern = clone_pattern(pattern)
        if not self.useGrouping:
            pattern.grouping = _UNGROUPED_PATTERN.grouping

        # TODO - support all the other formatting options, or issue warnings if
        # unsupported ones are used

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
