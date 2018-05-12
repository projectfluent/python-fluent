from __future__ import absolute_import, unicode_literals

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

    def test_messages(self):
        self.ctx.add_messages(dedent_ftl("""
            foo = Foo
            bar = Bar
            -baz = Baz
        """))
        self.assertEqual(sorted([i for i, m in self.ctx.messages()]),
                         ['bar', 'foo'])

    def test_has_message(self):
        self.ctx.add_messages(dedent_ftl("""
            foo = Foo
        """))

        self.assertTrue(self.ctx.has_message('foo'))
        self.assertFalse(self.ctx.has_message('bar'))

    def test_get_message(self):
        self.ctx.add_messages(dedent_ftl("""
            foo = Foo
        """))

        self.assertIsNotNone(self.ctx.get_message('foo'))
        self.assertRaises(LookupError, lambda: self.ctx.get_message('bar'))
