from __future__ import absolute_import, unicode_literals

import unittest

from fluent.bundle import FluentBundle
from fluent.bundle.errors import FluentReferenceError

from ..utils import dedent_ftl


class TestSelectExpressionWithStrings(unittest.TestCase):

    def setUp(self):
        self.ctx = FluentBundle(['en-US'], use_isolating=False)

    def test_with_a_matching_selector(self):
        self.ctx.add_messages(dedent_ftl("""
            foo = { "a" ->
                [a] A
               *[b] B
             }
        """))
        val, errs = self.ctx.format('foo', {})
        self.assertEqual(val, "A")
        self.assertEqual(len(errs), 0)

    def test_with_a_non_matching_selector(self):
        self.ctx.add_messages(dedent_ftl("""
            foo = { "c" ->
                [a] A
               *[b] B
             }
        """))
        val, errs = self.ctx.format('foo', {})
        self.assertEqual(val, "B")
        self.assertEqual(len(errs), 0)

    def test_with_a_missing_selector(self):
        self.ctx.add_messages(dedent_ftl("""
            foo = { $none ->
                [a] A
               *[b] B
             }
        """))
        val, errs = self.ctx.format('foo', {})
        self.assertEqual(val, "B")
        self.assertEqual(errs,
                         [FluentReferenceError("Unknown external: none")])

    def test_with_argument_expression(self):
        self.ctx.add_messages(dedent_ftl("""
            foo = { $arg ->
                [a] A
               *[b] B
             }
        """))
        val, errs = self.ctx.format('foo', {'arg': 'a'})
        self.assertEqual(val, "A")


class TestSelectExpressionWithNumbers(unittest.TestCase):

    def setUp(self):
        self.ctx = FluentBundle(['en-US'], use_isolating=False)
        self.ctx.add_messages(dedent_ftl("""
            foo = { 1 ->
               *[0] A
                [1] B
             }

            bar = { 2 ->
               *[0] A
                [1] B
             }

            baz = { $num ->
               *[0] A
                [1] B
             }

            qux = { 1.0 ->
               *[0] A
                [1] B
             }
        """))

    def test_selects_the_right_variant(self):
        val, errs = self.ctx.format('foo', {})
        self.assertEqual(val, "B")
        self.assertEqual(len(errs), 0)

    def test_with_a_non_matching_selector(self):
        val, errs = self.ctx.format('bar', {})
        self.assertEqual(val, "A")
        self.assertEqual(len(errs), 0)

    def test_with_a_missing_selector(self):
        val, errs = self.ctx.format('baz', {})
        self.assertEqual(val, "A")
        self.assertEqual(errs,
                         [FluentReferenceError("Unknown external: num")])

    def test_with_argument_int(self):
        val, errs = self.ctx.format('baz', {'num': 1})
        self.assertEqual(val, "B")

    def test_with_argument_float(self):
        val, errs = self.ctx.format('baz', {'num': 1.0})
        self.assertEqual(val, "B")

    def test_with_float(self):
        val, errs = self.ctx.format('qux', {})
        self.assertEqual(val, "B")


class TestSelectExpressionWithPluralCategories(unittest.TestCase):

    def setUp(self):
        self.ctx = FluentBundle(['en-US'], use_isolating=False)
        self.ctx.add_messages(dedent_ftl("""
            foo = { 1 ->
                [one] A
               *[other] B
             }

            bar = { 1 ->
                [1] A
               *[other] B
             }

            baz = { "not a number" ->
                [one] A
               *[other] B
             }

            qux = { $num ->
                [one] A
               *[other] B
             }
        """))

    def test_selects_the_right_category(self):
        val, errs = self.ctx.format('foo', {})
        self.assertEqual(val, "A")
        self.assertEqual(len(errs), 0)

    def test_selects_exact_match(self):
        val, errs = self.ctx.format('bar', {})
        self.assertEqual(val, "A")
        self.assertEqual(len(errs), 0)

    def test_selects_default_with_invalid_selector(self):
        val, errs = self.ctx.format('baz', {})
        self.assertEqual(val, "B")
        self.assertEqual(len(errs), 0)

    def test_with_a_missing_selector(self):
        val, errs = self.ctx.format('qux', {})
        self.assertEqual(val, "B")
        self.assertEqual(errs,
                         [FluentReferenceError("Unknown external: num")])

    def test_with_argument(self):
        val, errs = self.ctx.format('qux', {'num': 1})
        self.assertEqual(val, "A")
        self.assertEqual(len(errs), 0)

        val, errs = self.ctx.format('qux', {'num': 2})
        self.assertEqual(val, "B")
        self.assertEqual(len(errs), 0)
