from __future__ import absolute_import, unicode_literals

import unittest

from fluent.context import MessageContext

from ..syntax import dedent_ftl

# Unicode bidi isolation characters.
FSI = '\u2068'
PDI = '\u2069'


class TestUseIsolating(unittest.TestCase):

    def setUp(self):
        self.ctx = MessageContext(['en-US'])
        self.ctx.add_messages(dedent_ftl("""
            foo = Foo
            bar = { foo } Bar
            baz = { $arg } Baz
            qux = { bar } { baz }
        """))

    def test_isolates_interpolated_message_references(self):
        val, errs = self.ctx.format('bar', {})
        self.assertEqual(val, FSI + "Foo" + PDI + " Bar")
        self.assertEqual(len(errs), 0)

    def test_isolates_interpolated_string_typed_external_arguments(self):
        val, errs = self.ctx.format('baz', {'arg': 'Arg'})
        self.assertEqual(val, FSI + "Arg" + PDI + " Baz")
        self.assertEqual(len(errs), 0)

    def test_isolates_interpolated_number_typed_external_arguments(self):
        val, errs = self.ctx.format('baz', {'arg': 1})
        self.assertEqual(val, FSI + "1" + PDI + " Baz")
        self.assertEqual(len(errs), 0)

    def test_isolates_complex_interpolations(self):
        val, errs = self.ctx.format('qux', {'arg': 'Arg'})
        expected_bar = FSI + FSI + "Foo" + PDI + " Bar" + PDI
        expected_baz = FSI + FSI + "Arg" + PDI + " Baz" + PDI
        self.assertEqual(val, expected_bar + " " + expected_baz)
        self.assertEqual(len(errs), 0)


class TestSkipIsolation(unittest.TestCase):

    def setUp(self):
        self.ctx = MessageContext(['en-US'])
        self.ctx.add_messages(dedent_ftl("""
            -brand-short-name = Amaya
            foo = { -brand-short-name }
        """))

    def test_skip_isolation_if_only_one_placeable(self):
        val, errs = self.ctx.format('foo', {})
        self.assertEqual(val, 'Amaya')
        self.assertEqual(len(errs), 0)
