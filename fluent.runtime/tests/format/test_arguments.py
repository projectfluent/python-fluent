from __future__ import absolute_import, unicode_literals

import unittest

from fluent.runtime import FluentBundle, FluentResource

from ..utils import dedent_ftl


class TestNumbersInValues(unittest.TestCase):
    def setUp(self):
        self.ctx = FluentBundle(['en-US'], use_isolating=False)
        self.ctx.add_resource(FluentResource(dedent_ftl("""
            foo = Foo { $num }
            bar = { foo }
            baz =
                .attr = Baz Attribute { $num }
            qux = { "a" ->
               *[a]     Baz Variant A { $num }
             }
        """)))

    def test_can_be_used_in_the_message_value(self):
        val, errs = self.ctx.format('foo', {'num': 3})
        self.assertEqual(val, 'Foo 3')
        self.assertEqual(len(errs), 0)

    def test_can_be_used_in_the_message_value_which_is_referenced(self):
        val, errs = self.ctx.format('bar', {'num': 3})
        self.assertEqual(val, 'Foo 3')
        self.assertEqual(len(errs), 0)

    def test_can_be_used_in_an_attribute(self):
        val, errs = self.ctx.format('baz.attr', {'num': 3})
        self.assertEqual(val, 'Baz Attribute 3')
        self.assertEqual(len(errs), 0)

    def test_can_be_used_in_a_variant(self):
        val, errs = self.ctx.format('qux', {'num': 3})
        self.assertEqual(val, 'Baz Variant A 3')
        self.assertEqual(len(errs), 0)


class TestStrings(unittest.TestCase):
    def setUp(self):
        self.ctx = FluentBundle(['en-US'], use_isolating=False)
        self.ctx.add_resource(FluentResource(dedent_ftl("""
            foo = { $arg }
        """)))

    def test_can_be_a_string(self):
        val, errs = self.ctx.format('foo', {'arg': 'Argument'})
        self.assertEqual(val, 'Argument')
        self.assertEqual(len(errs), 0)
