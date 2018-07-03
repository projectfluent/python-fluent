from __future__ import absolute_import, unicode_literals

import unittest

import six

from .. import all_message_context_implementations
from ..syntax import dedent_ftl


@all_message_context_implementations
class TestSimpleStringValue(unittest.TestCase):
    def setUp(self):
        self.ctx = self.message_context_cls(['en-US'], use_isolating=False)
        self.ctx.add_messages(dedent_ftl("""
            foo               = Foo
            placeable-literal = { "Foo" } Bar
            placeable-message = { foo } Bar
            selector-literal = { "Foo" ->
               *[Foo] Member 1
             }
            bar
                .attr = Bar Attribute
            placeable-attr   = { bar.attr }
            -baz = Baz
                .attr = Baz Attribute
            selector-attr    = { -baz.attr ->
               *[Baz Attribute] Member 3
             }
        """))

    def test_can_be_used_as_a_value(self):
        val, errs = self.ctx.format('foo', {})
        self.assertEqual(val, 'Foo')
        self.assertEqual(type(val), six.text_type)
        self.assertEqual(len(errs), 0)

    def test_can_be_used_in_a_placeable(self):
        val, errs = self.ctx.format('placeable-literal', {})
        self.assertEqual(val, 'Foo Bar')
        self.assertEqual(len(errs), 0)

    def test_can_be_a_value_of_a_message_referenced_in_a_placeable(self):
        val, errs = self.ctx.format('placeable-message', {})
        self.assertEqual(val, 'Foo Bar')
        self.assertEqual(len(errs), 0)

    def test_can_be_a_selector(self):
        val, errs = self.ctx.format('selector-literal', {})
        self.assertEqual(val, 'Member 1')
        self.assertEqual(len(errs), 0)

    def test_can_be_used_as_an_attribute_value(self):
        val, errs = self.ctx.format('bar.attr', {})
        self.assertEqual(val, 'Bar Attribute')
        self.assertEqual(len(errs), 0)

    def test_can_be_a_value_of_an_attribute_used_in_a_placeable(self):
        val, errs = self.ctx.format('placeable-attr', {})
        self.assertEqual(val, 'Bar Attribute')
        self.assertEqual(len(errs), 0)

    def test_can_be_a_value_of_an_attribute_used_as_a_selector(self):
        val, errs = self.ctx.format('selector-attr', {})
        self.assertEqual(val, 'Member 3')
        self.assertEqual(len(errs), 0)


@all_message_context_implementations
class TestComplexStringValue(unittest.TestCase):
    def setUp(self):
        self.ctx = self.message_context_cls(['en-US'], use_isolating=False)
        self.ctx.add_messages(dedent_ftl("""
            foo               = Foo
            bar               = { foo } Bar

            placeable-message = { bar } Baz

            baz
                .attr = { bar } Baz Attribute

            placeable-attr = { baz.attr }

            selector-attr = { baz.attr ->
                [Foo Bar Baz Attribute] Variant
               *[ok] Valid
             }
        """))

    def test_can_be_used_as_a_value(self):
        val, errs = self.ctx.format('bar', {})
        self.assertEqual(val, 'Foo Bar')
        self.assertEqual(len(errs), 0)

    def test_can_be_value_of_a_message_referenced_in_a_placeable(self):
        val, errs = self.ctx.format('placeable-message', {})
        self.assertEqual(val, 'Foo Bar Baz')
        self.assertEqual(len(errs), 0)

    def test_can_be_used_as_an_attribute_value(self):
        val, errs = self.ctx.format('baz.attr', {})
        self.assertEqual(val, 'Foo Bar Baz Attribute')
        self.assertEqual(len(errs), 0)

    def test_can_be_a_value_of_an_attribute_used_in_a_placeable(self):
        val, errs = self.ctx.format('placeable-attr', {})
        self.assertEqual(val, 'Foo Bar Baz Attribute')
        self.assertEqual(len(errs), 0)

    @unittest.skip("For future FTL spec")
    def test_can_be_a_value_of_an_attribute_used_as_a_selector(self):
        val, errs = self.ctx.format('selector-attr', {})
        self.assertEqual(val, 'Variant 2')
        self.assertEqual(len(errs), 0)


@all_message_context_implementations
class TestNumbers(unittest.TestCase):
    def setUp(self):
        self.ctx = self.message_context_cls(['en-US'], use_isolating=False)
        self.ctx.add_messages(dedent_ftl("""
            one           =  { 1 }
            one_point_two =  { 1.2 }
            select        =  { 1 ->
               *[0] Zero
                [1] One
             }
        """))

    def test_int_number_used_in_placeable(self):
        val, errs = self.ctx.format('one', {})
        self.assertEqual(val, '1')
        self.assertEqual(len(errs), 0)

    def test_float_number_used_in_placeable(self):
        val, errs = self.ctx.format('one_point_two', {})
        self.assertEqual(val, '1.2')
        self.assertEqual(len(errs), 0)

    def test_can_be_used_as_a_selector(self):
        val, errs = self.ctx.format('select', {})
        self.assertEqual(val, 'One')
        self.assertEqual(len(errs), 0)