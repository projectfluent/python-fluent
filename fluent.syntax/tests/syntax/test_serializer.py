from __future__ import unicode_literals
import unittest
import sys

sys.path.append('.')

from tests.syntax import dedent_ftl
from fluent.syntax import FluentParser, FluentSerializer
from fluent.syntax.serializer import serialize_expression, serialize_variant_key


class TestSerializeResource(unittest.TestCase):
    @staticmethod
    def pretty_ftl(text):
        parser = FluentParser()
        serializer = FluentSerializer(with_junk=False)
        res = parser.parse(dedent_ftl(text))
        return serializer.serialize(res)

    def test_invalid_resource(self):
        serializer = FluentSerializer()

        with self.assertRaisesRegexp(Exception, 'Unknown resource type'):
            serializer.serialize(None)

        with self.assertRaisesRegexp(Exception, 'Unknown resource type'):
            serializer.serialize(object())

    def test_simple_message(self):
        input = """\
            foo = Foo
        """
        self.assertEqual(self.pretty_ftl(input), dedent_ftl(input))

    def test_simple_term(self):
        input = """\
            -foo = Foo
        """
        self.assertEqual(self.pretty_ftl(input), dedent_ftl(input))

    def test_two_simple_messages(self):
        input = """\
            foo = Foo
            bar = Bar
        """
        self.assertEqual(self.pretty_ftl(input), dedent_ftl(input))

    def test_block_multiline(self):
        input = """\
            foo =
                Foo
                Bar
        """
        self.assertEqual(self.pretty_ftl(input), dedent_ftl(input))

    def test_inline_multiline(self):
        input = """\
            foo = Foo
                Bar
        """
        output = """\
            foo =
                Foo
                Bar
        """
        self.assertEqual(self.pretty_ftl(input), dedent_ftl(output))

    def test_message_reference(self):
        input = """\
            foo = Foo { bar }
        """
        self.assertEqual(self.pretty_ftl(input), dedent_ftl(input))

    def test_term_reference(self):
        input = """\
            foo = Foo { -bar }
        """
        self.assertEqual(self.pretty_ftl(input), dedent_ftl(input))

    def test_variable_reference(self):
        input = """\
            foo = Foo { $bar }
        """
        self.assertEqual(self.pretty_ftl(input), dedent_ftl(input))

    def test_number_element(self):
        input = """\
            foo = Foo { 1 }
        """
        self.assertEqual(self.pretty_ftl(input), dedent_ftl(input))

    def test_string_element(self):
        input = """\
            foo = Foo { "bar" }
        """
        self.assertEqual(self.pretty_ftl(input), dedent_ftl(input))

    def test_attribute_expression(self):
        input = """\
            foo = Foo { bar.baz }
        """
        self.assertEqual(self.pretty_ftl(input), dedent_ftl(input))

    def test_comment_resource(self):
        input = """\
            ### A multiline
            ### resource comment.

            foo = Foo
        """
        self.assertEqual(self.pretty_ftl(input), dedent_ftl(input))

    def test_comment_message(self):
        input = """\
            # A multiline
            # message comment.
            foo = Foo
        """
        self.assertEqual(self.pretty_ftl(input), dedent_ftl(input))

    def test_comment_group(self):
        input = """\
            foo = Foo

            ## Comment Header
            ##
            ## A multiline
            ## group comment.

            bar = Bar
        """
        self.assertEqual(self.pretty_ftl(input), dedent_ftl(input))

    def test_comment_standalone(self):
        input = """\
            foo = Foo

            # A multiline

            bar = Bar
        """
        self.assertEqual(self.pretty_ftl(input), dedent_ftl(input))

    def test_multiline_with_placeable(self):
        input = """\
            foo =
                Foo { bar }
                Baz
        """
        self.assertEqual(self.pretty_ftl(input), dedent_ftl(input))

    def test_attribute(self):
        input = """\
            foo =
                .attr = Foo Attr
        """
        self.assertEqual(self.pretty_ftl(input), dedent_ftl(input))

    def test_attribute_multiline(self):
        input = """\
            foo =
                .attr =
                    Foo Attr
                    Continued
        """
        self.assertEqual(self.pretty_ftl(input), dedent_ftl(input))

    def test_two_attributes(self):
        input = """\
            foo =
                .attr-a = Foo Attr A
                .attr-b = Foo Attr B
        """
        self.assertEqual(self.pretty_ftl(input), dedent_ftl(input))

    def test_value_and_attributes(self):
        input = """\
            foo = Foo Value
                .attr-a = Foo Attr A
                .attr-b = Foo Attr B
        """
        self.assertEqual(self.pretty_ftl(input), dedent_ftl(input))

    def test_multiline_value_and_attributes(self):
        input = """\
            foo =
                Foo Value
                Continued
                .attr-a = Foo Attr A
                .attr-b = Foo Attr B
        """
        self.assertEqual(self.pretty_ftl(input), dedent_ftl(input))

    def test_select_expression(self):
        input = """\
            foo =
                { $sel ->
                   *[a] A
                    [b] B
                }
        """
        self.assertEqual(self.pretty_ftl(input), dedent_ftl(input))

    def test_variant_multiline(self):
        input = """\
            foo =
                { $sel ->
                   *[a]
                        AAA
                        BBB
                }
        """
        self.assertEqual(self.pretty_ftl(input), dedent_ftl(input))

    def test_variant_multiline_first_inline(self):
        input = """\
            foo =
                { $sel ->
                   *[a] AAA
                        BBB
                }
        """
        output = """\
            foo =
                { $sel ->
                   *[a]
                        AAA
                        BBB
                }
        """
        self.assertEqual(self.pretty_ftl(input), dedent_ftl(output))

    def test_variant_key_number(self):
        input = """\
            foo =
                { $sel ->
                   *[1] 1
                }
        """
        self.assertEqual(self.pretty_ftl(input), dedent_ftl(input))

    def test_select_expression_in_block_value(self):
        input = """\
            foo =
                Foo { $sel ->
                   *[a] A
                    [b] B
                }
        """
        self.assertEqual(self.pretty_ftl(input), dedent_ftl(input))

    def test_select_expression_in_inline_value(self):
        input = """\
            foo = Foo { $sel ->
                   *[a] A
                    [b] B
                }
        """
        output = """\
            foo =
                Foo { $sel ->
                   *[a] A
                    [b] B
                }
        """
        self.assertEqual(self.pretty_ftl(input), dedent_ftl(output))

    def test_select_expression_in_multi_multiline(self):
        input = """\
            foo =
                Foo
                Bar { $sel ->
                   *[a] A
                    [b] B
                }
        """
        self.assertEqual(self.pretty_ftl(input), dedent_ftl(input))

    def test_select_expression_nested(self):
        input = """\
            foo =
                { $a ->
                   *[a]
                        { $b ->
                           *[b] Foo
                        }
                }
        """
        self.assertEqual(self.pretty_ftl(input), dedent_ftl(input))

    def test_selector_variable_reference(self):
        input = """\
            foo =
                { $bar ->
                   *[a] A
                }
        """
        self.assertEqual(self.pretty_ftl(input), dedent_ftl(input))

    def test_selector_number_expression(self):
        input = """\
            foo =
                { 1 ->
                   *[a] A
                }
        """
        self.assertEqual(self.pretty_ftl(input), dedent_ftl(input))

    def test_selector_string_expression(self):
        input = """\
            foo =
                { "bar" ->
                   *[a] A
                }
        """
        self.assertEqual(self.pretty_ftl(input), dedent_ftl(input))

    def test_selector_attribute_expression(self):
        input = """\
            foo =
                { -bar.baz ->
                   *[a] A
                }
        """
        self.assertEqual(self.pretty_ftl(input), dedent_ftl(input))

    def test_call_expression(self):
        input = """\
            foo = { FOO() }
        """
        self.assertEqual(self.pretty_ftl(input), dedent_ftl(input))

    def test_call_expression_with_string_expression(self):
        input = """\
            foo = { FOO("bar") }
        """
        self.assertEqual(self.pretty_ftl(input), dedent_ftl(input))

    def test_call_expression_with_number_expression(self):
        input = """\
            foo = { FOO(1) }
        """
        self.assertEqual(self.pretty_ftl(input), dedent_ftl(input))

    def test_call_expression_with_message_reference(self):
        input = """\
            foo = { FOO(bar) }
        """
        self.assertEqual(self.pretty_ftl(input), dedent_ftl(input))

    def test_call_expression_with_variable_reference(self):
        input = """\
            foo = { FOO($bar) }
        """
        self.assertEqual(self.pretty_ftl(input), dedent_ftl(input))

    def test_call_expression_with_two_positional_arguments(self):
        input = """\
            foo = { FOO(bar, baz) }
        """
        self.assertEqual(self.pretty_ftl(input), dedent_ftl(input))

    def test_call_expression_with_named_argument_number(self):
        input = """\
            foo = { FOO(bar: 1) }
        """
        self.assertEqual(self.pretty_ftl(input), dedent_ftl(input))

    def test_call_expression_with_named_argument_string(self):
        input = """\
            foo = { FOO(bar: "bar") }
        """
        self.assertEqual(self.pretty_ftl(input), dedent_ftl(input))

    def test_call_expression_with_two_named_arguments(self):
        input = """\
            foo = { FOO(bar: "bar", baz: "baz") }
        """
        self.assertEqual(self.pretty_ftl(input), dedent_ftl(input))

    def test_call_expression_with_positional_and_named_arguments(self):
        input = """\
            foo = { FOO(bar, 1, baz: "baz") }
        """
        self.assertEqual(self.pretty_ftl(input), dedent_ftl(input))

    def test_macro_call(self):
        input = """\
            foo = { -term() }
        """
        self.assertEqual(self.pretty_ftl(input), dedent_ftl(input))

    def test_nested_placeables(self):
        input = """\
            foo = {{ FOO() }}
        """
        self.assertEqual(self.pretty_ftl(input), dedent_ftl(input))

    def test_backslash_in_text(self):
        input = """\
            foo = \\{ placeable }
        """
        self.assertEqual(self.pretty_ftl(input), dedent_ftl(input))

    def test_escaped_special_in_string_literal(self):
        input = """\
            foo = { "Escaped \\" quote" }
        """
        self.assertEqual(self.pretty_ftl(input), dedent_ftl(input))

    def test_escaped_unicode_sequence(self):
        input = """\
            foo = { "\\u0065" }
        """
        self.assertEqual(self.pretty_ftl(input), dedent_ftl(input))


