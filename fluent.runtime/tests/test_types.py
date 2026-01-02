import re
import warnings
from datetime import date, datetime
from decimal import Decimal

import pytest
import pytz
from babel import Locale
from fluent.runtime.types import (
    FluentDateType,
    FluentNumber,
    fluent_date,
    fluent_number,
)

en_US = Locale.parse("en_US")
cur_pos = fluent_number(123456.78123, currency="USD", style="currency")
cur_neg = fluent_number(-123456.78123, currency="USD", style="currency")


class TestFluentNumber:
    def test_int(self):
        i = fluent_number(1)
        assert isinstance(i, int)
        assert isinstance(i, FluentNumber)
        assert i + 1 == 2

    def test_float(self):
        f = fluent_number(1.1)
        assert isinstance(f, float)
        assert isinstance(f, FluentNumber)
        assert f + 1 == 2.1

    def test_decimal(self):
        d = Decimal("1.1")
        assert isinstance(fluent_number(d), Decimal)
        assert isinstance(fluent_number(d), FluentNumber)
        assert d + 1 == Decimal("2.1")

    def test_disallow_nonexistant_options(self):
        with pytest.raises(TypeError):
            fluent_number(
                1,
                not_a_real_option=True,
            )

    def test_style_validation(self):
        with pytest.raises(ValueError):
            fluent_number(1, style="xyz")

    def test_use_grouping(self):
        f1 = fluent_number(123456.78, useGrouping=True)
        f2 = fluent_number(123456.78, useGrouping=False)
        assert f1.format(en_US) == "123,456.78"
        assert f2.format(en_US) == "123456.78"
        # ensure we didn't mutate anything when we created the new
        # NumberPattern:
        assert f1.format(en_US) == "123,456.78"

    def test_use_grouping_decimal(self):
        d = Decimal("123456.78")
        f1 = fluent_number(d, useGrouping=True)
        f2 = fluent_number(d, useGrouping=False)
        assert f1.format(en_US) == "123,456.78"
        assert f2.format(en_US) == "123456.78"

    def test_minimum_integer_digits(self):
        f = fluent_number(1.23, minimumIntegerDigits=3)
        assert f.format(en_US) == "001.23"

    def test_minimum_integer_digits_decimal(self):
        f = fluent_number(Decimal("1.23"), minimumIntegerDigits=3)
        assert f.format(en_US) == "001.23"

    def test_minimum_fraction_digits(self):
        f = fluent_number(1.2, minimumFractionDigits=3)
        assert f.format(en_US) == "1.200"

    def test_maximum_fraction_digits(self):
        f1 = fluent_number(1.23456)
        assert f1.format(en_US) == "1.235"
        f2 = fluent_number(1.23456, maximumFractionDigits=5)
        assert f2.format(en_US) == "1.23456"

    def test_minimum_significant_digits(self):
        f1 = fluent_number(123, minimumSignificantDigits=5)
        assert f1.format(en_US) == "123.00"
        f2 = fluent_number(12.3, minimumSignificantDigits=5)
        assert f2.format(en_US) == "12.300"

    def test_maximum_significant_digits(self):
        f1 = fluent_number(123456, maximumSignificantDigits=3)
        assert f1.format(en_US) == "123,000"
        f2 = fluent_number(12.3456, maximumSignificantDigits=3)
        assert f2.format(en_US) == "12.3"
        f3 = fluent_number(12, maximumSignificantDigits=5)
        assert f3.format(en_US) == "12"

    def test_currency(self):
        # This test the default currencyDisplay value
        assert cur_pos.format(en_US) == "$123,456.78"

    def test_currency_display_validation(self):
        with pytest.raises(ValueError):
            fluent_number(1234, currencyDisplay="junk")

    def test_currency_display_symbol(self):
        cur_pos_sym = fluent_number(cur_pos, currencyDisplay="symbol")
        cur_neg_sym = fluent_number(cur_neg, currencyDisplay="symbol")
        assert cur_pos_sym.format(en_US) == "$123,456.78"
        assert cur_neg_sym.format(en_US) == "-$123,456.78"

    def test_currency_display_code(self):
        # Outputs here were determined by comparing with Javascrpt
        # Intl.NumberFormat in Firefox.
        cur_pos_code = fluent_number(cur_pos, currencyDisplay="code")
        cur_neg_code = fluent_number(cur_neg, currencyDisplay="code")
        assert cur_pos_code.format(en_US) == "USD123,456.78"
        assert cur_neg_code.format(en_US) == "-USD123,456.78"

    @pytest.mark.skip("Babel doesn't provide support for this yet")
    def test_currency_display_name(self):
        cur_pos_name = fluent_number(cur_pos, currencyDisplay="name")
        cur_neg_name = fluent_number(cur_neg, currencyDisplay="name")
        assert cur_pos_name.format(en_US) == "123,456.78 US dollars"
        assert cur_neg_name.format(en_US) == "-123,456.78 US dollars"

        # Some others locales:
        hr_BA = Locale.parse("hr_BA")
        assert cur_pos_name.format(hr_BA) == "123.456,78 američkih dolara"
        es_GT = Locale.parse("es_GT")
        assert cur_pos_name.format(es_GT) == "dólares estadounidenses 123,456.78"

    def test_copy_attributes(self):
        f1 = fluent_number(123456.78, useGrouping=False)
        assert f1.options.useGrouping is False

        # Check we didn't mutate anything
        assert FluentNumber.default_number_format_options.useGrouping is True

        f2 = fluent_number(f1, style="percent")
        assert f2.options.style == "percent"

        # Check we copied
        assert f2.options.useGrouping is False

        # and didn't mutate anything
        assert f1.options.style == "decimal"
        assert FluentNumber.default_number_format_options.style == "decimal"


