import unittest
import warnings
from datetime import date, datetime
from decimal import Decimal

import pytz
from babel import Locale

from fluent.runtime.types import FluentDateType, FluentNumber, fluent_date, fluent_number


class TestFluentNumber(unittest.TestCase):

    locale = Locale.parse('en_US')

    def setUp(self):
        self.cur_pos = fluent_number(123456.78123,
                                     currency='USD',
                                     style='currency')
        self.cur_neg = fluent_number(-123456.78123,
                                     currency='USD',
                                     style='currency')

    def test_int(self):
        i = fluent_number(1)
        self.assertTrue(isinstance(i, int))
        self.assertTrue(isinstance(i, FluentNumber))
        self.assertEqual(i + 1, 2)

    def test_float(self):
        f = fluent_number(1.1)
        self.assertTrue(isinstance(f, float))
        self.assertTrue(isinstance(f, FluentNumber))
        self.assertEqual(f + 1, 2.1)

    def test_decimal(self):
        d = Decimal('1.1')
        self.assertTrue(isinstance(fluent_number(d), Decimal))
        self.assertTrue(isinstance(fluent_number(d), FluentNumber))
        self.assertEqual(d + 1, Decimal('2.1'))

    def test_disallow_nonexistant_options(self):
        self.assertRaises(
            TypeError,
            fluent_number,
            1,
            not_a_real_option=True,
        )

    def test_style_validation(self):
        self.assertRaises(ValueError,
                          fluent_number,
                          1,
                          style='xyz')

    def test_use_grouping(self):
        f1 = fluent_number(123456.78, useGrouping=True)
        f2 = fluent_number(123456.78, useGrouping=False)
        self.assertEqual(f1.format(self.locale), "123,456.78")
        self.assertEqual(f2.format(self.locale), "123456.78")
        # ensure we didn't mutate anything when we created the new
        # NumberPattern:
        self.assertEqual(f1.format(self.locale), "123,456.78")

    def test_use_grouping_decimal(self):
        d = Decimal('123456.78')
        f1 = fluent_number(d, useGrouping=True)
        f2 = fluent_number(d, useGrouping=False)
        self.assertEqual(f1.format(self.locale), "123,456.78")
        self.assertEqual(f2.format(self.locale), "123456.78")

    def test_minimum_integer_digits(self):
        f = fluent_number(1.23, minimumIntegerDigits=3)
        self.assertEqual(f.format(self.locale), "001.23")

    def test_minimum_integer_digits_decimal(self):
        f = fluent_number(Decimal('1.23'), minimumIntegerDigits=3)
        self.assertEqual(f.format(self.locale), "001.23")

    def test_minimum_fraction_digits(self):
        f = fluent_number(1.2, minimumFractionDigits=3)
        self.assertEqual(f.format(self.locale), "1.200")

    def test_maximum_fraction_digits(self):
        f1 = fluent_number(1.23456)
        self.assertEqual(f1.format(self.locale), "1.235")
        f2 = fluent_number(1.23456, maximumFractionDigits=5)
        self.assertEqual(f2.format(self.locale), "1.23456")

    def test_minimum_significant_digits(self):
        f1 = fluent_number(123, minimumSignificantDigits=5)
        self.assertEqual(f1.format(self.locale), "123.00")
        f2 = fluent_number(12.3, minimumSignificantDigits=5)
        self.assertEqual(f2.format(self.locale), "12.300")

    def test_maximum_significant_digits(self):
        f1 = fluent_number(123456, maximumSignificantDigits=3)
        self.assertEqual(f1.format(self.locale), "123,000")
        f2 = fluent_number(12.3456, maximumSignificantDigits=3)
        self.assertEqual(f2.format(self.locale), "12.3")
        f3 = fluent_number(12, maximumSignificantDigits=5)
        self.assertEqual(f3.format(self.locale), "12")

    def test_currency(self):
        # This test the default currencyDisplay value
        self.assertEqual(self.cur_pos.format(self.locale), "$123,456.78")

    def test_currency_display_validation(self):
        self.assertRaises(ValueError,
                          fluent_number,
                          1234,
                          currencyDisplay="junk")

    def test_currency_display_symbol(self):
        cur_pos_sym = fluent_number(self.cur_pos, currencyDisplay="symbol")
        cur_neg_sym = fluent_number(self.cur_neg, currencyDisplay="symbol")
        self.assertEqual(cur_pos_sym.format(self.locale), "$123,456.78")
        self.assertEqual(cur_neg_sym.format(self.locale), "-$123,456.78")

    def test_currency_display_code(self):
        # Outputs here were determined by comparing with Javascrpt
        # Intl.NumberFormat in Firefox.
        cur_pos_code = fluent_number(self.cur_pos, currencyDisplay="code")
        cur_neg_code = fluent_number(self.cur_neg, currencyDisplay="code")
        self.assertEqual(cur_pos_code.format(self.locale), "USD123,456.78")
        self.assertEqual(cur_neg_code.format(self.locale), "-USD123,456.78")

    @unittest.skip("Babel doesn't provide support for this yet")
    def test_currency_display_name(self):
        cur_pos_name = fluent_number(self.cur_pos, currencyDisplay="name")
        cur_neg_name = fluent_number(self.cur_neg, currencyDisplay="name")
        self.assertEqual(cur_pos_name.format(self.locale), "123,456.78 US dollars")
        self.assertEqual(cur_neg_name.format(self.locale), "-123,456.78 US dollars")

        # Some others locales:
        hr_BA = Locale.parse('hr_BA')
        self.assertEqual(cur_pos_name.format(hr_BA),
                         "123.456,78 američkih dolara")
        es_GT = Locale.parse('es_GT')
        self.assertEqual(cur_pos_name.format(es_GT),
                         "dólares estadounidenses 123,456.78")

    def test_copy_attributes(self):
        f1 = fluent_number(123456.78, useGrouping=False)
        self.assertEqual(f1.options.useGrouping, False)

        # Check we didn't mutate anything
        self.assertIs(FluentNumber.default_number_format_options.useGrouping, True)

        f2 = fluent_number(f1, style="percent")
        self.assertEqual(f2.options.style, "percent")

        # Check we copied
        self.assertEqual(f2.options.useGrouping, False)

        # and didn't mutate anything
        self.assertEqual(f1.options.style, "decimal")
        self.assertEqual(FluentNumber.default_number_format_options.style, "decimal")