class TestSerializeExpression(unittest.TestCase):
    @staticmethod
    def pretty_expr(text):
        parser = FluentParser()
        entry = parser.parse_entry(dedent_ftl(text))
        expr = entry.value.elements[0].expression
        return serialize_expression(expr)

    def test_invalid_expression(self):
        with self.assertRaisesRegexp(Exception, 'Unknown expression type'):
            serialize_expression(None)

        with self.assertRaisesRegexp(Exception, 'Unknown expression type'):
            serialize_expression(object())

    def test_string_expression(self):
        input = """\
            foo = { "str" }
        """
        self.assertEqual(self.pretty_expr(input), '"str"')

    def test_number_expression(self):
        input = """\
            foo = { 3 }
        """
        self.assertEqual(self.pretty_expr(input), '3')

    def test_message_reference(self):
        input = """\
            foo = { msg }
        """
        self.assertEqual(self.pretty_expr(input), 'msg')

    def test_variable_reference(self):
        input = """\
            foo = { $ext }
        """
        self.assertEqual(self.pretty_expr(input), '$ext')

    def test_attribute_expression(self):
        input = """\
            foo = { msg.attr }
        """
        self.assertEqual(self.pretty_expr(input), 'msg.attr')

    def test_call_expression(self):
        input = """\
            foo = { BUILTIN(3.14, kwarg: "value") }
        """
        self.assertEqual(self.pretty_expr(input), 'BUILTIN(3.14, kwarg: "value")')

    def test_select_expression(self):
        input = """\
            foo =
                { $num ->
                   *[one] One
                }
        """
        self.assertEqual(self.pretty_expr(input), '$num ->\n   *[one] One\n')


