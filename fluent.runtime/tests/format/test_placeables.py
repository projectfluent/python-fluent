import unittest

from fluent.runtime import FluentBundle, FluentResource
from fluent.runtime.errors import FluentCyclicReferenceError, FluentReferenceError

from ..utils import dedent_ftl


class TestPlaceables(unittest.TestCase):
    def setUp(self):
        self.bundle = FluentBundle(['en-US'], use_isolating=False)
        self.bundle.add_resource(FluentResource(dedent_ftl("""
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
        """)))

    def test_placeable_message(self):
        val, errs = self.bundle.format_pattern(self.bundle.get_message('uses-message').value, {})
        self.assertEqual(val, 'Message')
        self.assertEqual(len(errs), 0)

    def test_placeable_message_attr(self):
        val, errs = self.bundle.format_pattern(self.bundle.get_message('uses-message-attr').value, {})
        self.assertEqual(val, 'Message Attribute')
        self.assertEqual(len(errs), 0)

    def test_placeable_term(self):
        val, errs = self.bundle.format_pattern(self.bundle.get_message('uses-term').value, {})
        self.assertEqual(val, 'Term')
        self.assertEqual(len(errs), 0)

    def test_placeable_bad_message(self):
        val, errs = self.bundle.format_pattern(self.bundle.get_message('bad-message-ref').value, {})
        self.assertEqual(val, 'Text {not-a-message}')
        self.assertEqual(len(errs), 1)
        self.assertEqual(
            errs,
            [FluentReferenceError("Unknown message: not-a-message")])

    def test_placeable_bad_message_attr(self):
        val, errs = self.bundle.format_pattern(self.bundle.get_message('bad-message-attr-ref').value, {})
        self.assertEqual(val, 'Text {message.not-an-attr}')
        self.assertEqual(len(errs), 1)
        self.assertEqual(
            errs,
            [FluentReferenceError("Unknown attribute: message.not-an-attr")])

    def test_placeable_bad_term(self):
        val, errs = self.bundle.format_pattern(self.bundle.get_message('bad-term-ref').value, {})
        self.assertEqual(val, 'Text {-not-a-term}')
        self.assertEqual(len(errs), 1)
        self.assertEqual(
            errs,
            [FluentReferenceError("Unknown term: -not-a-term")])

    def test_cycle_detection(self):
        val, errs = self.bundle.format_pattern(self.bundle.get_message('self-referencing-message').value, {})
        self.assertEqual(val, 'Text ???')
        self.assertEqual(len(errs), 1)
        self.assertEqual(
            errs,
            [FluentCyclicReferenceError("Cyclic reference")])

    def test_mutual_cycle_detection(self):
        val, errs = self.bundle.format_pattern(self.bundle.get_message('cyclic-msg1').value, {})
        self.assertEqual(val, 'Text1 Text2 ???')
        self.assertEqual(len(errs), 1)
        self.assertEqual(
            errs,
            [FluentCyclicReferenceError("Cyclic reference")])

    def test_allowed_self_reference(self):
        val, errs = self.bundle.format_pattern(self.bundle.get_message('self-attribute-ref-ok').value, {})
        self.assertEqual(val, 'Parent Attribute')
        self.assertEqual(len(errs), 0)
        val, errs = self.bundle.format_pattern(self.bundle.get_message('self-parent-ref-ok').attributes['attr'], {})
        self.assertEqual(val, 'Attribute Parent')
        self.assertEqual(len(errs), 0)


class TestSingleElementPattern(unittest.TestCase):
    def test_single_literal_number_isolating(self):
        self.bundle = FluentBundle(['en-US'], use_isolating=True)
        self.bundle.add_resource(FluentResource('foo = { 1 }'))
        val, errs = self.bundle.format_pattern(self.bundle.get_message('foo').value)
        self.assertEqual(val, '1')
        self.assertEqual(errs, [])

    def test_single_literal_number_non_isolating(self):
        self.bundle = FluentBundle(['en-US'], use_isolating=False)
        self.bundle.add_resource(FluentResource('foo = { 1 }'))
        val, errs = self.bundle.format_pattern(self.bundle.get_message('foo').value)
        self.assertEqual(val, '1')
        self.assertEqual(errs, [])

    def test_single_arg_number_isolating(self):
        self.bundle = FluentBundle(['en-US'], use_isolating=True)
        self.bundle.add_resource(FluentResource('foo = { $arg }'))
        val, errs = self.bundle.format_pattern(self.bundle.get_message('foo').value, {'arg': 1})
        self.assertEqual(val, '1')
        self.assertEqual(errs, [])

    def test_single_arg_number_non_isolating(self):
        self.bundle = FluentBundle(['en-US'], use_isolating=False)
        self.bundle.add_resource(FluentResource('foo = { $arg }'))
        val, errs = self.bundle.format_pattern(self.bundle.get_message('foo').value, {'arg': 1})
        self.assertEqual(val, '1')
        self.assertEqual(errs, [])

    def test_single_arg_missing_isolating(self):
        self.bundle = FluentBundle(['en-US'], use_isolating=True)
        self.bundle.add_resource(FluentResource('foo = { $arg }'))
        val, errs = self.bundle.format_pattern(self.bundle.get_message('foo').value)
        self.assertEqual(val, 'arg')
        self.assertEqual(len(errs), 1)

    def test_single_arg_missing_non_isolating(self):
        self.bundle = FluentBundle(['en-US'], use_isolating=False)
        self.bundle.add_resource(FluentResource('foo = { $arg }'))
        val, errs = self.bundle.format_pattern(self.bundle.get_message('foo').value)
        self.assertEqual(val, 'arg')
        self.assertEqual(len(errs), 1)
