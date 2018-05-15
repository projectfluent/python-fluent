from __future__ import absolute_import, unicode_literals

import unittest

from fluent.context import MessageContext

from ..syntax import dedent_ftl


class TestPlaceables(unittest.TestCase):
    def setUp(self):
        self.ctx = MessageContext(['en-US'], use_isolating=False)
        self.ctx.add_messages(dedent_ftl("""
            message = Message
                    .attr = Message Attribute
            -term = Term
                  .attr = Term Attribute
            -term2 = {
               *[variant1] Term Variant 1
                [variant2] Term Variant 2
             }

            uses-message = { message }
            uses-message-attr = { message.attr }
            uses-term = { -term }
            uses-term-variant = { -term2[variant2] }

            bad-message-ref = { not-a-message }
            bad-term-ref = { -not-a-term }
        """))

    def test_placeable_message(self):
        val, errs = self.ctx.format('uses-message', {})
        self.assertEqual(val, 'Message')
        self.assertEqual(len(errs), 0)

    def test_placeable_message_attr(self):
        val, errs = self.ctx.format('uses-message-attr', {})
        self.assertEqual(val, 'Message Attribute')
        self.assertEqual(len(errs), 0)

    def test_placeable_term(self):
        val, errs = self.ctx.format('uses-term', {})
        self.assertEqual(val, 'Term')
        self.assertEqual(len(errs), 0)

    def test_placeable_term_variant(self):
        val, errs = self.ctx.format('uses-term-variant', {})
        self.assertEqual(val, 'Term Variant 2')
        self.assertEqual(len(errs), 0)
