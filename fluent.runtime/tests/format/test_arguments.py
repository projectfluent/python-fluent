import unittest

from fluent.runtime import FluentBundle, FluentResource

from ..utils import dedent_ftl


class TestNumbersInValues(unittest.TestCase):
    def setUp(self):
        self.bundle = FluentBundle(['en-US'], use_isolating=False)
        self.bundle.add_resource(FluentResource(dedent_ftl("""
            foo = Foo { $num }
            bar = { foo }
            baz =
                .attr = Baz Attribute { $num }
            qux = { "a" ->
               *[a]     Baz Variant A { $num }
             }
        """)))

    def test_can_be_used_in_the_message_value(self):
        val, errs = self.bundle.format_pattern(self.bundle.get_message('foo').value, {'num': 3})
        self.assertEqual(val, 'Foo 3')
        self.assertEqual(len(errs), 0)

    def test_can_be_used_in_the_message_value_which_is_referenced(self):
        val, errs = self.bundle.format_pattern(self.bundle.get_message('bar').value, {'num': 3})
        self.assertEqual(val, 'Foo 3')
        self.assertEqual(len(errs), 0)

    def test_can_be_used_in_an_attribute(self):
        val, errs = self.bundle.format_pattern(self.bundle.get_message('baz').attributes['attr'], {'num': 3})
        self.assertEqual(val, 'Baz Attribute 3')
        self.assertEqual(len(errs), 0)

    def test_can_be_used_in_a_variant(self):
        val, errs = self.bundle.format_pattern(self.bundle.get_message('qux').value, {'num': 3})
        self.assertEqual(val, 'Baz Variant A 3')
        self.assertEqual(len(errs), 0)


class TestStrings(unittest.TestCase):
    def setUp(self):
        self.bundle = FluentBundle(['en-US'], use_isolating=False)
        self.bundle.add_resource(FluentResource(dedent_ftl("""
            foo = { $arg }
        """)))

    def test_can_be_a_string(self):
        val, errs = self.bundle.format_pattern(self.bundle.get_message('foo').value, {'arg': 'Argument'})
        self.assertEqual(val, 'Argument')
        self.assertEqual(len(errs), 0)
