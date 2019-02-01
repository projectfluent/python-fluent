# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import unittest

from fluent.runtime import FluentBundle

from .utils import dedent_ftl


class TestFluentBundle(unittest.TestCase):
    def setUp(self):
        self.ctx = FluentBundle(['en-US'])

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
        """))

        self.assertTrue(self.ctx.has_message('foo'))
        self.assertFalse(self.ctx.has_message('bar'))

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
        ctx = FluentBundle(['en-US'])
        self.assertEqual(ctx._plural_form(0),
                         'other')
        self.assertEqual(ctx._plural_form(1),
                         'one')
        self.assertEqual(ctx._plural_form(2),
                         'other')

    def test_plural_form_english_floats(self):
        ctx = FluentBundle(['en-US'])
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
        ctx = FluentBundle(['fr'])
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
