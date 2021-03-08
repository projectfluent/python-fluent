import unittest

from fluent.runtime import FluentBundle, FluentResource
from fluent.runtime.errors import FluentReferenceError

from ..utils import dedent_ftl


class TestSelectExpressionWithStrings(unittest.TestCase):

    def setUp(self):
        self.bundle = FluentBundle(['en-US'], use_isolating=False)

    def test_with_a_matching_selector(self):
        self.bundle.add_resource(FluentResource(dedent_ftl("""
            foo = { "a" ->
                [a] A
               *[b] B
             }
        """)))
        val, errs = self.bundle.format_pattern(self.bundle.get_message('foo').value, {})
        self.assertEqual(val, "A")
        self.assertEqual(len(errs), 0)

    def test_with_a_non_matching_selector(self):
        self.bundle.add_resource(FluentResource(dedent_ftl("""
            foo = { "c" ->
                [a] A
               *[b] B
             }
        """)))
        val, errs = self.bundle.format_pattern(self.bundle.get_message('foo').value, {})
        self.assertEqual(val, "B")
        self.assertEqual(len(errs), 0)

    def test_with_a_missing_selector(self):
        self.bundle.add_resource(FluentResource(dedent_ftl("""
            foo = { $none ->
                [a] A
               *[b] B
             }
        """)))
        val, errs = self.bundle.format_pattern(self.bundle.get_message('foo').value, {})
        self.assertEqual(val, "B")
        self.assertEqual(errs,
                         [FluentReferenceError("Unknown external: none")])

    def test_with_argument_expression(self):
        self.bundle.add_resource(FluentResource(dedent_ftl("""
            foo = { $arg ->
                [a] A
               *[b] B
             }
        """)))
        val, errs = self.bundle.format_pattern(self.bundle.get_message('foo').value, {'arg': 'a'})
        self.assertEqual(val, "A")


class TestSelectExpressionWithNumbers(unittest.TestCase):

    def setUp(self):
        self.bundle = FluentBundle(['en-US'], use_isolating=False)
        self.bundle.add_resource(FluentResource(dedent_ftl("""
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
        """)))

    def test_selects_the_right_variant(self):
        val, errs = self.bundle.format_pattern(self.bundle.get_message('foo').value, {})
        self.assertEqual(val, "B")
        self.assertEqual(len(errs), 0)

    def test_with_a_non_matching_selector(self):
        val, errs = self.bundle.format_pattern(self.bundle.get_message('bar').value, {})
        self.assertEqual(val, "A")
        self.assertEqual(len(errs), 0)

    def test_with_a_missing_selector(self):
        val, errs = self.bundle.format_pattern(self.bundle.get_message('baz').value, {})
        self.assertEqual(val, "A")
        self.assertEqual(errs,
                         [FluentReferenceError("Unknown external: num")])

    def test_with_argument_int(self):
        val, errs = self.bundle.format_pattern(self.bundle.get_message('baz').value, {'num': 1})
        self.assertEqual(val, "B")

    def test_with_argument_float(self):
        val, errs = self.bundle.format_pattern(self.bundle.get_message('baz').value, {'num': 1.0})
        self.assertEqual(val, "B")

    def test_with_float(self):
        val, errs = self.bundle.format_pattern(self.bundle.get_message('qux').value, {})
        self.assertEqual(val, "B")


class TestSelectExpressionWithPluralCategories(unittest.TestCase):

    def setUp(self):
        self.bundle = FluentBundle(['en-US'], use_isolating=False)
        self.bundle.add_resource(FluentResource(dedent_ftl("""
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
        """)))

    def test_selects_the_right_category(self):
        val, errs = self.bundle.format_pattern(self.bundle.get_message('foo').value, {})
        self.assertEqual(val, "A")
        self.assertEqual(len(errs), 0)

    def test_selects_exact_match(self):
        val, errs = self.bundle.format_pattern(self.bundle.get_message('bar').value, {})
        self.assertEqual(val, "A")
        self.assertEqual(len(errs), 0)

    def test_selects_default_with_invalid_selector(self):
        val, errs = self.bundle.format_pattern(self.bundle.get_message('baz').value, {})
        self.assertEqual(val, "B")
        self.assertEqual(len(errs), 0)

    def test_with_a_missing_selector(self):
        val, errs = self.bundle.format_pattern(self.bundle.get_message('qux').value, {})
        self.assertEqual(val, "B")
        self.assertEqual(errs,
                         [FluentReferenceError("Unknown external: num")])

    def test_with_argument_integer(self):
        val, errs = self.bundle.format_pattern(self.bundle.get_message('qux').value, {'num': 1})
        self.assertEqual(val, "A")
        self.assertEqual(len(errs), 0)

        val, errs = self.bundle.format_pattern(self.bundle.get_message('qux').value, {'num': 2})
        self.assertEqual(val, "B")
        self.assertEqual(len(errs), 0)

    def test_with_argument_float(self):
        val, errs = self.bundle.format_pattern(self.bundle.get_message('qux').value, {'num': 1.0})
        self.assertEqual(val, "A")
        self.assertEqual(len(errs), 0)


class TestSelectExpressionWithTerms(unittest.TestCase):

    def setUp(self):
        self.bundle = FluentBundle(['en-US'], use_isolating=False)
        self.bundle.add_resource(FluentResource(dedent_ftl("""
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
        """)))

    def test_ref_term_attribute(self):
        val, errs = self.bundle.format_pattern(self.bundle.get_message('ref-term-attr').value)
        self.assertEqual(val, "Term Attribute")
        self.assertEqual(len(errs), 0)

    def test_ref_term_attribute_fallback(self):
        val, errs = self.bundle.format_pattern(self.bundle.get_message('ref-term-attr-other').value)
        self.assertEqual(val, "Other")
        self.assertEqual(len(errs), 0)

    def test_ref_term_attribute_missing(self):
        val, errs = self.bundle.format_pattern(self.bundle.get_message('ref-term-attr-missing').value)
        self.assertEqual(val, "Other")
        self.assertEqual(len(errs), 1)
        self.assertEqual(errs,
                         [FluentReferenceError('Unknown attribute: -my-term.missing')])
