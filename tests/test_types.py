from __future__ import absolute_import, unicode_literals

import unittest

from fluent.types import fluent_number, FluentNumber
from babel import Locale


class TestFluentNumber(unittest.TestCase):

    locale = Locale.parse('en_US')

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