class TestSerializeVariantKey(unittest.TestCase):
    @staticmethod
    def pretty_variant_key(text, index):
        parser = FluentParser()
        entry = parser.parse_entry(dedent_ftl(text))
        variants = entry.value.elements[0].expression.variants
        return serialize_variant_key(variants[index].key)

    def test_invalid_expression(self):
        with self.assertRaisesRegexp(Exception, 'Unknown variant key type'):
            serialize_variant_key(None)

        with self.assertRaisesRegexp(Exception, 'Unknown variant key type'):
            serialize_variant_key(object())

    def test_identifiers(self):
        input = """\
            foo = { $num ->
                [one] One
               *[other] Other
            }
        """
        self.assertEqual(self.pretty_variant_key(input, 0), 'one')
        self.assertEqual(self.pretty_variant_key(input, 1), 'other')

    def test_number_literals(self):
        input = """\
            foo = { $num ->
                [-123456789] Minus a lot
                [0] Zero
               *[3.14] Pi
                [007] James
            }
        """
        self.assertEqual(self.pretty_variant_key(input, 0), '-123456789')
        self.assertEqual(self.pretty_variant_key(input, 1), '0')
        self.assertEqual(self.pretty_variant_key(input, 2), '3.14')
        self.assertEqual(self.pretty_variant_key(input, 3), '007')
