import unittest

from fluent.runtime import FluentBundle, FluentResource

from .utils import dedent_ftl


class TestFluentBundle(unittest.TestCase):
    def setUp(self):
        self.bundle = FluentBundle(['en-US'])

    def test_add_resource(self):
        self.bundle.add_resource(FluentResource(dedent_ftl("""
            foo = Foo
            bar = Bar
            -baz = Baz
        """)))
        self.assertIn('foo', self.bundle._messages)
        self.assertIn('bar', self.bundle._messages)
        self.assertIn('baz', self.bundle._terms)

    def test_has_message(self):
        self.bundle.add_resource(FluentResource(dedent_ftl("""
            foo = Foo
        """)))

        self.assertTrue(self.bundle.has_message('foo'))
        self.assertFalse(self.bundle.has_message('bar'))

    def test_has_message_for_term(self):
        self.bundle.add_resource(FluentResource(dedent_ftl("""
            -foo = Foo
        """)))

        self.assertFalse(self.bundle.has_message('-foo'))

    def test_has_message_with_attribute(self):
        self.bundle.add_resource(FluentResource(dedent_ftl("""
            foo = Foo
                .attr = Foo Attribute
        """)))

        self.assertTrue(self.bundle.has_message('foo'))
        self.assertFalse(self.bundle.has_message('foo.attr'))
        self.assertFalse(self.bundle.has_message('foo.other-attribute'))

    def test_plural_form_english_ints(self):
        bundle = FluentBundle(['en-US'])
        self.assertEqual(bundle._plural_form(0),
                         'other')
        self.assertEqual(bundle._plural_form(1),
                         'one')
        self.assertEqual(bundle._plural_form(2),
                         'other')

    def test_plural_form_english_floats(self):
        bundle = FluentBundle(['en-US'])
        self.assertEqual(bundle._plural_form(0.0),
                         'other')
        self.assertEqual(bundle._plural_form(1.0),
                         'one')
        self.assertEqual(bundle._plural_form(2.0),
                         'other')
        self.assertEqual(bundle._plural_form(0.5),
                         'other')

    def test_plural_form_french(self):
        # Just spot check one other, to ensure that we
        # are not getting the EN locale by accident or
        bundle = FluentBundle(['fr'])
        self.assertEqual(bundle._plural_form(0),
                         'one')
        self.assertEqual(bundle._plural_form(1),
                         'one')
        self.assertEqual(bundle._plural_form(2),
                         'other')

    def test_format_args(self):
        self.bundle.add_resource(FluentResource('foo = Foo'))
        val, errs = self.bundle.format_pattern(self.bundle.get_message('foo').value)
        self.assertEqual(val, 'Foo')

        val, errs = self.bundle.format_pattern(self.bundle.get_message('foo').value, {})
        self.assertEqual(val, 'Foo')

    def test_format_missing(self):
        self.assertRaises(LookupError,
                          self.bundle.get_message,
                          'a-missing-message')

    def test_format_term(self):
        self.bundle.add_resource(FluentResource(dedent_ftl("""
            -foo = Foo
        """)))
        self.assertRaises(LookupError,
                          self.bundle.get_message,
                          '-foo')
        self.assertRaises(LookupError,
                          self.bundle.get_message,
                          'foo')

    def test_message_and_term_separate(self):
        self.bundle.add_resource(FluentResource(dedent_ftl("""
            foo = Refers to { -foo }
            -foo = Foo
        """)))
        val, errs = self.bundle.format_pattern(self.bundle.get_message('foo').value, {})
        self.assertEqual(val, 'Refers to \u2068Foo\u2069')
        self.assertEqual(errs, [])
