from __future__ import absolute_import, unicode_literals

import unittest
from datetime import date, datetime
from decimal import Decimal

from fluent.runtime.errors import FluentReferenceError
from fluent.runtime.types import fluent_date, fluent_number

from .. import all_fluent_bundle_implementations
from ..utils import dedent_ftl


@all_fluent_bundle_implementations
class TestNumberBuiltin(unittest.TestCase):

    def setUp(self):
        self.ctx = self.fluent_bundle_cls(['en-US'], use_isolating=False)
        self.ctx.add_messages(dedent_ftl("""
            implicit-call    = { 123456 }
            implicit-call2   = { $arg }
            defaults         = { NUMBER(123456) }
            percent-style    = { NUMBER(1.234, style: "percent") }
            from-arg         = { NUMBER($arg) }
            merge-params     = { NUMBER($arg, useGrouping: 0) }
            bad-kwarg        = { NUMBER(1, badkwarg: 0) }
            bad-arity        = { NUMBER(1, 2) }
        """))

    def test_implicit_call(self):
        val, errs = self.ctx.format('implicit-call', {})
        self.assertEqual(val, "123,456")
        self.assertEqual(len(errs), 0)

    def test_implicit_call2_int(self):
        val, errs = self.ctx.format('implicit-call2', {'arg': 123456})
        self.assertEqual(val, "123,456")
        self.assertEqual(len(errs), 0)

    def test_implicit_call2_float(self):
        val, errs = self.ctx.format('implicit-call2', {'arg': 123456.0})
        self.assertEqual(val, "123,456")
        self.assertEqual(len(errs), 0)

    def test_implicit_call2_decimal(self):
        val, errs = self.ctx.format('implicit-call2', {'arg': Decimal('123456.0')})
        self.assertEqual(val, "123,456")
        self.assertEqual(len(errs), 0)

    def test_defaults(self):
        val, errs = self.ctx.format('defaults', {})
        self.assertEqual(val, "123,456")
        self.assertEqual(len(errs), 0)

    def test_style_in_ftl(self):
        # style is only allowed as developer option
        val, errs = self.ctx.format('percent-style', {})
        self.assertEqual(val, "1.234")
        self.assertEqual(len(errs), 1)

    def test_percent_style(self):
        val, errs = self.ctx.format('from-arg', {'arg': fluent_number(1.234, style="percent")})
        self.assertEqual(val, "123%")
        self.assertEqual(len(errs), 0)

    def test_from_arg_int(self):
        val, errs = self.ctx.format('from-arg', {'arg': 123456})
        self.assertEqual(val, "123,456")
        self.assertEqual(len(errs), 0)

    def test_from_arg_float(self):
        val, errs = self.ctx.format('from-arg', {'arg': 123456.0})
        self.assertEqual(val, "123,456")
        self.assertEqual(len(errs), 0)

    def test_from_arg_decimal(self):
        val, errs = self.ctx.format('from-arg', {'arg': Decimal('123456.0')})
        self.assertEqual(val, "123,456")
        self.assertEqual(len(errs), 0)

    def test_from_arg_missing(self):
        val, errs = self.ctx.format('from-arg', {})
        self.assertEqual(val, "arg")
        self.assertEqual(len(errs), 1)
        self.assertEqual(errs,
                         [FluentReferenceError('Unknown external: arg')])

    def test_partial_application(self):
        number = fluent_number(123456.78, currency="USD", style="currency")
        val, errs = self.ctx.format('from-arg', {'arg': number})
        self.assertEqual(val, "$123,456.78")
        self.assertEqual(len(errs), 0)

    def test_merge_params(self):
        number = fluent_number(123456.78, currency="USD", style="currency")
        val, errs = self.ctx.format('merge-params',
                                    {'arg': number})
        self.assertEqual(val, "$123456.78")
        self.assertEqual(len(errs), 0)

    def test_bad_kwarg(self):
        val, errs = self.ctx.format('bad-kwarg')
        self.assertEqual(val, "1")
        self.assertEqual(len(errs), 1)
        self.assertEqual(type(errs[0]), TypeError)

    def test_bad_arity(self):
        val, errs = self.ctx.format('bad-arity')
        self.assertEqual(val, "1")
        self.assertEqual(len(errs), 1)
        self.assertEqual(type(errs[0]), TypeError)


@all_fluent_bundle_implementations
class TestDatetimeBuiltin(unittest.TestCase):

    def setUp(self):
        self.ctx = self.fluent_bundle_cls(['en-US'], use_isolating=False)
        self.ctx.add_messages(dedent_ftl("""
            implicit-call    = { $date }
            explicit-call    = { DATETIME($date) }
            call-with-arg    = { DATETIME($date, dateStyle: "long") }
        """))

    def test_implicit_call_date(self):
        val, errs = self.ctx.format('implicit-call', {'date': date(2018, 2, 1)})
        self.assertEqual(val, "Feb 1, 2018")
        self.assertEqual(len(errs), 0)

    def test_implicit_call_datetime(self):
        val, errs = self.ctx.format('implicit-call', {'date': datetime(2018, 2, 1, 14, 15, 16)})
        self.assertEqual(val, "Feb 1, 2018")
        self.assertEqual(len(errs), 0)

    def test_explicit_call_date(self):
        val, errs = self.ctx.format('explicit-call', {'date': date(2018, 2, 1)})
        self.assertEqual(val, "Feb 1, 2018")
        self.assertEqual(len(errs), 0)

    def test_explicit_call_datetime(self):
        val, errs = self.ctx.format('explicit-call', {'date': datetime(2018, 2, 1, 14, 15, 16)})
        self.assertEqual(val, "Feb 1, 2018")
        self.assertEqual(len(errs), 0)

    def test_explicit_call_date_fluent_date(self):
        val, errs = self.ctx.format('explicit-call', {'date':
                                                      fluent_date(
                                                          date(2018, 2, 1),
                                                          dateStyle='short')
                                                      })
        self.assertEqual(val, "2/1/18")
        self.assertEqual(len(errs), 0)

    def test_arg(self):
        val, errs = self.ctx.format('call-with-arg', {'date': date(2018, 2, 1)})
        self.assertEqual(val, "February 1, 2018")
        self.assertEqual(len(errs), 0)

    def test_arg_overrides_fluent_date(self):
        val, errs = self.ctx.format('call-with-arg', {'date':
                                                      fluent_date(
                                                          date(2018, 2, 1),
                                                          dateStyle='short')
                                                      })
        self.assertEqual(val, "February 1, 2018")
        self.assertEqual(len(errs), 0)
