# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import unittest

from fluent.types import fluent_number, FluentNumber
from babel import Locale


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
        self.assertTrue(isinstance(fluent_number(1), int))
        self.assertTrue(isinstance(fluent_number(1), FluentNumber))

    def test_float(self):
        self.assertTrue(isinstance(fluent_number(1.1), float))
        self.assertTrue(isinstance(fluent_number(1.1), FluentNumber))

    def test_use_grouping(self):
        f1 = fluent_number(123456.78, useGrouping=True)
        f2 = fluent_number(123456.78, useGrouping=False)
        self.assertEqual(f1.format(self.locale), "123,456.78")
        self.assertEqual(f2.format(self.locale), "123456.78")
        # ensure we didn't mutate anything when we created the new
        # NumberPattern:
        self.assertEqual(f1.format(self.locale), "123,456.78")

    def test_minimum_integer_digits(self):
        f = fluent_number(1.23, minimumIntegerDigits=3)
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
        self.assertEqual(f1.__dict__['useGrouping'], False)
        self.assertEqual(f1.useGrouping, False)

        # Check we didn't mutate anything
        self.assertIs(FluentNumber.useGrouping, True)
        self.assertIs(FluentNumber.DEFAULTS['useGrouping'], True)

        f2 = fluent_number(f1, style="percent")
        self.assertEqual(f2.style, "percent")

        # Check we copied
        self.assertEqual(f2.useGrouping, False)

        # and didn't mutate anything
        self.assertEqual(f1.style, "decimal")
