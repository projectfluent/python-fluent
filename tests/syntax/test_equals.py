from __future__ import unicode_literals
import unittest
import sys

sys.path.append('.')

from tests.syntax import dedent_ftl
from fluent.syntax.parser import FluentParser


def identity(node):
    return node


class TestEntryEqualToSelf(unittest.TestCase):
    def setUp(self):
        self.parser = FluentParser()

    def parse_ftl_entry(self, string):
        return self.parser.parse_entry(dedent_ftl(string))

    def test_same_simple_message(self):
        message1 = self.parse_ftl_entry("""\
            foo = Foo
        """)

        self.assertTrue(message1.equals(message1))
        self.assertTrue(message1.equals(message1.traverse(identity)))

    def test_same_selector_message(self):
        message1 = self.parse_ftl_entry("""\
            foo =
                { $num ->
                    [one] One
                    [two] Two
                    [few] Few
                    [many] Many
                   *[other] Other
                }
        """)

        self.assertTrue(message1.equals(message1))
        self.assertTrue(message1.equals(message1.traverse(identity)))

    def test_same_complex_placeable_message(self):
        message1 = self.parse_ftl_entry("""\
            foo = Foo { NUMBER($num, style: "decimal") } Bar
        """)

        self.assertTrue(message1.equals(message1))
        self.assertTrue(message1.equals(message1.traverse(identity)))

    def test_same_message_with_attribute(self):
        message1 = self.parse_ftl_entry("""\
            foo
                .attr = Attr
        """)

        self.assertTrue(message1.equals(message1))
        self.assertTrue(message1.equals(message1.traverse(identity)))

    def test_same_message_with_attributes(self):
        message1 = self.parse_ftl_entry("""\
            foo
                .attr1 = Attr 1
                .attr2 = Attr 2
        """)

        self.assertTrue(message1.equals(message1))
        self.assertTrue(message1.equals(message1.traverse(identity)))

    def test_same_message_with_tag(self):
        message1 = self.parse_ftl_entry("""\
            foo = Foo
                #tag
        """)

        self.assertTrue(message1.equals(message1))
        self.assertTrue(message1.equals(message1.traverse(identity)))

    def test_same_message_with_tags(self):
        message1 = self.parse_ftl_entry("""\
            foo = Foo
                #tag1
                #tag2
        """)

        self.assertTrue(message1.equals(message1))
        self.assertTrue(message1.equals(message1.traverse(identity)))

    def test_same_junk(self):
        message1 = self.parse_ftl_entry("""\
            foo = Foo {
        """)

        self.assertTrue(message1.equals(message1))
        self.assertTrue(message1.equals(message1.traverse(identity)))


class TestOrderEquals(unittest.TestCase):
    def setUp(self):
        self.parser = FluentParser()

    def parse_ftl_entry(self, string):
        return self.parser.parse_entry(dedent_ftl(string))

    def test_attributes(self):
        message1 = self.parse_ftl_entry("""\
            foo
                .attr1 = Attr1
                .attr2 = Attr2
        """)
        message2 = self.parse_ftl_entry("""\
            foo
                .attr2 = Attr2
                .attr1 = Attr1
        """)

        self.assertTrue(message1.equals(message2))
        self.assertTrue(message2.equals(message1))

    def test_tags(self):
        message1 = self.parse_ftl_entry("""\
            foo = Foo
                #tag1
                #tag2
        """)
        message2 = self.parse_ftl_entry("""\
            foo = Foo
                #tag2
                #tag1
        """)

        self.assertTrue(message1.equals(message2))
        self.assertTrue(message2.equals(message1))

    def test_variants(self):
        message1 = self.parse_ftl_entry("""\
            foo =
                { $num ->
                    [a] A
                   *[b] B
                }
        """)
        message2 = self.parse_ftl_entry("""\
            foo =
                { $num ->
                   *[b] B
                    [a] A
                }
        """)

        self.assertTrue(message1.equals(message2))
        self.assertTrue(message2.equals(message1))


class TestEqualWithSpans(unittest.TestCase):
    def test_default_behavior(self):
        parser = FluentParser()

        strings = [
            ("foo = Foo", "foo = Foo"),
            ("foo = Foo", "foo =   Foo"),
            ("foo = { $arg }", "foo = {  $arg  }"),
        ]

        messages = [
            (parser.parse_entry(a), parser.parse_entry(b))
            for a, b in strings
        ]

        for a, b in messages:
            self.assertTrue(a.equals(b))

    def test_parser_without_spans(self):
        parser = FluentParser(with_spans=False)

        strings = [
            ("foo = Foo", "foo = Foo"),
            ("foo = Foo", "foo =   Foo"),
            ("foo = { $arg }", "foo = {  $arg  }"),
        ]

        messages = [
            (parser.parse_entry(a), parser.parse_entry(b))
            for a, b in strings
        ]

        for a, b in messages:
            self.assertTrue(a.equals(b))

    def test_equals_with_spans(self):
        parser = FluentParser()

        strings = [
            ("foo = Foo", "foo = Foo"),
            ("foo = { $arg }", "foo = { $arg }"),
        ]

        messages = [
            (parser.parse_entry(a), parser.parse_entry(b))
            for a, b in strings
        ]

        for a, b in messages:
            self.assertTrue(a.equals(b, with_spans=True))

    def test_parser_without_spans_equals_with_spans(self):
        parser = FluentParser(with_spans=False)

        strings = [
            ("foo = Foo", "foo = Foo"),
            ("foo = Foo", "foo =   Foo"),
            ("foo = { $arg }", "foo = { $arg }"),
            ("foo = { $arg }", "foo = {  $arg  }"),
        ]

        messages = [
            (parser.parse_entry(a), parser.parse_entry(b))
            for a, b in strings
        ]

        for a, b in messages:
            self.assertTrue(a.equals(b, with_spans=True))

    def test_differ_with_spans(self):
        parser = FluentParser()

        strings = [
            ("foo = Foo", "foo =   Foo"),
            ("foo = { $arg }", "foo = {  $arg  }"),
        ]

        messages = [
            (parser.parse_entry(a), parser.parse_entry(b))
            for a, b in strings
        ]

        for a, b in messages:
            self.assertFalse(a.equals(b, with_spans=True))
