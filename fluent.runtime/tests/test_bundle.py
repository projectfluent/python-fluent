# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import unittest

from fluent.runtime.errors import FluentDuplicateMessageId, FluentJunkFound, FluentReferenceError

from . import all_fluent_bundle_implementations
from .utils import dedent_ftl


@all_fluent_bundle_implementations
class TestFluentBundle(unittest.TestCase):
    def setUp(self):
        self.ctx = self.fluent_bundle_cls(['en-US'])

    def test_add_messages(self):
        self.ctx.add_messages(dedent_ftl("""
            foo = Foo
            bar = Bar
            -baz = Baz
        """))
        self.assertIn('foo', self.ctx._messages_and_terms)
        self.assertIn('bar', self.ctx._messages_and_terms)
        self.assertIn('-baz', self.ctx._messages_and_terms)

    def test_has_message(self):
        self.ctx.add_messages(dedent_ftl("""
            foo = Foo
            -term = Term
        """))

        self.assertTrue(self.ctx.has_message('foo'))
        self.assertFalse(self.ctx.has_message('bar'))
        self.assertFalse(self.ctx.has_message('-term'))

    def test_has_message_for_term(self):
        self.ctx.add_messages(dedent_ftl("""
            -foo = Foo
        """))

        self.assertFalse(self.ctx.has_message('-foo'))

    def test_has_message_with_attribute(self):
        self.ctx.add_messages(dedent_ftl("""
            foo = Foo
                .attr = Foo Attribute
        """))

        self.assertTrue(self.ctx.has_message('foo'))
        self.assertFalse(self.ctx.has_message('foo.attr'))
        self.assertFalse(self.ctx.has_message('foo.other-attribute'))

    def test_plural_form_english_ints(self):
        ctx = self.fluent_bundle_cls(['en-US'])
        self.assertEqual(ctx._plural_form(0),
                         'other')
        self.assertEqual(ctx._plural_form(1),
                         'one')
        self.assertEqual(ctx._plural_form(2),
                         'other')

    def test_plural_form_english_floats(self):
        ctx = self.fluent_bundle_cls(['en-US'])
        self.assertEqual(ctx._plural_form(0.0),
                         'other')
        self.assertEqual(ctx._plural_form(1.0),
                         'one')
        self.assertEqual(ctx._plural_form(2.0),
                         'other')
        self.assertEqual(ctx._plural_form(0.5),
                         'other')

    def test_plural_form_french(self):
        # Just spot check one other, to ensure that we
        # are not getting the EN locale by accident or
        ctx = self.fluent_bundle_cls(['fr'])
        self.assertEqual(ctx._plural_form(0),
                         'one')
        self.assertEqual(ctx._plural_form(1),
                         'one')
        self.assertEqual(ctx._plural_form(2),
                         'other')

    def test_format_args(self):
        self.ctx.add_messages('foo = Foo')
        val, errs = self.ctx.format('foo')
        self.assertEqual(val, 'Foo')

        val, errs = self.ctx.format('foo', {})
        self.assertEqual(val, 'Foo')

    def test_format_missing(self):
        self.assertRaises(LookupError,
                          self.ctx.format,
                          'a-missing-message')

    def test_format_term(self):
        self.ctx.add_messages(dedent_ftl("""
            -foo = Foo
        """))
        self.assertRaises(LookupError,
                          self.ctx.format,
                          '-foo')
        self.assertRaises(LookupError,
                          self.ctx.format,
                          'foo')

    def test_message_and_term_separate(self):
        self.ctx.add_messages(dedent_ftl("""
            foo = Refers to { -foo }
            -foo = Foo
        """))
        val, errs = self.ctx.format('foo', {})
        self.assertEqual(val, 'Refers to \u2068Foo\u2069')
        self.assertEqual(errs, [])

    def test_check_messages_duplicate(self):
        self.ctx.add_messages("foo = Foo\n"
                              "foo = Bar\n")
        checks = self.ctx.check_messages()
        self.assertEqual(checks,
                         [('foo', FluentDuplicateMessageId("Additional definition for 'foo' discarded."))])
        # Earlier takes precedence
        self.assertEqual(self.ctx.format('foo')[0], 'Foo')

    def test_check_messages_junk(self):
        self.ctx.add_messages("unfinished")
        checks = self.ctx.check_messages()
        self.assertEqual(len(checks), 1)
        check1_name, check1_error = checks[0]
        self.assertEqual(check1_name, None)
        self.assertEqual(type(check1_error), FluentJunkFound)
        self.assertEqual(check1_error.message, 'Junk found: Expected message "unfinished" to have a value or attributes')
        self.assertEqual(check1_error.annotations[0].message, 'Expected message "unfinished" to have a value or attributes')

    def test_check_messages_compile_errors(self):
        self.ctx.add_messages("foo = { -missing }")
        checks = self.ctx.check_messages()
        if self.ctx.__class__.__name__ == "CompilingFluentBundle":
            # CompilingFluentBundle is able to do more static checks.
            self.assertEqual(len(checks), 1)
            check1_name, check1_error = checks[0]
            self.assertEqual(check1_name, 'foo')
            self.assertEqual(type(check1_error), FluentReferenceError)
            self.assertEqual(check1_error.args[0], 'Unknown term: -missing')
        else:
            self.assertEqual(len(checks), 0)
