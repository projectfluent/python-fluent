from __future__ import absolute_import, unicode_literals

import unittest

from fluent.runtime.errors import FluentReferenceError

from .. import all_fluent_bundle_implementations
from ..utils import dedent_ftl


@all_fluent_bundle_implementations
class TestSelectExpressionWithStrings(unittest.TestCase):

    def setUp(self):
        self.ctx = self.fluent_bundle_cls(['en-US'], use_isolating=False)

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

    def test_string_selector_with_plural_categories(self):
        self.ctx.add_messages(dedent_ftl("""
            foo = { $arg ->
                [something] A
               *[other] B
             }
        """))
        # Even though 'other' matches a CLDR plural, this is not a plural
        # category match, and should work without errors when we pass
        # a string.

        val, errs = self.ctx.format('foo', {'arg': 'something'})
        self.assertEqual(val, "A")
        self.assertEqual(errs, [])

        val2, errs2 = self.ctx.format('foo', {'arg': 'other'})
        self.assertEqual(val2, "B")
        self.assertEqual(errs2, [])

        val3, errs3 = self.ctx.format('foo', {'arg': 'not listed'})
        self.assertEqual(val3, "B")
        self.assertEqual(errs3, [])


@all_fluent_bundle_implementations
class TestSelectExpressionWithNumbers(unittest.TestCase):

    def setUp(self):
        self.ctx = self.fluent_bundle_cls(['en-US'], use_isolating=False)
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


@all_fluent_bundle_implementations
class TestSelectExpressionWithPluralCategories(unittest.TestCase):

    def setUp(self):
        self.ctx = self.fluent_bundle_cls(['en-US'], use_isolating=False)
        self.ctx.add_messages(dedent_ftl("""
            foo = { 1 ->
                [one] A
               *[other] B
             }

            foo-arg = { $count ->
                [one] A
               *[other] B
             }

            bar = { 1 ->
                [1] A
               *[other] B
             }

            bar-arg = { $count ->
                [1] A
               *[other] B
             }

            baz = { "not a number" ->
                [one] A
               *[other] B
             }

            baz-arg = { $count ->
                [one] A
               *[other] B
             }

            qux = { 1.0 ->
                [1] A
               *[other] B
             }

        """))

    def test_selects_the_right_category_with_integer_static(self):
        val, errs = self.ctx.format('foo', {})
        self.assertEqual(val, "A")
        self.assertEqual(len(errs), 0)

    def test_selects_the_right_category_with_integer_runtime(self):
        val, errs = self.ctx.format('foo-arg', {'count': 1})
        self.assertEqual(val, "A")
        self.assertEqual(errs, [])

        val, errs = self.ctx.format('foo-arg', {'count': 2})
        self.assertEqual(val, "B")
        self.assertEqual(errs, [])

    def test_selects_the_right_category_with_float_static(self):
        val, errs = self.ctx.format('qux', {})
        self.assertEqual(val, "A")
        self.assertEqual(len(errs), 0)

    def test_selects_the_right_category_with_float_runtime(self):
        val, errs = self.ctx.format('foo-arg', {'count': 1.0})
        self.assertEqual(val, "A")
        self.assertEqual(len(errs), 0)

    def test_selects_exact_match_static(self):
        val, errs = self.ctx.format('bar', {})
        self.assertEqual(val, "A")
        self.assertEqual(len(errs), 0)

    def test_selects_exact_match_runtime(self):
        val, errs = self.ctx.format('bar-arg', {'count': 1})
        self.assertEqual(val, "A")
        self.assertEqual(len(errs), 0)

    def test_selects_default_with_invalid_selector_static(self):
        val, errs = self.ctx.format('baz', {})
        self.assertEqual(val, "B")
        self.assertEqual(len(errs), 0)

    def test_selects_default_with_invalid_selector_runtime(self):
        val, errs = self.ctx.format('baz-arg', {'count': 'not a number'})
        self.assertEqual(val, "B")
        self.assertEqual(len(errs), 0)

    def test_with_a_missing_selector(self):
        val, errs = self.ctx.format('foo-arg', {})
        self.assertEqual(val, "B")
        self.assertEqual(errs,
                         [FluentReferenceError("Unknown external: count")])


@all_fluent_bundle_implementations
class TestSelectExpressionWithTerms(unittest.TestCase):

    def setUp(self):
        self.ctx = self.fluent_bundle_cls(['en-US'], use_isolating=False)
        self.ctx.add_messages(dedent_ftl("""
            -my-term = term
                 .attr = termattribute

            ref-term-attr = { -my-term.attr ->
                    [termattribute]   Term Attribute
                   *[other]           Other
            }

            ref-term-attr-other = { -my-term.attr ->
                    [x]      Term Attribute
                   *[other]  Other
            }

            ref-term-attr-missing = { -my-term.missing ->
                    [x]      Term Attribute
                   *[other]  Other
            }
        """))

    def test_ref_term_attribute(self):
        val, errs = self.ctx.format('ref-term-attr')
        self.assertEqual(val, "Term Attribute")
        self.assertEqual(len(errs), 0)

    def test_ref_term_attribute_fallback(self):
        val, errs = self.ctx.format('ref-term-attr-other')
        self.assertEqual(val, "Other")
        self.assertEqual(len(errs), 0)

    def test_ref_term_attribute_missing(self):
        val, errs = self.ctx.format('ref-term-attr-missing')
        self.assertEqual(val, "Other")
        self.assertEqual(len(errs), 1)
        self.assertEqual(errs,
                         [FluentReferenceError('Unknown attribute: -my-term.missing')])
