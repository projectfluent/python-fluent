from __future__ import absolute_import, unicode_literals

import unittest

from fluent.context import MessageContext

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

    # TODO - "can be formatted directly" tests,
    # some kind of API for getting message attributes.


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

    def test_can_be_referenced_for_entities_with_pattern_values(self):
        val, errs = self.ctx.format('ref-baz', {})
        self.assertEqual(val, 'Foo Attribute')
        self.assertEqual(len(errs), 0)

    def test_works_with_self_references(self):
        val, errs = self.ctx.format('ref-qux', {})
        self.assertEqual(val, 'Qux Attribute')
        self.assertEqual(len(errs), 0)

    # TODO - "can be formatted directly" tests
