from __future__ import absolute_import, unicode_literals

import unittest

from fluent.context import MessageContext
from fluent.resolver import FluentReferenceError

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

            bad-message-ref = Text { not-a-message }
            bad-message-attr-ref = Text { message.not-an-attr }
            bad-term-ref = Text { -not-a-term }
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

    def test_placeable_bad_message(self):
        val, errs = self.ctx.format('bad-message-ref', {})
        self.assertEqual(val, 'Text not-a-message')
        self.assertEqual(len(errs), 1)
        self.assertEqual(
            errs,
            [FluentReferenceError("Unknown message: not-a-message")])

    def test_placeable_bad_message_attr(self):
        val, errs = self.ctx.format('bad-message-attr-ref', {})
        self.assertEqual(val, 'Text Message')
        self.assertEqual(len(errs), 1)
        self.assertEqual(
            errs,
            [FluentReferenceError("Unknown attribute: message.not-an-attr")])

    def test_placeable_bad_term(self):
        val, errs = self.ctx.format('bad-term-ref', {})
        self.assertEqual(val, 'Text -not-a-term')
        self.assertEqual(len(errs), 1)
        self.assertEqual(
            errs,
            [FluentReferenceError("Unknown term: -not-a-term")])