a_date = date(2018, 2, 1)
a_datetime = datetime(2018, 2, 1, 14, 15, 16, 123456, tzinfo=pytz.UTC)


class TestFluentDate:
    def test_date(self):
        fd = fluent_date(a_date)
        assert isinstance(fd, date)
        assert isinstance(fd, FluentDateType)
        assert fd.year == a_date.year
        assert fd.month == a_date.month
        assert fd.day == a_date.day

    def test_datetime(self):
        fd = fluent_date(a_datetime)
        assert isinstance(fd, datetime)
        assert isinstance(fd, FluentDateType)
        assert fd.year == a_datetime.year
        assert fd.month == a_datetime.month
        assert fd.day == a_datetime.day
        assert fd.hour == a_datetime.hour
        assert fd.minute == a_datetime.minute
        assert fd.second == a_datetime.second
        assert fd.microsecond == a_datetime.microsecond
        assert fd.tzinfo == a_datetime.tzinfo

    def test_format_defaults(self):
        fd = fluent_date(a_date)
        en_US = Locale.parse("en_US")
        en_GB = Locale.parse("en_GB")
        assert fd.format(en_GB) == "1 Feb 2018"
        assert fd.format(en_US) == "Feb 1, 2018"

    def test_dateStyle_date(self):
        fd = fluent_date(a_date, dateStyle="long")
        en_US = Locale.parse("en_US")
        en_GB = Locale.parse("en_GB")
        assert fd.format(en_GB) == "1 February 2018"
        assert fd.format(en_US) == "February 1, 2018"

    def test_dateStyle_datetime(self):
        fd = fluent_date(a_datetime, dateStyle="long")
        en_US = Locale.parse("en_US")
        en_GB = Locale.parse("en_GB")
        assert fd.format(en_GB) == "1 February 2018"
        assert fd.format(en_US) == "February 1, 2018"

    def test_timeStyle_datetime(self):
        fd = fluent_date(a_datetime, timeStyle="short")
        en_US = Locale.parse("en_US")
        en_GB = Locale.parse("en_GB")
        assert re.search("^2:15\\sPM$", fd.format(en_US))
        assert fd.format(en_GB) == "14:15"

    def test_dateStyle_and_timeStyle_datetime(self):
        fd = fluent_date(a_datetime, timeStyle="short", dateStyle="short")
        en_US = Locale.parse("en_US")
        en_GB = Locale.parse("en_GB")
        assert re.search("^2/1/18, 2:15\\sPM$", fd.format(en_US))
        assert fd.format(en_GB) == "01/02/2018, 14:15"

    def test_validate_dateStyle(self):
        with pytest.raises(ValueError):
            fluent_date(a_date, dateStyle="nothing")

    def test_validate_timeStyle(self):
        with pytest.raises(ValueError):
            fluent_date(a_datetime, timeStyle="nothing")

    def test_timeZone(self):
        en_GB = Locale.parse("en_GB")
        LondonTZ = pytz.timezone("Europe/London")

        # 1st July is a date in British Summer Time

        # datetime object with tzinfo set to BST
        dt1 = datetime(2018, 7, 1, 23, 30, 0, tzinfo=pytz.UTC).astimezone(LondonTZ)
        fd1 = fluent_date(dt1, dateStyle="short", timeStyle="short")
        assert fd1.format(en_GB) == "02/07/2018, 00:30"
        fd1b = fluent_date(dt1, dateStyle="full", timeStyle="full")
        assert re.search(
            "^Monday,? 2 July 2018(,| at) 00:30:00 British Summer Time$",
            fd1b.format(en_GB),
        )
        fd1c = fluent_date(dt1, dateStyle="short")
        assert fd1c.format(en_GB) == "02/07/2018"
        fd1d = fluent_date(dt1, timeStyle="short")
        assert fd1d.format(en_GB) == "00:30"

        # datetime object with no TZ, TZ passed in to fluent_date
        dt2 = datetime(2018, 7, 1, 23, 30, 0)  # Assumed UTC
        fd2 = fluent_date(
            dt2, dateStyle="short", timeStyle="short", timeZone="Europe/London"
        )
        assert fd2.format(en_GB) == "02/07/2018, 00:30"
        fd2b = fluent_date(
            dt2, dateStyle="full", timeStyle="full", timeZone="Europe/London"
        )
        assert re.search(
            "^Monday,? 2 July 2018(,| at) 00:30:00 British Summer Time$",
            fd2b.format(en_GB),
        )
        fd2c = fluent_date(dt2, dateStyle="short", timeZone="Europe/London")
        assert fd2c.format(en_GB) == "02/07/2018"
        fd2d = fluent_date(dt1, timeStyle="short", timeZone="Europe/London")
        assert fd2d.format(en_GB) == "00:30"

    def test_allow_unsupported_options(self):
        # We are just checking that these don't raise exceptions
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            fluent_date(
                a_date,
                hour12=True,
                weekday="narrow",
                era="narrow",
                year="numeric",
                month="numeric",
                day="numeric",
                hour="numeric",
                minute="numeric",
                second="numeric",
                timeZoneName="short",
            )

    def test_disallow_nonexistant_options(self):
        with pytest.raises(TypeError):
            fluent_date(
                a_date,
                not_a_real_option=True,
            )

    def test_dont_wrap_unnecessarily(self):
        f1 = fluent_date(a_date)
        f2 = fluent_date(f1)
        assert f1 is f2

    def test_copy_attributes(self):
        f1 = fluent_date(a_date, dateStyle="long", hour12=False)
        assert f1.options.dateStyle == "long"

        f2 = fluent_date(f1, hour12=False)

        # Check we copied other attributes:
        assert f2.options.dateStyle == "long"
        assert f2.options.hour12 is False

        # Check we can override
        f3 = fluent_date(f2, dateStyle="full")
        assert f3.options.dateStyle == "full"

        # and didn't mutate anything
        assert f1.options.dateStyle == "long"
        assert f2.options.dateStyle == "long"
