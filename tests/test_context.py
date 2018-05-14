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
