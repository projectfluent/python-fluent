from __future__ import absolute_import, unicode_literals

import unittest

from fluent.context import MessageContext

from ..syntax import dedent_ftl


class TestSimpleStringValue(unittest.TestCase):
    def setUp(self):
        self.ctx = MessageContext(['en-US'], use_isolating=False)
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
        self.assertEqual(len(errs), 0)

    def test_can_be_used_in_a_placeable(self):
        val, errs = self.ctx.format('placeable-literal', {})
        self.assertEqual(val, 'Foo Bar')
        self.assertEqual(len(errs), 0)

    def test_can_be_a_value_of_a_message_referenced_in_a_placeable(self):
        val, errs = self.ctx.format('placeable-message', {})
        self.assertEqual(val, 'Foo Bar')
        self.assertEqual(len(errs), 0)

    # TODO - the rest of tests from
    # https://github.com/projectfluent/fluent.js/blob/master/fluent/test/primitives_test.js
