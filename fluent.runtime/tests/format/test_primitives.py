import unittest

from fluent.runtime import FluentBundle, FluentResource

from ..utils import dedent_ftl


class TestSimpleStringValue(unittest.TestCase):
    def setUp(self):
        self.bundle = FluentBundle(['en-US'], use_isolating=False)
        self.bundle.add_resource(FluentResource(dedent_ftl(r"""
            foo               = Foo
            placeable-literal = { "Foo" } Bar
            placeable-message = { foo } Bar
            selector-literal = { "Foo" ->
                [Foo] Member 1
               *[Bar] Member 2
             }
            bar =
                .attr = Bar Attribute
            placeable-attr   = { bar.attr }
            -baz = Baz
                .attr = BazAttribute
            selector-attr    = { -baz.attr ->
                [BazAttribute] Member 3
               *[other]        Member 4
             }
            escapes = {"    "}stuff{"\u0258}\"\\end"}
        """)))

    def test_can_be_used_as_a_value(self):
        val, errs = self.bundle.format_pattern(self.bundle.get_message('foo').value, {})
        self.assertEqual(val, 'Foo')
        self.assertEqual(len(errs), 0)

    def test_can_be_used_in_a_placeable(self):
        val, errs = self.bundle.format_pattern(self.bundle.get_message('placeable-literal').value, {})
        self.assertEqual(val, 'Foo Bar')
        self.assertEqual(len(errs), 0)

    def test_can_be_a_value_of_a_message_referenced_in_a_placeable(self):
        val, errs = self.bundle.format_pattern(self.bundle.get_message('placeable-message').value, {})
        self.assertEqual(val, 'Foo Bar')
        self.assertEqual(len(errs), 0)

    def test_can_be_a_selector(self):
        val, errs = self.bundle.format_pattern(self.bundle.get_message('selector-literal').value, {})
        self.assertEqual(val, 'Member 1')
        self.assertEqual(len(errs), 0)

    def test_can_be_used_as_an_attribute_value(self):
        val, errs = self.bundle.format_pattern(self.bundle.get_message('bar').attributes['attr'], {})
        self.assertEqual(val, 'Bar Attribute')
        self.assertEqual(len(errs), 0)

    def test_can_be_a_value_of_an_attribute_used_in_a_placeable(self):
        val, errs = self.bundle.format_pattern(self.bundle.get_message('placeable-attr').value, {})
        self.assertEqual(val, 'Bar Attribute')
        self.assertEqual(len(errs), 0)

    def test_can_be_a_value_of_an_attribute_used_as_a_selector(self):
        val, errs = self.bundle.format_pattern(self.bundle.get_message('selector-attr').value, {})
        self.assertEqual(val, 'Member 3')
        self.assertEqual(len(errs), 0)

    def test_escapes(self):
        val, errs = self.bundle.format_pattern(self.bundle.get_message('escapes').value, {})
        self.assertEqual(val, r'    stuffɘ}"\end')
        self.assertEqual(len(errs), 0)


class TestComplexStringValue(unittest.TestCase):
    def setUp(self):
        self.bundle = FluentBundle(['en-US'], use_isolating=False)
        self.bundle.add_resource(FluentResource(dedent_ftl("""
            foo               = Foo
            bar               = { foo }Bar

            placeable-message = { bar }Baz

            baz =
                .attr = { bar }BazAttribute

            -qux = Qux
                .attr = { bar }QuxAttribute

            placeable-attr = { baz.attr }

            selector-attr = { -qux.attr ->
                [FooBarQuxAttribute] FooBarQux
               *[other] Other
             }
        """)))

    def test_can_be_used_as_a_value(self):
        val, errs = self.bundle.format_pattern(self.bundle.get_message('bar').value, {})
        self.assertEqual(val, 'FooBar')
        self.assertEqual(len(errs), 0)

    def test_can_be_value_of_a_message_referenced_in_a_placeable(self):
        val, errs = self.bundle.format_pattern(self.bundle.get_message('placeable-message').value, {})
        self.assertEqual(val, 'FooBarBaz')
        self.assertEqual(len(errs), 0)

    def test_can_be_used_as_an_attribute_value(self):
        val, errs = self.bundle.format_pattern(self.bundle.get_message('baz').attributes['attr'], {})
        self.assertEqual(val, 'FooBarBazAttribute')
        self.assertEqual(len(errs), 0)

    def test_can_be_a_value_of_an_attribute_used_in_a_placeable(self):
        val, errs = self.bundle.format_pattern(self.bundle.get_message('placeable-attr').value, {})
        self.assertEqual(val, 'FooBarBazAttribute')
        self.assertEqual(len(errs), 0)

    def test_can_be_a_value_of_an_attribute_used_as_a_selector(self):
        val, errs = self.bundle.format_pattern(self.bundle.get_message('selector-attr').value, {})
        self.assertEqual(val, 'FooBarQux')
        self.assertEqual(len(errs), 0)


class TestNumbers(unittest.TestCase):
    def setUp(self):
        self.bundle = FluentBundle(['en-US'], use_isolating=False)
        self.bundle.add_resource(FluentResource(dedent_ftl("""
            one           =  { 1 }
            one_point_two =  { 1.2 }
            select        =  { 1 ->
               *[0] Zero
                [1] One
             }
        """)))

    def test_int_number_used_in_placeable(self):
        val, errs = self.bundle.format_pattern(self.bundle.get_message('one').value, {})
        self.assertEqual(val, '1')
        self.assertEqual(len(errs), 0)

    def test_float_number_used_in_placeable(self):
        val, errs = self.bundle.format_pattern(self.bundle.get_message('one_point_two').value, {})
        self.assertEqual(val, '1.2')
        self.assertEqual(len(errs), 0)

    def test_can_be_used_as_a_selector(self):
        val, errs = self.bundle.format_pattern(self.bundle.get_message('select').value, {})
        self.assertEqual(val, 'One')
        self.assertEqual(len(errs), 0)
