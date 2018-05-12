from __future__ import absolute_import, unicode_literals

import unittest

from fluent.context import MessageContext

from ..syntax import dedent_ftl


class TestNumbersInValues(unittest.TestCase):
    def setUp(self):
        self.ctx = MessageContext(['en-US'], use_isolating=False)
        self.ctx.add_messages(dedent_ftl("""
            foo = Foo { $num }
            bar = { foo }
            baz
                .attr = Baz Attribute { $num }
            qux = { "a" ->
               *[a]     Baz Variant A { $num }
            }
        """))

    def test_can_be_used_in_the_message_value(self):
        val, errs = self.ctx.format('foo', {'num': 3})
        self.assertEqual(val, 'Foo 3')
        self.assertEqual(len(errs), 0)

    # TODO - the rest from
    # https://github.com/projectfluent/fluent.js/blob/master/fluent/test/arguments_test.js


class TestStrings(unittest.TestCase):
    def setUp(self):
        self.ctx = MessageContext(['en-US'], use_isolating=False)
        self.ctx.add_messages(dedent_ftl("""
            foo = { $arg }
        """))

    def test_can_be_a_string(self):
        val, errs = self.ctx.format('foo', {'arg': 'Argument'})
        self.assertEqual(val, 'Argument')
        self.assertEqual(len(errs), 0)
