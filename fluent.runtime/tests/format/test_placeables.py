from __future__ import absolute_import, unicode_literals

import unittest

from fluent.runtime import FluentBundle
from fluent.runtime.errors import FluentCyclicReferenceError, FluentReferenceError

from ..utils import dedent_ftl


class TestPlaceables(unittest.TestCase):
    def setUp(self):
        self.ctx = FluentBundle(['en-US'], use_isolating=False)
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

            bad-message-ref = Text { not-a-message }
            bad-message-attr-ref = Text { message.not-an-attr }
            bad-term-ref = Text { -not-a-term }

            self-referencing-message = Text { self-referencing-message }
            cyclic-msg1 = Text1 { cyclic-msg2 }
            cyclic-msg2 = Text2 { cyclic-msg1 }
            self-cyclic-message = Parent { self-cyclic-message.attr }
                                .attr = Attribute { self-cyclic-message }

            self-attribute-ref-ok = Parent { self-attribute-ref-ok.attr }
                                  .attr = Attribute
            self-parent-ref-ok = Parent
                               .attr =  Attribute { self-parent-ref-ok }
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

    def test_cycle_detection(self):
        val, errs = self.ctx.format('self-referencing-message', {})
        self.assertEqual(val, 'Text ???')
        self.assertEqual(len(errs), 1)
        self.assertEqual(
            errs,
            [FluentCyclicReferenceError("Cyclic reference")])

    def test_mutual_cycle_detection(self):
        val, errs = self.ctx.format('cyclic-msg1', {})
        self.assertEqual(val, 'Text1 Text2 ???')
        self.assertEqual(len(errs), 1)
        self.assertEqual(
            errs,
            [FluentCyclicReferenceError("Cyclic reference")])

    def test_allowed_self_reference(self):
        val, errs = self.ctx.format('self-attribute-ref-ok', {})
        self.assertEqual(val, 'Parent Attribute')
        self.assertEqual(len(errs), 0)
        val, errs = self.ctx.format('self-parent-ref-ok.attr', {})
        self.assertEqual(val, 'Attribute Parent')
        self.assertEqual(len(errs), 0)


class TestSingleElementPattern(unittest.TestCase):
    def test_single_literal_number_isolating(self):
        self.ctx = FluentBundle(['en-US'], use_isolating=True)
        self.ctx.add_messages('foo = { 1 }')
        val, errs = self.ctx.format('foo')
        self.assertEqual(val, '1')
        self.assertEqual(errs, [])

    def test_single_literal_number_non_isolating(self):
        self.ctx = FluentBundle(['en-US'], use_isolating=False)
        self.ctx.add_messages('foo = { 1 }')
        val, errs = self.ctx.format('foo')
        self.assertEqual(val, '1')
        self.assertEqual(errs, [])

    def test_single_arg_number_isolating(self):
        self.ctx = FluentBundle(['en-US'], use_isolating=True)
        self.ctx.add_messages('foo = { $arg }')
        val, errs = self.ctx.format('foo', {'arg': 1})
        self.assertEqual(val, '1')
        self.assertEqual(errs, [])

    def test_single_arg_number_non_isolating(self):
        self.ctx = FluentBundle(['en-US'], use_isolating=False)
        self.ctx.add_messages('foo = { $arg }')
        val, errs = self.ctx.format('foo', {'arg': 1})
        self.assertEqual(val, '1')
        self.assertEqual(errs, [])

    def test_single_arg_missing_isolating(self):
        self.ctx = FluentBundle(['en-US'], use_isolating=True)
        self.ctx.add_messages('foo = { $arg }')
        val, errs = self.ctx.format('foo')
        self.assertEqual(val, 'arg')
        self.assertEqual(len(errs), 1)

    def test_single_arg_missing_non_isolating(self):
        self.ctx = FluentBundle(['en-US'], use_isolating=False)
        self.ctx.add_messages('foo = { $arg }')
        val, errs = self.ctx.format('foo')
        self.assertEqual(val, 'arg')
        self.assertEqual(len(errs), 1)
