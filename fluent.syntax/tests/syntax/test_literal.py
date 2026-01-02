import sys

from fluent.syntax.parser import FluentParser


def parse_literal(input):
    parser = FluentParser(with_spans=False)
    ast = parser.parse_entry(input)
    expr = ast.value.elements[0].expression
    return expr.parse()


class TestStringLiteralParse:
    def test_no_escape_sequences(self):
        assert parse_literal('x = {"abc"}') == {"value": "abc"}

    def test_double_quote_backslash(self):
        assert parse_literal(r'x = {"\""}') == {"value": '"'}
        assert parse_literal(r'x = {"\\"}') == {"value": "\\"}

    def test_unicode_escape(self):
        assert parse_literal('x = {"\\u0041"}') == {"value": "A"}
        assert parse_literal('x = {"\\\\u0041"}') == {"value": "\\u0041"}
        if sys.maxunicode > 0xFFFF:
            assert parse_literal('x = {"\\U01F602"}') == {"value": "😂"}
        assert parse_literal('x = {"\\\\U01F602"}') == {"value": "\\U01F602"}

    def test_trailing_number(self):
        assert parse_literal('x = {"\\u004100"}') == {"value": "A00"}
        if sys.maxunicode > 0xFFFF:
            assert parse_literal('x = {"\\U01F60200"}') == {"value": "😂00"}


class TestNumberLiteralParse:
    def test_integers(self):
        assert parse_literal("x = {0}") == {"value": 0, "precision": 0}
        assert parse_literal("x = {1}") == {"value": 1, "precision": 0}
        assert parse_literal("x = {-0}") == {"value": 0, "precision": 0}
        assert parse_literal("x = {-1}") == {"value": -1, "precision": 0}

    def test_padded_integers(self):
        assert parse_literal("x = {00}") == {"value": 0, "precision": 0}
        assert parse_literal("x = {01}") == {"value": 1, "precision": 0}
        assert parse_literal("x = {-00}") == {"value": 0, "precision": 0}
        assert parse_literal("x = {-01}") == {"value": -1, "precision": 0}

    def test_positive_floats(self):
        assert parse_literal("x = {0.0}") == {"value": 0, "precision": 1}
        assert parse_literal("x = {0.01}") == {"value": 0.01, "precision": 2}
        assert parse_literal("x = {1.03}") == {"value": 1.03, "precision": 2}
        assert parse_literal("x = {1.000}") == {"value": 1, "precision": 3}

    def test_negative_floats(self):
        assert parse_literal("x = {-0.0}") == {"value": 0, "precision": 1}
        assert parse_literal("x = {-0.01}") == {"value": -0.01, "precision": 2}
        assert parse_literal("x = {-1.03}") == {"value": -1.03, "precision": 2}
        assert parse_literal("x = {-1.000}") == {"value": -1, "precision": 3}

    def test_padded_floats(self):
        assert parse_literal("x = {-00.00}") == {"value": 0, "precision": 2}
        assert parse_literal("x = {-01.000}") == {"value": -1, "precision": 3}
