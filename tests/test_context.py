# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import os.path
import unittest

from fluent.context import MessageContext

from .syntax import dedent_ftl


class TestMessageContext(unittest.TestCase):
    def setUp(self):
        self.ctx = MessageContext(['en-US'])

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
        ctx = MessageContext(['en-US'])
        self.assertEqual(ctx.plural_form_for_number(0),
                         'other')
        self.assertEqual(ctx.plural_form_for_number(1),
                         'one')
        self.assertEqual(ctx.plural_form_for_number(2),
                         'other')

    def test_plural_form_english_floats(self):
        ctx = MessageContext(['en-US'])
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
        ctx = MessageContext(['fr'])
        self.assertEqual(ctx.plural_form_for_number(0),
                         'one')
        self.assertEqual(ctx.plural_form_for_number(1),
                         'one')
        self.assertEqual(ctx.plural_form_for_number(2),
                         'other')

    def test_add_messages_from_file(self):
        ctx = MessageContext(['pl'])
        ftl_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                'syntax', 'fixtures_structure', 'term.ftl')
        ctx.add_messages_from_file(ftl_file)

        # End to end test to check we actually loaded it.
        val, errs = ctx.format('update-successful', {})
        self.assertEqual(val, "Firefox został pomyślnie zaktualizowany.")
        self.assertEqual(len(errs), 0)
