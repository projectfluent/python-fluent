import unittest

from fluent.syntax.stream import ParserStream


class TestParserStream(unittest.TestCase):

    def test_next(self):
        ps = ParserStream("abcd")

        self.assertEqual("a", ps.current_char)
        self.assertEqual(0, ps.index)

        self.assertEqual("b", ps.next())
        self.assertEqual("b", ps.current_char)
        self.assertEqual(1, ps.index)

        self.assertEqual("c", ps.next())
        self.assertEqual("c", ps.current_char)
        self.assertEqual(2, ps.index)

        self.assertEqual("d", ps.next())
        self.assertEqual("d", ps.current_char)
        self.assertEqual(3, ps.index)

        self.assertEqual(None, ps.next())
        self.assertEqual(None, ps.current_char)
        self.assertEqual(4, ps.index)

    def test_peek(self):
        ps = ParserStream("abcd")

        self.assertEqual("a", ps.current_peek)
        self.assertEqual(0, ps.peek_offset)

        self.assertEqual("b", ps.peek())
        self.assertEqual("b", ps.current_peek)
        self.assertEqual(1, ps.peek_offset)

        self.assertEqual("c", ps.peek())
        self.assertEqual("c", ps.current_peek)
        self.assertEqual(2, ps.peek_offset)

        self.assertEqual("d", ps.peek())
        self.assertEqual("d", ps.current_peek)
        self.assertEqual(3, ps.peek_offset)

        self.assertEqual(None, ps.peek())
        self.assertEqual(None, ps.current_peek)
        self.assertEqual(4, ps.peek_offset)

    def test_peek_and_next(self):
        ps = ParserStream("abcd")

        self.assertEqual("b", ps.peek())
        self.assertEqual(1, ps.peek_offset)
        self.assertEqual(0, ps.index)

        self.assertEqual("b", ps.next())
        self.assertEqual(0, ps.peek_offset)
        self.assertEqual(1, ps.index)

        self.assertEqual("c", ps.peek())
        self.assertEqual(1, ps.peek_offset)
        self.assertEqual(1, ps.index)

        self.assertEqual("c", ps.next())
        self.assertEqual(0, ps.peek_offset)
        self.assertEqual(2, ps.index)
        self.assertEqual("c", ps.current_char)
        self.assertEqual("c", ps.current_peek)

        self.assertEqual("d", ps.peek())
        self.assertEqual(1, ps.peek_offset)
        self.assertEqual(2, ps.index)

        self.assertEqual("d", ps.next())
        self.assertEqual(0, ps.peek_offset)
        self.assertEqual(3, ps.index)
        self.assertEqual("d", ps.current_char)
        self.assertEqual("d", ps.current_peek)

        self.assertEqual(None, ps.peek())
        self.assertEqual(1, ps.peek_offset)
        self.assertEqual(3, ps.index)
        self.assertEqual("d", ps.current_char)
        self.assertEqual(None, ps.current_peek)

        self.assertEqual(None, ps.peek())
        self.assertEqual(2, ps.peek_offset)
        self.assertEqual(3, ps.index)

        self.assertEqual(None, ps.next())
        self.assertEqual(0, ps.peek_offset)
        self.assertEqual(4, ps.index)

    def test_skip_to_peek(self):
        ps = ParserStream("abcd")

        ps.peek()
        ps.peek()

        ps.skip_to_peek()

        self.assertEqual("c", ps.current_char)
        self.assertEqual("c", ps.current_peek)
        self.assertEqual(0, ps.peek_offset)
        self.assertEqual(2, ps.index)

        ps.peek()

        self.assertEqual("c", ps.current_char)
        self.assertEqual("d", ps.current_peek)
        self.assertEqual(1, ps.peek_offset)
        self.assertEqual(2, ps.index)

        ps.next()

        self.assertEqual("d", ps.current_char)
        self.assertEqual("d", ps.current_peek)
        self.assertEqual(0, ps.peek_offset)
        self.assertEqual(3, ps.index)

    def test_reset_peek(self):
        ps = ParserStream("abcd")

        ps.next()
        ps.peek()
        ps.peek()
        ps.reset_peek()

        self.assertEqual("b", ps.current_char)
        self.assertEqual("b", ps.current_peek)
        self.assertEqual(0, ps.peek_offset)
        self.assertEqual(1, ps.index)

        ps.peek()

        self.assertEqual("b", ps.current_char)
        self.assertEqual("c", ps.current_peek)
        self.assertEqual(1, ps.peek_offset)
        self.assertEqual(1, ps.index)

        ps.peek()
        ps.peek()
        ps.peek()
        ps.reset_peek()

        self.assertEqual("b", ps.current_char)
        self.assertEqual("b", ps.current_peek)
        self.assertEqual(0, ps.peek_offset)
        self.assertEqual(1, ps.index)

        self.assertEqual("c", ps.peek())
        self.assertEqual("b", ps.current_char)
        self.assertEqual("c", ps.current_peek)
        self.assertEqual(1, ps.peek_offset)
        self.assertEqual(1, ps.index)

        self.assertEqual("d", ps.peek())
        self.assertEqual(None, ps.peek())

    def test_source_position_over_newline(self):
        ps = ParserStream("ab\nc")

        # Initially we should start at 0,0
        self.assertEqual("a", ps.current_char)
        self.assertEqual(0, ps.row_index)
        self.assertEqual(0, ps.column_index)

        # Advancing within a line should increase the columm
        self.assertEqual("b", ps.next())
        self.assertEqual(0, ps.row_index)
        self.assertEqual(1, ps.column_index)

        # Advancing to the newline should increase the column
        self.assertEqual("\n", ps.next())
        self.assertEqual(0, ps.row_index)
        self.assertEqual(2, ps.column_index)

        # Advancing past the newline should increase the row and reset the column
        self.assertEqual("c", ps.next())
        self.assertEqual(1, ps.row_index)
        self.assertEqual(0, ps.column_index)

    def test_source_position_over_crlf(self):
        ps = ParserStream("a\r\nb")

        # Initially we should start at 0,0
        self.assertEqual("a", ps.current_char)
        self.assertEqual(0, ps.row_index)
        self.assertEqual(0, ps.column_index)

        # Advancing to the CRLF should increase the column
        self.assertEqual("\r", ps.next())
        self.assertEqual(0, ps.row_index)
        self.assertEqual(1, ps.column_index)

        # Advancing past the CRLF should increase the row and reset the column
        self.assertEqual("b", ps.next())
        self.assertEqual(1, ps.row_index)
        self.assertEqual(0, ps.column_index)

    def test_skip_to_peek_over_newline(self):
        ps = ParserStream("ab\nc")

        # Initially we should start at 0,0
        self.assertEqual("a", ps.current_char)
        self.assertEqual(0, ps.row_index)
        self.assertEqual(0, ps.column_index)

        # Peeking then advancing within a line should increase the columm
        self.assertEqual("b", ps.peek())
        self.assertEqual(0, ps.row_index)
        self.assertEqual(0, ps.column_index)

        ps.skip_to_peek()
        self.assertEqual(0, ps.row_index)
        self.assertEqual(1, ps.column_index)

        # Peeking then advancing to the newline should increase the column
        self.assertEqual("\n", ps.peek())
        self.assertEqual(0, ps.row_index)
        self.assertEqual(1, ps.column_index)

        ps.skip_to_peek()
        self.assertEqual(0, ps.row_index)
        self.assertEqual(2, ps.column_index)

        # Peeking then advancing past the newline should increase the row and reset the column
        self.assertEqual("c", ps.peek())
        self.assertEqual(0, ps.row_index)
        self.assertEqual(2, ps.column_index)

        ps.skip_to_peek()
        self.assertEqual(1, ps.row_index)
        self.assertEqual(0, ps.column_index)

    def test_skip_to_peek_over_crlf(self):
        ps = ParserStream("a\r\nb")

        # Initially we should start at 0,0
        self.assertEqual("a", ps.current_char)
        self.assertEqual(0, ps.row_index)
        self.assertEqual(0, ps.column_index)

        # Peeking then advancing to the CRLF should increase the column
        self.assertEqual("\r", ps.peek())
        self.assertEqual(0, ps.row_index)
        self.assertEqual(0, ps.column_index)

        ps.skip_to_peek()
        self.assertEqual(0, ps.row_index)
        self.assertEqual(1, ps.column_index)

        # Peeking then advancing past the CRLF should increase the row and reset the column
        self.assertEqual("b", ps.peek())
        self.assertEqual(0, ps.row_index)
        self.assertEqual(1, ps.column_index)

        ps.skip_to_peek()
        self.assertEqual(1, ps.row_index)
        self.assertEqual(0, ps.column_index)
