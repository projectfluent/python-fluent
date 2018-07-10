# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import unittest

from . import all_message_context_implementations
from .syntax import dedent_ftl


@all_message_context_implementations
class TestMessageContext(unittest.TestCase):
    def setUp(self):
        self.ctx = self.message_context_cls(['en-US'])

    def test_add_messages(self):
        self.ctx.add_messages(dedent_ftl("""
            foo = Foo
            bar = Bar
            -baz = Baz
        """))
        self.assertIn('foo', self.ctx._messages)
        self.assertIn('bar', self.ctx._messages)
        self.assertNotIn('-baz', self.ctx._messages)
        self.assertIn('-baz', self.ctx._terms)

    def test_message_ids(self):
        self.ctx.add_messages(dedent_ftl("""
            foo = Foo
            bar = Bar
            -baz = Baz
        """))
        self.assertEqual(sorted(self.ctx.message_ids()),
                         ['bar', 'foo'])

    def test_has_message(self):
        self.ctx.add_messages(dedent_ftl("""
            foo = Foo
        """))

        self.assertTrue(self.ctx.has_message('foo'))
        self.assertFalse(self.ctx.has_message('bar'))

    def test_has_message_with_attribute(self):
        self.ctx.add_messages(dedent_ftl("""
            foo = Foo
                .attr = Foo Attribute
        """))

        self.assertTrue(self.ctx.has_message('foo'))
        self.assertTrue(self.ctx.has_message('foo.attr'))
        self.assertFalse(self.ctx.has_message('foo.other-attribute'))

    def test_plural_form_english_ints(self):
        ctx = self.message_context_cls(['en-US'])
        self.assertEqual(ctx.plural_form_for_number(0),
                         'other')
        self.assertEqual(ctx.plural_form_for_number(1),
                         'one')
        self.assertEqual(ctx.plural_form_for_number(2),
                         'other')

    def test_plural_form_english_floats(self):
        ctx = self.message_context_cls(['en-US'])
        self.assertEqual(ctx.plural_form_for_number(0.0),
                         'other')
        self.assertEqual(ctx.plural_form_for_number(1.0),
                         'one')
        self.assertEqual(ctx.plural_form_for_number(2.0),
                         'other')
        self.assertEqual(ctx.plural_form_for_number(0.5),
                         'other')

    def test_plural_form_french(self):
        # Just spot check one other, to ensure that we
        # are not getting the EN locale by accident or
        ctx = self.message_context_cls(['fr'])
        self.assertEqual(ctx.plural_form_for_number(0),
                         'one')
        self.assertEqual(ctx.plural_form_for_number(1),
                         'one')
        self.assertEqual(ctx.plural_form_for_number(2),
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