class TestFluentDate(unittest.TestCase):

    locale = Locale.parse('en_US')

    def setUp(self):
        self.a_date = date(2018, 2, 1)
        self.a_datetime = datetime(2018, 2, 1, 14, 15, 16, 123456,
                                   tzinfo=pytz.UTC)

    def test_date(self):
        fd = fluent_date(self.a_date)
        self.assertTrue(isinstance(fd, date))
        self.assertTrue(isinstance(fd, FluentDateType))
        self.assertEqual(fd.year, self.a_date.year)
        self.assertEqual(fd.month, self.a_date.month)
        self.assertEqual(fd.day, self.a_date.day)

    def test_datetime(self):
        fd = fluent_date(self.a_datetime)
        self.assertTrue(isinstance(fd, datetime))
        self.assertTrue(isinstance(fd, FluentDateType))
        self.assertEqual(fd.year, self.a_datetime.year)
        self.assertEqual(fd.month, self.a_datetime.month)
        self.assertEqual(fd.day, self.a_datetime.day)
        self.assertEqual(fd.hour, self.a_datetime.hour)
        self.assertEqual(fd.minute, self.a_datetime.minute)
        self.assertEqual(fd.second, self.a_datetime.second)
        self.assertEqual(fd.microsecond, self.a_datetime.microsecond)
        self.assertEqual(fd.tzinfo, self.a_datetime.tzinfo)

    def test_format_defaults(self):
        fd = fluent_date(self.a_date)
        en_US = Locale.parse('en_US')
        en_GB = Locale.parse('en_GB')
        self.assertEqual(fd.format(en_GB), '1 Feb 2018')
        self.assertEqual(fd.format(en_US), 'Feb 1, 2018')

    def test_dateStyle_date(self):
        fd = fluent_date(self.a_date, dateStyle='long')
        en_US = Locale.parse('en_US')
        en_GB = Locale.parse('en_GB')
        self.assertEqual(fd.format(en_GB), '1 February 2018')
        self.assertEqual(fd.format(en_US), 'February 1, 2018')

    def test_dateStyle_datetime(self):
        fd = fluent_date(self.a_datetime, dateStyle='long')
        en_US = Locale.parse('en_US')
        en_GB = Locale.parse('en_GB')
        self.assertEqual(fd.format(en_GB), '1 February 2018')
        self.assertEqual(fd.format(en_US), 'February 1, 2018')

    def test_timeStyle_datetime(self):
        fd = fluent_date(self.a_datetime, timeStyle='short')
        en_US = Locale.parse('en_US')
        en_GB = Locale.parse('en_GB')
        self.assertRegex(fd.format(en_US), '^2:15\\sPM$')
        self.assertEqual(fd.format(en_GB), '14:15')

    def test_dateStyle_and_timeStyle_datetime(self):
        fd = fluent_date(self.a_datetime, timeStyle='short', dateStyle='short')
        en_US = Locale.parse('en_US')
        en_GB = Locale.parse('en_GB')
        self.assertRegex(fd.format(en_US), '^2/1/18, 2:15\\sPM$')
        self.assertEqual(fd.format(en_GB), '01/02/2018, 14:15')

    def test_validate_dateStyle(self):
        self.assertRaises(ValueError,
                          fluent_date,
                          self.a_date,
                          dateStyle="nothing")

    def test_validate_timeStyle(self):
        self.assertRaises(ValueError,
                          fluent_date,
                          self.a_datetime,
                          timeStyle="nothing")

    def test_timeZone(self):
        en_GB = Locale.parse('en_GB')
        LondonTZ = pytz.timezone('Europe/London')

        # 1st July is a date in British Summer Time

        # datetime object with tzinfo set to BST
        dt1 = datetime(2018, 7, 1, 23, 30, 0, tzinfo=pytz.UTC).astimezone(LondonTZ)
        fd1 = fluent_date(dt1, dateStyle='short', timeStyle='short')
        self.assertEqual(fd1.format(en_GB), '02/07/2018, 00:30')
        fd1b = fluent_date(dt1, dateStyle='full', timeStyle='full')
        self.assertRegex(fd1b.format(en_GB), '^Monday, 2 July 2018(,| at) 00:30:00 British Summer Time$')
        fd1c = fluent_date(dt1, dateStyle='short')
        self.assertEqual(fd1c.format(en_GB), '02/07/2018')
        fd1d = fluent_date(dt1, timeStyle='short')
        self.assertEqual(fd1d.format(en_GB), '00:30')

        # datetime object with no TZ, TZ passed in to fluent_date
        dt2 = datetime(2018, 7, 1, 23, 30, 0)  # Assumed UTC
        fd2 = fluent_date(dt2, dateStyle='short', timeStyle='short',
                          timeZone='Europe/London')
        self.assertEqual(fd2.format(en_GB), '02/07/2018, 00:30')
        fd2b = fluent_date(dt2, dateStyle='full', timeStyle='full',
                           timeZone='Europe/London')
        self.assertRegex(fd2b.format(en_GB), '^Monday, 2 July 2018(,| at) 00:30:00 British Summer Time$')
        fd2c = fluent_date(dt2, dateStyle='short',
                           timeZone='Europe/London')
        self.assertEqual(fd2c.format(en_GB), '02/07/2018')
        fd2d = fluent_date(dt1, timeStyle='short',
                           timeZone='Europe/London')
        self.assertEqual(fd2d.format(en_GB), '00:30')

    def test_allow_unsupported_options(self):
        # We are just checking that these don't raise exceptions
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            fluent_date(self.a_date,
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
        self.assertRaises(
            TypeError,
            fluent_date,
            self.a_date,
            not_a_real_option=True,
        )

    def test_dont_wrap_unnecessarily(self):
        f1 = fluent_date(self.a_date)
        f2 = fluent_date(f1)
        self.assertIs(f1, f2)

    def test_copy_attributes(self):
        f1 = fluent_date(self.a_date, dateStyle='long', hour12=False)
        self.assertEqual(f1.options.dateStyle, 'long')

        f2 = fluent_date(f1, hour12=False)

        # Check we copied other attributes:
        self.assertEqual(f2.options.dateStyle, "long")
        self.assertEqual(f2.options.hour12, False)

        # Check we can override
        f3 = fluent_date(f2, dateStyle="full")
        self.assertEqual(f3.options.dateStyle, "full")

        # and didn't mutate anything
        self.assertEqual(f1.options.dateStyle, "long")
        self.assertEqual(f2.options.dateStyle, "long")
