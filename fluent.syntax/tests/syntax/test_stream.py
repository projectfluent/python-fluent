from fluent.syntax.stream import ParserStream


class TestParserStream:
    def test_next(self):
        ps = ParserStream("abcd")

        assert "a" == ps.current_char
        assert 0 == ps.index

        assert "b" == ps.next()
        assert "b" == ps.current_char
        assert 1 == ps.index

        assert "c" == ps.next()
        assert "c" == ps.current_char
        assert 2 == ps.index

        assert "d" == ps.next()
        assert "d" == ps.current_char
        assert 3 == ps.index

        assert ps.next() is None
        assert ps.current_char is None
        assert 4 == ps.index

    def test_peek(self):
        ps = ParserStream("abcd")

        assert "a" == ps.current_peek
        assert 0 == ps.peek_offset

        assert "b" == ps.peek()
        assert "b" == ps.current_peek
        assert 1 == ps.peek_offset

        assert "c" == ps.peek()
        assert "c" == ps.current_peek
        assert 2 == ps.peek_offset

        assert "d" == ps.peek()
        assert "d" == ps.current_peek
        assert 3 == ps.peek_offset

        assert ps.peek() is None
        assert ps.current_peek is None
        assert 4 == ps.peek_offset

    def test_peek_and_next(self):
        ps = ParserStream("abcd")

        assert "b" == ps.peek()
        assert 1 == ps.peek_offset
        assert 0 == ps.index

        assert "b" == ps.next()
        assert 0 == ps.peek_offset
        assert 1 == ps.index

        assert "c" == ps.peek()
        assert 1 == ps.peek_offset
        assert 1 == ps.index

        assert "c" == ps.next()
        assert 0 == ps.peek_offset
        assert 2 == ps.index
        assert "c" == ps.current_char
        assert "c" == ps.current_peek

        assert "d" == ps.peek()
        assert 1 == ps.peek_offset
        assert 2 == ps.index

        assert "d" == ps.next()
        assert 0 == ps.peek_offset
        assert 3 == ps.index
        assert "d" == ps.current_char
        assert "d" == ps.current_peek

        assert ps.peek() is None
        assert 1 == ps.peek_offset
        assert 3 == ps.index
        assert "d" == ps.current_char
        assert ps.current_peek is None

        assert ps.peek() is None
        assert 2 == ps.peek_offset
        assert 3 == ps.index

        assert ps.next() is None
        assert 0 == ps.peek_offset
        assert 4 == ps.index

    def test_skip_to_peek(self):
        ps = ParserStream("abcd")

        ps.peek()
        ps.peek()

        ps.skip_to_peek()

        assert "c" == ps.current_char
        assert "c" == ps.current_peek
        assert 0 == ps.peek_offset
        assert 2 == ps.index

        ps.peek()

        assert "c" == ps.current_char
        assert "d" == ps.current_peek
        assert 1 == ps.peek_offset
        assert 2 == ps.index

        ps.next()

        assert "d" == ps.current_char
        assert "d" == ps.current_peek
        assert 0 == ps.peek_offset
        assert 3 == ps.index

    def test_reset_peek(self):
        ps = ParserStream("abcd")

        ps.next()
        ps.peek()
        ps.peek()
        ps.reset_peek()

        assert "b" == ps.current_char
        assert "b" == ps.current_peek
        assert 0 == ps.peek_offset
        assert 1 == ps.index

        ps.peek()

        assert "b" == ps.current_char
        assert "c" == ps.current_peek
        assert 1 == ps.peek_offset
        assert 1 == ps.index

        ps.peek()
        ps.peek()
        ps.peek()
        ps.reset_peek()

        assert "b" == ps.current_char
        assert "b" == ps.current_peek
        assert 0 == ps.peek_offset
        assert 1 == ps.index

        assert "c" == ps.peek()
        assert "b" == ps.current_char
        assert "c" == ps.current_peek
        assert 1 == ps.peek_offset
        assert 1 == ps.index

        assert "d" == ps.peek()
        assert ps.peek() is None
