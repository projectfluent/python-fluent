import pytest
from fluent.syntax import FluentParser, FluentSerializer
from fluent.syntax.serializer import serialize_expression, serialize_variant_key

from . import dedent_ftl


class TestSerializeResource:
    @staticmethod
    def pretty_ftl(text):
        parser = FluentParser()
        serializer = FluentSerializer(with_junk=False)
        res = parser.parse(dedent_ftl(text))
        return serializer.serialize(res)

    def test_invalid_resource(self):
        serializer = FluentSerializer()

        with pytest.raises(Exception, match="Unknown resource type"):
            serializer.serialize(None)

        with pytest.raises(Exception, match="Unknown resource type"):
            serializer.serialize(object())

    def test_simple_message(self):
        input = """\
            foo = Foo
        """
        assert self.pretty_ftl(input) == dedent_ftl(input)

    def test_simple_term(self):
        input = """\
            -foo = Foo
        """
        assert self.pretty_ftl(input) == dedent_ftl(input)

    def test_two_simple_messages(self):
        input = """\
            foo = Foo
            bar = Bar
        """
        assert self.pretty_ftl(input) == dedent_ftl(input)

    def test_block_multiline(self):
        input = """\
            foo =
                Foo
                Bar
        """
        assert self.pretty_ftl(input) == dedent_ftl(input)

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
        assert self.pretty_ftl(input) == dedent_ftl(output)

    def test_message_reference(self):
        input = """\
            foo = Foo { bar }
        """
        assert self.pretty_ftl(input) == dedent_ftl(input)

    def test_term_reference(self):
        input = """\
            foo = Foo { -bar }
        """
        assert self.pretty_ftl(input) == dedent_ftl(input)

    def test_variable_reference(self):
        input = """\
            foo = Foo { $bar }
        """
        assert self.pretty_ftl(input) == dedent_ftl(input)

    def test_number_element(self):
        input = """\
            foo = Foo { 1 }
        """
        assert self.pretty_ftl(input) == dedent_ftl(input)

    def test_string_element(self):
        input = """\
            foo = Foo { "bar" }
        """
        assert self.pretty_ftl(input) == dedent_ftl(input)

    def test_attribute_expression(self):
        input = """\
            foo = Foo { bar.baz }
        """
        assert self.pretty_ftl(input) == dedent_ftl(input)

    def test_comment_resource(self):
        input = """\
            ### A multiline
            ### resource comment.

            foo = Foo
        """
        assert self.pretty_ftl(input) == dedent_ftl(input)

    def test_comment_message(self):
        input = """\
            # A multiline
            # message comment.
            foo = Foo
            #
            bar = Bar
        """
        assert self.pretty_ftl(input) == dedent_ftl(input)

    def test_comment_group(self):
        input = """\
            foo = Foo

            ## Comment Header
            ##
            ## A multiline
            ## group comment.

            bar = Bar

            ##

            baz = Baz
        """
        assert self.pretty_ftl(input) == dedent_ftl(input)

    def test_comment_standalone(self):
        input = """\
            foo = Foo

            # A standalone comment

            bar = Bar
        """
        assert self.pretty_ftl(input) == dedent_ftl(input)

    def test_multiline_starting_inline(self):
        input = """\
            foo = Foo
                Bar
        """
        output = """\
            foo =
                Foo
                Bar
        """
        assert self.pretty_ftl(input) == dedent_ftl(output)

    def test_multiline_starting_inline_with_special_char(self):
        input = """\
            foo = *Foo
                Bar
        """
        assert self.pretty_ftl(input) == dedent_ftl(input)

    def test_multiline_with_placeable(self):
        input = """\
            foo =
                Foo { bar }
                Baz
        """
        assert self.pretty_ftl(input) == dedent_ftl(input)

    def test_attribute(self):
        input = """\
            foo =
                .attr = Foo Attr
        """
        assert self.pretty_ftl(input) == dedent_ftl(input)

    def test_attribute_multiline(self):
        input = """\
            foo =
                .attr =
                    Foo Attr
                    Continued
        """
        assert self.pretty_ftl(input) == dedent_ftl(input)

    def test_two_attributes(self):
        input = """\
            foo =
                .attr-a = Foo Attr A
                .attr-b = Foo Attr B
        """
        assert self.pretty_ftl(input) == dedent_ftl(input)

    def test_value_and_attributes(self):
        input = """\
            foo = Foo Value
                .attr-a = Foo Attr A
                .attr-b = Foo Attr B
        """
        assert self.pretty_ftl(input) == dedent_ftl(input)

    def test_multiline_value_and_attributes(self):
        input = """\
            foo =
                Foo Value
                Continued
                .attr-a = Foo Attr A
                .attr-b = Foo Attr B
        """
        assert self.pretty_ftl(input) == dedent_ftl(input)

    def test_select_expression(self):
        input = """\
            foo =
                { $sel ->
                   *[a] A
                    [b] B
                }
        """
        assert self.pretty_ftl(input) == dedent_ftl(input)

    def test_variant_multiline(self):
        input = """\
            foo =
                { $sel ->
                   *[a]
                        AAA
                        BBB
                }
        """
        assert self.pretty_ftl(input) == dedent_ftl(input)

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
        assert self.pretty_ftl(input) == dedent_ftl(output)

    def test_variant_key_number(self):
        input = """\
            foo =
                { $sel ->
                   *[1] 1
                }
        """
        assert self.pretty_ftl(input) == dedent_ftl(input)

    def test_select_expression_in_block_value(self):
        input = """\
            foo =
                Foo { $sel ->
                   *[a] A
                    [b] B
                }
        """
        assert self.pretty_ftl(input) == dedent_ftl(input)

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
        assert self.pretty_ftl(input) == dedent_ftl(output)

    def test_select_expression_in_inline_value_starting_with_special_char(self):
        input = """\
            foo = .Foo { $sel ->
                   *[a] A
                    [b] B
                }
        """
        assert self.pretty_ftl(input) == dedent_ftl(input)

    def test_select_expression_in_multi_multiline(self):
        input = """\
            foo =
                Foo
                Bar { $sel ->
                   *[a] A
                    [b] B
                }
        """
        assert self.pretty_ftl(input) == dedent_ftl(input)

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
        assert self.pretty_ftl(input) == dedent_ftl(input)

    def test_selector_variable_reference(self):
        input = """\
            foo =
                { $bar ->
                   *[a] A
                }
        """
        assert self.pretty_ftl(input) == dedent_ftl(input)

    def test_selector_number_expression(self):
        input = """\
            foo =
                { 1 ->
                   *[a] A
                }
        """
        assert self.pretty_ftl(input) == dedent_ftl(input)

    def test_selector_string_expression(self):
        input = """\
            foo =
                { "bar" ->
                   *[a] A
                }
        """
        assert self.pretty_ftl(input) == dedent_ftl(input)

    def test_selector_attribute_expression(self):
        input = """\
            foo =
                { -bar.baz ->
                   *[a] A
                }
        """
        assert self.pretty_ftl(input) == dedent_ftl(input)

    def test_call_expression(self):
        input = """\
            foo = { FOO() }
        """
        assert self.pretty_ftl(input) == dedent_ftl(input)

    def test_call_expression_with_string_expression(self):
        input = """\
            foo = { FOO("bar") }
        """
        assert self.pretty_ftl(input) == dedent_ftl(input)

    def test_call_expression_with_number_expression(self):
        input = """\
            foo = { FOO(1) }
        """
        assert self.pretty_ftl(input) == dedent_ftl(input)

    def test_call_expression_with_message_reference(self):
        input = """\
            foo = { FOO(bar) }
        """
        assert self.pretty_ftl(input) == dedent_ftl(input)

    def test_call_expression_with_variable_reference(self):
        input = """\
            foo = { FOO($bar) }
        """
        assert self.pretty_ftl(input) == dedent_ftl(input)

    def test_call_expression_with_two_positional_arguments(self):
        input = """\
            foo = { FOO(bar, baz) }
        """
        assert self.pretty_ftl(input) == dedent_ftl(input)

    def test_call_expression_with_named_argument_number(self):
        input = """\
            foo = { FOO(bar: 1) }
        """
        assert self.pretty_ftl(input) == dedent_ftl(input)

    def test_call_expression_with_named_argument_string(self):
        input = """\
            foo = { FOO(bar: "bar") }
        """
        assert self.pretty_ftl(input) == dedent_ftl(input)

    def test_call_expression_with_two_named_arguments(self):
        input = """\
            foo = { FOO(bar: "bar", baz: "baz") }
        """
        assert self.pretty_ftl(input) == dedent_ftl(input)

    def test_call_expression_with_positional_and_named_arguments(self):
        input = """\
            foo = { FOO(bar, 1, baz: "baz") }
        """
        assert self.pretty_ftl(input) == dedent_ftl(input)

    def test_macro_call(self):
        input = """\
            foo = { -term() }
        """
        assert self.pretty_ftl(input) == dedent_ftl(input)

    def test_nested_placeables(self):
        input = """\
            foo = {{ FOO() }}
        """
        assert self.pretty_ftl(input) == dedent_ftl(input)

    def test_backslash_in_text(self):
        input = """\
            foo = \\{ placeable }
        """
        assert self.pretty_ftl(input) == dedent_ftl(input)

    def test_escaped_special_in_string_literal(self):
        input = """\
            foo = { "Escaped \\" quote" }
        """
        assert self.pretty_ftl(input) == dedent_ftl(input)

    def test_escaped_unicode_sequence(self):
        input = """\
            foo = { "\\u0065" }
        """
        assert self.pretty_ftl(input) == dedent_ftl(input)


