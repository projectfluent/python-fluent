from __future__ import absolute_import, unicode_literals

import unittest

from fluent.context import MessageContext
from fluent.resolver import FluentReferenceError

from ..syntax import dedent_ftl


class TestAttributesWithStringValues(unittest.TestCase):

    def setUp(self):
        self.ctx = MessageContext(['en-US'], use_isolating=False)
        self.ctx.add_messages(dedent_ftl("""
            foo = Foo
                .attr = Foo Attribute
            bar = { foo } Bar
                .attr = Bar Attribute
            ref-foo = { foo.attr }
            ref-bar = { bar.attr }
        """))

    def test_can_be_referenced_for_entities_with_string_values(self):
        val, errs = self.ctx.format('ref-foo', {})
        self.assertEqual(val, 'Foo Attribute')
        self.assertEqual(len(errs), 0)

    def test_can_be_referenced_for_entities_with_pattern_values(self):
        val, errs = self.ctx.format('ref-bar', {})
        self.assertEqual(val, 'Bar Attribute')
        self.assertEqual(len(errs), 0)

    def test_can_be_formatted_directly_for_entities_with_string_values(self):
        val, errs = self.ctx.format('foo.attr', {})
        self.assertEqual(val, 'Foo Attribute')
        self.assertEqual(len(errs), 0)

    def test_can_be_formatted_directly_for_entities_with_pattern_values(self):
        val, errs = self.ctx.format('bar.attr', {})
        self.assertEqual(val, 'Bar Attribute')
        self.assertEqual(len(errs), 0)


class TestAttributesWithSimplePatternValues(unittest.TestCase):

    def setUp(self):
        self.ctx = MessageContext(['en-US'], use_isolating=False)
        self.ctx.add_messages(dedent_ftl("""
            foo = Foo
            bar = Bar
                .attr = { foo } Attribute
            baz = { foo } Baz
                .attr = { foo } Attribute
            qux = Qux
                .attr = { qux } Attribute
            ref-bar = { bar.attr }
            ref-baz = { baz.attr }
            ref-qux = { qux.attr }
        """))

    def test_can_be_referenced_for_entities_with_string_values(self):
        val, errs = self.ctx.format('ref-bar', {})
        self.assertEqual(val, 'Foo Attribute')
        self.assertEqual(len(errs), 0)

    def test_can_be_formatted_directly_for_entities_with_string_values(self):
        val, errs = self.ctx.format('bar.attr', {})
        self.assertEqual(val, 'Foo Attribute')
        self.assertEqual(len(errs), 0)

    def test_can_be_referenced_for_entities_with_pattern_values(self):
        val, errs = self.ctx.format('ref-baz', {})
        self.assertEqual(val, 'Foo Attribute')
        self.assertEqual(len(errs), 0)

    def test_can_be_formatted_directly_for_entities_with_pattern_values(self):
        val, errs = self.ctx.format('baz.attr', {})
        self.assertEqual(val, 'Foo Attribute')
        self.assertEqual(len(errs), 0)

    def test_works_with_self_references(self):
        val, errs = self.ctx.format('ref-qux', {})
        self.assertEqual(val, 'Qux Attribute')
        self.assertEqual(len(errs), 0)


class TestMissing(unittest.TestCase):
    def setUp(self):
        self.ctx = MessageContext(['en-US'], use_isolating=False)
        self.ctx.add_messages(dedent_ftl("""
            foo = Foo
            bar = Bar
                .attr = Bar Attribute
            baz = { foo } Baz
            qux = { foo } Qux
                .attr = Qux Attribute
            ref-foo = { foo.missing }
            ref-bar = { bar.missing }
            ref-baz = { baz.missing }
            ref-qux = { qux.missing }
        """))

    def test_falls_back_for_msg_with_string_value_and_no_attributes(self):
        val, errs = self.ctx.format('ref-foo', {})
        self.assertEqual(val, 'Foo')
        self.assertEqual(errs,
                         [FluentReferenceError(
                             'Unknown attribute: foo.missing')])

    def test_falls_back_for_msg_with_string_value_and_other_attributes(self):
        val, errs = self.ctx.format('ref-bar', {})
        self.assertEqual(val, 'Bar')
        self.assertEqual(errs,
                         [FluentReferenceError(
                             'Unknown attribute: bar.missing')])

    def test_falls_back_for_msg_with_pattern_value_and_no_attributes(self):
        val, errs = self.ctx.format('ref-baz', {})
        self.assertEqual(val, 'Foo Baz')
        self.assertEqual(errs,
                         [FluentReferenceError(
                             'Unknown attribute: baz.missing')])

    def test_falls_back_for_msg_with_pattern_value_and_other_attributes(self):
        val, errs = self.ctx.format('ref-qux', {})
        self.assertEqual(val, 'Foo Qux')
        self.assertEqual(errs,
                         [FluentReferenceError(
                             'Unknown attribute: qux.missing')])
