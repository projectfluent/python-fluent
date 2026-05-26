from fluent.syntax.parser import FluentParser

from . import dedent_ftl


def parse_ftl_entry(string):
    return FluentParser().parse_entry(dedent_ftl(string))


class TestEntryEqualToSelf:
    def test_same_simple_message(self):
        message1 = parse_ftl_entry(
            """\
            foo = Foo
        """
        )

        assert message1.equals(message1)
        assert message1.equals(message1.clone())

    def test_same_selector_message(self):
        message1 = parse_ftl_entry(
            """\
            foo =
                { $num ->
                    [one] One
                    [two] Two
                    [few] Few
                    [many] Many
                   *[other] Other
                }
        """
        )

        assert message1.equals(message1)
        assert message1.equals(message1.clone())

    def test_same_complex_placeable_message(self):
        message1 = parse_ftl_entry(
            """\
            foo = Foo { NUMBER($num, style: "decimal") } Bar
        """
        )

        assert message1.equals(message1)
        assert message1.equals(message1.clone())

    def test_same_message_with_attribute(self):
        message1 = parse_ftl_entry(
            """\
            foo =
                .attr = Attr
        """
        )

        assert message1.equals(message1)
        assert message1.equals(message1.clone())

    def test_same_message_with_attributes(self):
        message1 = parse_ftl_entry(
            """\
            foo =
                .attr1 = Attr 1
                .attr2 = Attr 2
        """
        )

        assert message1.equals(message1)
        assert message1.equals(message1.clone())

    def test_same_junk(self):
        message1 = parse_ftl_entry(
            """\
            foo = Foo {
        """
        )

        assert message1.equals(message1)
        assert message1.equals(message1.clone())


class TestNonEquals:
    def test_attributes(self):
        message1 = parse_ftl_entry(
            """\
            foo =
                .attr1 = Attr1
                .attr2 = Attr2
        """
        )
        message2 = parse_ftl_entry(
            """\
            foo =
                .attr2 = Attr2
                .attr1 = Attr1
        """
        )

        assert not message1.equals(message2)

    def test_variants(self):
        message1 = parse_ftl_entry(
            """\
            foo =
                { $num ->
                    [a] A
                   *[b] B
                }
        """
        )
        message2 = parse_ftl_entry(
            """\
            foo =
                { $num ->
                   *[b] B
                    [a] A
                }
        """
        )

        assert not message1.equals(message2)

    def test_variants_with_numbers(self):
        message1 = parse_ftl_entry(
            """\
            foo =
                { $num ->
                    [1] A
                   *[b] B
                }
        """
        )
        message2 = parse_ftl_entry(
            """\
            foo =
                { $num ->
                   *[b] B
                    [1] A
                }
        """
        )

        assert not message1.equals(message2)


class TestEqualWithSpans:
    def test_default_behavior(self):
        parser = FluentParser()

        strings = [
            ("foo = Foo", "foo = Foo"),
            ("foo = Foo", "foo =   Foo"),
            ("foo = { $arg }", "foo = {  $arg  }"),
        ]

        messages = [(parser.parse_entry(a), parser.parse_entry(b)) for a, b in strings]

        for a, b in messages:
            assert a.equals(b)

    def test_parser_without_spans(self):
        parser = FluentParser(with_spans=False)

        strings = [
            ("foo = Foo", "foo = Foo"),
            ("foo = Foo", "foo =   Foo"),
            ("foo = { $arg }", "foo = {  $arg  }"),
        ]

        messages = [(parser.parse_entry(a), parser.parse_entry(b)) for a, b in strings]

        for a, b in messages:
            assert a.equals(b)

    def test_equals_with_spans(self):
        parser = FluentParser()

        strings = [
            ("foo = Foo", "foo = Foo"),
            ("foo = { $arg }", "foo = { $arg }"),
        ]

        messages = [(parser.parse_entry(a), parser.parse_entry(b)) for a, b in strings]

        for a, b in messages:
            assert a.equals(b, ignored_fields=None)

    def test_parser_without_spans_equals_with_spans(self):
        parser = FluentParser(with_spans=False)

        strings = [
            ("foo = Foo", "foo = Foo"),
            ("foo = Foo", "foo =   Foo"),
            ("foo = { $arg }", "foo = { $arg }"),
            ("foo = { $arg }", "foo = {  $arg  }"),
        ]

        messages = [(parser.parse_entry(a), parser.parse_entry(b)) for a, b in strings]

        for a, b in messages:
            assert a.equals(b, ignored_fields=None)

    def test_differ_with_spans(self):
        parser = FluentParser()

        strings = [
            ("foo = Foo", "foo =   Foo"),
            ("foo = { $arg }", "foo = {  $arg  }"),
        ]

        messages = [(parser.parse_entry(a), parser.parse_entry(b)) for a, b in strings]

        for a, b in messages:
            assert not a.equals(b, ignored_fields=None)


class TestIgnoredFields:
    def test_ignore_value(self):
        a = parse_ftl_entry("foo = Foo")
        b = parse_ftl_entry("foo = Bar")

        assert a.equals(b, ignored_fields=["value"])

    def test_ignore_value_span(self):
        a = parse_ftl_entry("foo = Foo")
        b = parse_ftl_entry("foo = Foobar")

        assert a.equals(b, ignored_fields=["span", "value"])
        assert not a.equals(b, ignored_fields=["value"])

    def test_ignore_comments(self):
        a = parse_ftl_entry(
            """\
            # Comment A
            foo = Foo
        """
        )
        b = parse_ftl_entry(
            """\
            # Comment B
            foo = Foo
        """
        )
        c = parse_ftl_entry(
            """\
            # Comment CC
            foo = Foo
        """
        )

        assert a.equals(b, ignored_fields=["comment"])
        assert not a.equals(c, ignored_fields=["comment"])
        assert a.equals(c, ignored_fields=["comment", "span"])