class TestSerializeExpression:
    @staticmethod
    def pretty_expr(text):
        parser = FluentParser()
        entry = parser.parse_entry(dedent_ftl(text))
        expr = entry.value.elements[0].expression
        return serialize_expression(expr)

    def test_invalid_expression(self):
        with pytest.raises(Exception, match="Unknown expression type"):
            serialize_expression(None)

        with pytest.raises(Exception, match="Unknown expression type"):
            serialize_expression(object())

    def test_string_expression(self):
        input = """\
            foo = { "str" }
        """
        assert self.pretty_expr(input) == '"str"'

    def test_number_expression(self):
        input = """\
            foo = { 3 }
        """
        assert self.pretty_expr(input) == "3"

    def test_message_reference(self):
        input = """\
            foo = { msg }
        """
        assert self.pretty_expr(input) == "msg"

    def test_variable_reference(self):
        input = """\
            foo = { $ext }
        """
        assert self.pretty_expr(input) == "$ext"

    def test_attribute_expression(self):
        input = """\
            foo = { msg.attr }
        """
        assert self.pretty_expr(input) == "msg.attr"

    def test_call_expression(self):
        input = """\
            foo = { BUILTIN(3.14, kwarg: "value") }
        """
        assert self.pretty_expr(input) == 'BUILTIN(3.14, kwarg: "value")'

    def test_select_expression(self):
        input = """\
            foo =
                { $num ->
                   *[one] One
                }
        """
        assert self.pretty_expr(input) == "$num ->\n   *[one] One\n"


class TestSerializeVariantKey:
    @staticmethod
    def pretty_variant_key(text, index):
        parser = FluentParser()
        entry = parser.parse_entry(dedent_ftl(text))
        variants = entry.value.elements[0].expression.variants
        return serialize_variant_key(variants[index].key)

    def test_invalid_expression(self):
        with pytest.raises(Exception, match="Unknown variant key type"):
            serialize_variant_key(None)

        with pytest.raises(Exception, match="Unknown variant key type"):
            serialize_variant_key(object())

    def test_identifiers(self):
        input = """\
            foo = { $num ->
                [one] One
               *[other] Other
            }
        """
        assert self.pretty_variant_key(input, 0) == "one"
        assert self.pretty_variant_key(input, 1) == "other"

    def test_number_literals(self):
        input = """\
            foo = { $num ->
                [-123456789] Minus a lot
                [0] Zero
               *[3.14] Pi
                [007] James
            }
        """
        assert self.pretty_variant_key(input, 0) == "-123456789"
        assert self.pretty_variant_key(input, 1) == "0"
        assert self.pretty_variant_key(input, 2) == "3.14"
        assert self.pretty_variant_key(input, 3) == "007"
