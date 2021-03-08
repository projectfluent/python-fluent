import unittest

from fluent.runtime import FluentBundle, FluentResource
from fluent.runtime.errors import FluentReferenceError

from ..utils import dedent_ftl


class TestAttributesWithStringValues(unittest.TestCase):

    def setUp(self):
        self.bundle = FluentBundle(['en-US'], use_isolating=False)
        self.bundle.add_resource(FluentResource(dedent_ftl("""
            foo = Foo
                .attr = Foo Attribute
            bar = { foo } Bar
                .attr = Bar Attribute
            ref-foo = { foo.attr }
            ref-bar = { bar.attr }
        """)))

    def test_can_be_referenced_for_entities_with_string_values(self):
        val, errs = self.bundle.format_pattern(self.bundle.get_message('ref-foo').value, {})
        self.assertEqual(val, 'Foo Attribute')
        self.assertEqual(len(errs), 0)

    def test_can_be_referenced_for_entities_with_pattern_values(self):
        val, errs = self.bundle.format_pattern(self.bundle.get_message('ref-bar').value, {})
        self.assertEqual(val, 'Bar Attribute')
        self.assertEqual(len(errs), 0)

    def test_can_be_formatted_directly_for_entities_with_string_values(self):
        val, errs = self.bundle.format_pattern(self.bundle.get_message('foo').attributes['attr'], {})
        self.assertEqual(val, 'Foo Attribute')
        self.assertEqual(len(errs), 0)

    def test_can_be_formatted_directly_for_entities_with_pattern_values(self):
        val, errs = self.bundle.format_pattern(self.bundle.get_message('bar').attributes['attr'], {})
        self.assertEqual(val, 'Bar Attribute')
        self.assertEqual(len(errs), 0)


class TestAttributesWithSimplePatternValues(unittest.TestCase):

    def setUp(self):
        self.bundle = FluentBundle(['en-US'], use_isolating=False)
        self.bundle.add_resource(FluentResource(dedent_ftl("""
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
        """)))

    def test_can_be_referenced_for_entities_with_string_values(self):
        val, errs = self.bundle.format_pattern(self.bundle.get_message('ref-bar').value, {})
        self.assertEqual(val, 'Foo Attribute')
        self.assertEqual(len(errs), 0)

    def test_can_be_formatted_directly_for_entities_with_string_values(self):
        val, errs = self.bundle.format_pattern(self.bundle.get_message('bar').attributes['attr'], {})
        self.assertEqual(val, 'Foo Attribute')
        self.assertEqual(len(errs), 0)

    def test_can_be_referenced_for_entities_with_pattern_values(self):
        val, errs = self.bundle.format_pattern(self.bundle.get_message('ref-baz').value, {})
        self.assertEqual(val, 'Foo Attribute')
        self.assertEqual(len(errs), 0)

    def test_can_be_formatted_directly_for_entities_with_pattern_values(self):
        val, errs = self.bundle.format_pattern(self.bundle.get_message('baz').attributes['attr'], {})
        self.assertEqual(val, 'Foo Attribute')
        self.assertEqual(len(errs), 0)

    def test_works_with_self_references(self):
        val, errs = self.bundle.format_pattern(self.bundle.get_message('ref-qux').value, {})
        self.assertEqual(val, 'Qux Attribute')
        self.assertEqual(len(errs), 0)

    def test_works_with_self_references_direct(self):
        val, errs = self.bundle.format_pattern(self.bundle.get_message('qux').attributes['attr'], {})
        self.assertEqual(val, 'Qux Attribute')
        self.assertEqual(len(errs), 0)


class TestMissing(unittest.TestCase):
    def setUp(self):
        self.bundle = FluentBundle(['en-US'], use_isolating=False)
        self.bundle.add_resource(FluentResource(dedent_ftl("""
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
            attr-only =
                     .attr  = Attr Only Attribute
            ref-double-missing = { missing.attr }
        """)))

    def test_msg_with_string_value_and_no_attributes(self):
        val, errs = self.bundle.format_pattern(self.bundle.get_message('ref-foo').value, {})
        self.assertEqual(val, '{foo.missing}')
        self.assertEqual(errs,
                         [FluentReferenceError(
                             'Unknown attribute: foo.missing')])

    def test_msg_with_string_value_and_other_attributes(self):
        val, errs = self.bundle.format_pattern(self.bundle.get_message('ref-bar').value, {})
        self.assertEqual(val, '{bar.missing}')
        self.assertEqual(errs,
                         [FluentReferenceError(
                             'Unknown attribute: bar.missing')])

    def test_msg_with_pattern_value_and_no_attributes(self):
        val, errs = self.bundle.format_pattern(self.bundle.get_message('ref-baz').value, {})
        self.assertEqual(val, '{baz.missing}')
        self.assertEqual(errs,
                         [FluentReferenceError(
                             'Unknown attribute: baz.missing')])

    def test_msg_with_pattern_value_and_other_attributes(self):
        val, errs = self.bundle.format_pattern(self.bundle.get_message('ref-qux').value, {})
        self.assertEqual(val, '{qux.missing}')
        self.assertEqual(errs,
                         [FluentReferenceError(
                             'Unknown attribute: qux.missing')])

    def test_attr_only_attribute(self):
        val, errs = self.bundle.format_pattern(self.bundle.get_message('attr-only').attributes['attr'], {})
        self.assertEqual(val, 'Attr Only Attribute')
        self.assertEqual(len(errs), 0)

    def test_missing_message_and_attribute(self):
        val, errs = self.bundle.format_pattern(self.bundle.get_message('ref-double-missing').value, {})
        self.assertEqual(val, '{missing.attr}')
        self.assertEqual(errs, [FluentReferenceError('Unknown attribute: missing.attr')])
