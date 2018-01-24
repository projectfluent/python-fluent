from __future__ import unicode_literals
import unittest
import sys

sys.path.append('.')

from tests.syntax import dedent_ftl
from fluent.syntax import parse, serialize


def pretty_ftl(text):
    res = parse(dedent_ftl(text))
    return serialize(res)


class TestSerializer(unittest.TestCase):
    def test_simple_message(self):
        input = """\
            foo = Foo
        """
        self.assertEqual(pretty_ftl(input), dedent_ftl(input))

    def test_two_simple_messages(self):
        input = """\
            foo = Foo
            bar = Bar
        """
        self.assertEqual(pretty_ftl(input), dedent_ftl(input))

    def test_multiline_simple(self):
        input = """\
            foo =
                Foo
                Bar
        """
        self.assertEqual(pretty_ftl(input), dedent_ftl(input))

    def test_message_reference(self):
        input = """\
            foo = Foo { bar }
        """
        self.assertEqual(pretty_ftl(input), dedent_ftl(input))

    def test_external_argument(self):
        input = """\
            foo = Foo { $bar }
        """
        self.assertEqual(pretty_ftl(input), dedent_ftl(input))

    def test_number_element(self):
        input = """\
            foo = Foo { 1 }
        """
        self.assertEqual(pretty_ftl(input), dedent_ftl(input))

    def test_string_element(self):
        input = """\
            foo = Foo { "bar" }
        """
        self.assertEqual(pretty_ftl(input), dedent_ftl(input))

    def test_variant_expression(self):
        input = """\
            foo = Foo { bar[baz] }
        """
        self.assertEqual(pretty_ftl(input), dedent_ftl(input))

    def test_attribute_expression(self):
        input = """\
            foo = Foo { bar.baz }
        """
        self.assertEqual(pretty_ftl(input), dedent_ftl(input))

    def test_comment_resource(self):
        input = """\
            ### A multiline
            ### resource comment.

            foo = Foo
        """
        self.assertEqual(pretty_ftl(input), dedent_ftl(input))

    def test_comment_message(self):
        input = """\
            # A multiline
            # message comment.
            foo = Foo
        """
        self.assertEqual(pretty_ftl(input), dedent_ftl(input))

    def test_comment_group(self):
        input = """\
            foo = Foo

            ## Comment Header
            ##
            ## A multiline
            ## section comment.

            bar = Bar
        """
        self.assertEqual(pretty_ftl(input), dedent_ftl(input))

    def test_comment_standalone(self):
        input = """\
            foo = Foo

            # A multiline

            bar = Bar
        """
        self.assertEqual(pretty_ftl(input), dedent_ftl(input))

    def test_multiline_with_placeable(self):
        input = """\
            foo =
                Foo { bar }
                Baz
        """
        self.assertEqual(pretty_ftl(input), dedent_ftl(input))

    def test_attribute(self):
        input = """\
            foo
                .attr = Foo Attr
        """
        self.assertEqual(pretty_ftl(input), dedent_ftl(input))

    def test_attribute_multiline(self):
        input = """\
            foo
                .attr =
                    Foo Attr
                    Continued
        """
        self.assertEqual(pretty_ftl(input), dedent_ftl(input))

    def test_two_attributes(self):
        input = """\
            foo
                .attr-a = Foo Attr A
                .attr-b = Foo Attr B
        """
        self.assertEqual(pretty_ftl(input), dedent_ftl(input))

    def test_value_and_attributes(self):
        input = """\
            foo = Foo Value
                .attr-a = Foo Attr A
                .attr-b = Foo Attr B
        """
        self.assertEqual(pretty_ftl(input), dedent_ftl(input))

    def test_multiline_value_and_attributes(self):
        input = """\
            foo =
                Foo Value
                Continued
                .attr-a = Foo Attr A
                .attr-b = Foo Attr B
        """
        self.assertEqual(pretty_ftl(input), dedent_ftl(input))

    def test_select_expression_no_selector(self):
        input = """\
            foo = {
                   *[a] A
                    [b] B
                }
        """
        self.assertEqual(pretty_ftl(input), dedent_ftl(input))

    def test_select_expression(self):
        input = """\
            foo = { sel ->
                   *[a] A
                    [b] B
                }
        """
        self.assertEqual(pretty_ftl(input), dedent_ftl(input))

    # XXX The variant contains a new-line so the serializer defaults to
    # multiline formatting for all of its contents.
    # https://bugzilla.mozilla.org/show_bug.cgi?id=1397760
    def test_variant_multiline_first_inline(self):
        input = """\
            foo = {
                   *[a] AAA
                        BBB
                }
        """
        output = """\
            foo = {
                   *[a]
                        AAA
                        BBB
                }
        """
        self.assertEqual(pretty_ftl(input), dedent_ftl(output))

    def test_variant_multiline(self):
        input = """\
            foo = {
                   *[a]
                        AAA
                        BBB
                }
        """
        self.assertEqual(pretty_ftl(input), dedent_ftl(input))

    def test_variant_key_words(self):
        input = """\
            foo = {
                   *[a b c] A B C
                }
        """
        self.assertEqual(pretty_ftl(input), dedent_ftl(input))

    def test_variant_key_number(self):
        input = """\
            foo = {
                   *[1] 1
                }
        """
        self.assertEqual(pretty_ftl(input), dedent_ftl(input))

    @unittest.skip("The serializer doesn't know it's multiline.")
    def test_select_expression_in_simple_multiline(self):
        input = """\
            foo =
                Foo { sel ->
                   *[a] A
                    [b] B
                }
        """
        self.assertEqual(pretty_ftl(input), dedent_ftl(input))

    # None of the Text elements contain a new-line, so the serializer outputs
    # a single-line value.
    def test_select_expression_in_simple_multiline_current(self):
        input = """\
            foo =
                Foo { sel ->
                   *[a] A
                    [b] B
                }
        """
        output = """\
            foo = Foo { sel ->
                   *[a] A
                    [b] B
                }
        """
        self.assertEqual(pretty_ftl(input), dedent_ftl(output))

    def test_select_expression_in_multi_multiline(self):
        input = """\
            foo =
                Foo
                Bar { sel ->
                   *[a] A
                    [b] B
                }
        """
        self.assertEqual(pretty_ftl(input), dedent_ftl(input))

    def test_select_expression_nested(self):
        input = """\
            foo = { sel_a ->
                   *[a] { sel_b ->
                           *[b] Foo
                        }
                }
        """
        self.assertEqual(pretty_ftl(input), dedent_ftl(input))

    def test_selector_message_reference(self):
        input = """\
            foo = { bar ->
                   *[a] A
                }
        """
        self.assertEqual(pretty_ftl(input), dedent_ftl(input))

    def test_selector_external_argument(self):
        input = """\
            foo = { $bar ->
                   *[a] A
                }
        """
        self.assertEqual(pretty_ftl(input), dedent_ftl(input))

    def test_selector_number_expression(self):
        input = """\
            foo = { 1 ->
                   *[a] A
                }
        """
        self.assertEqual(pretty_ftl(input), dedent_ftl(input))

    def test_selector_string_expression(self):
        input = """\
            foo = { "bar" ->
                   *[a] A
                }
        """
        self.assertEqual(pretty_ftl(input), dedent_ftl(input))

    def test_selector_variant_expression(self):
        input = """\
            foo = { bar[baz] ->
                   *[a] A
                }
        """
        self.assertEqual(pretty_ftl(input), dedent_ftl(input))

    def test_selector_attribute_expression(self):
        input = """\
            foo = { bar.baz ->
                   *[a] A
                }
        """
        self.assertEqual(pretty_ftl(input), dedent_ftl(input))

    def test_call_expression(self):
        input = """\
            foo = { FOO() }
        """
        self.assertEqual(pretty_ftl(input), dedent_ftl(input))

    def test_call_expression_with_string_expression(self):
        input = """\
            foo = { FOO("bar") }
        """
        self.assertEqual(pretty_ftl(input), dedent_ftl(input))

    def test_call_expression_with_number_expression(self):
        input = """\
            foo = { FOO(1) }
        """
        self.assertEqual(pretty_ftl(input), dedent_ftl(input))

    def test_call_expression_with_message_reference(self):
        input = """\
            foo = { FOO(bar) }
        """
        self.assertEqual(pretty_ftl(input), dedent_ftl(input))

    def test_call_expression_with_external_argument(self):
        input = """\
            foo = { FOO($bar) }
        """
        self.assertEqual(pretty_ftl(input), dedent_ftl(input))

    def test_call_expression_with_two_positional_arguments(self):
        input = """\
            foo = { FOO(bar, baz) }
        """
        self.assertEqual(pretty_ftl(input), dedent_ftl(input))

    def test_call_expression_with_named_argument_number(self):
        input = """\
            foo = { FOO(bar: 1) }
        """
        self.assertEqual(pretty_ftl(input), dedent_ftl(input))

    def test_call_expression_with_named_argument_string(self):
        input = """\
            foo = { FOO(bar: "bar") }
        """
        self.assertEqual(pretty_ftl(input), dedent_ftl(input))

    def test_call_expression_with_two_named_arguments(self):
        input = """\
            foo = { FOO(bar: "bar", baz: "baz") }
        """
        self.assertEqual(pretty_ftl(input), dedent_ftl(input))

    def test_call_expression_with_positional_and_named_arguments(self):
        input = """\
            foo = { FOO(bar, baz: "baz", 1) }
        """
        self.assertEqual(pretty_ftl(input), dedent_ftl(input))
