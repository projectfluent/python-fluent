import unittest

from fluent.syntax.stream import ParserStream


class TestParserStream(unittest.TestCase):

    def test_next(self):
        ps = ParserStream("abcd")

        self.assertEqual('a', ps.current_char)
        self.assertEqual(0, ps.index)

        self.assertEqual('b', ps.next())
        self.assertEqual('b', ps.current_char)
        self.assertEqual(1, ps.index)

        self.assertEqual('c', ps.next())
        self.assertEqual('c', ps.current_char)
        self.assertEqual(2, ps.index)

        self.assertEqual('d', ps.next())
        self.assertEqual('d', ps.current_char)
        self.assertEqual(3, ps.index)

        self.assertEqual(None, ps.next())
        self.assertEqual(None, ps.current_char)
        self.assertEqual(4, ps.index)

    def test_peek(self):
        ps = ParserStream("abcd")

        self.assertEqual('a', ps.current_peek)
        self.assertEqual(0, ps.peek_offset)

        self.assertEqual('b', ps.peek())
        self.assertEqual('b', ps.current_peek)
        self.assertEqual(1, ps.peek_offset)

        self.assertEqual('c', ps.peek())
        self.assertEqual('c', ps.current_peek)
        self.assertEqual(2, ps.peek_offset)

        self.assertEqual('d', ps.peek())
        self.assertEqual('d', ps.current_peek)
        self.assertEqual(3, ps.peek_offset)

        self.assertEqual(None, ps.peek())
        self.assertEqual(None, ps.current_peek)
        self.assertEqual(4, ps.peek_offset)

    def test_peek_and_next(self):
        ps = ParserStream("abcd")

        self.assertEqual('b', ps.peek())
        self.assertEqual(1, ps.peek_offset)
        self.assertEqual(0, ps.index)

        self.assertEqual('b', ps.next())
        self.assertEqual(0, ps.peek_offset)
        self.assertEqual(1, ps.index)

        self.assertEqual('c', ps.peek())
        self.assertEqual(1, ps.peek_offset)
        self.assertEqual(1, ps.index)

        self.assertEqual('c', ps.next())
        self.assertEqual(0, ps.peek_offset)
        self.assertEqual(2, ps.index)
        self.assertEqual('c', ps.current_char)
        self.assertEqual('c', ps.current_peek)

        self.assertEqual('d', ps.peek())
        self.assertEqual(1, ps.peek_offset)
        self.assertEqual(2, ps.index)

        self.assertEqual('d', ps.next())
        self.assertEqual(0, ps.peek_offset)
        self.assertEqual(3, ps.index)
        self.assertEqual('d', ps.current_char)
        self.assertEqual('d', ps.current_peek)

        self.assertEqual(None, ps.peek())
        self.assertEqual(1, ps.peek_offset)
        self.assertEqual(3, ps.index)
        self.assertEqual('d', ps.current_char)
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

        self.assertEqual('c', ps.current_char)
        self.assertEqual('c', ps.current_peek)
        self.assertEqual(0, ps.peek_offset)
        self.assertEqual(2, ps.index)

        ps.peek()

        self.assertEqual('c', ps.current_char)
        self.assertEqual('d', ps.current_peek)
        self.assertEqual(1, ps.peek_offset)
        self.assertEqual(2, ps.index)

        ps.next()

        self.assertEqual('d', ps.current_char)
        self.assertEqual('d', ps.current_peek)
        self.assertEqual(0, ps.peek_offset)
        self.assertEqual(3, ps.index)

    def test_reset_peek(self):
        ps = ParserStream("abcd")

        ps.next()
        ps.peek()
        ps.peek()
        ps.reset_peek()

        self.assertEqual('b', ps.current_char)
        self.assertEqual('b', ps.current_peek)
        self.assertEqual(0, ps.peek_offset)
        self.assertEqual(1, ps.index)

        ps.peek()

        self.assertEqual('b', ps.current_char)
        self.assertEqual('c', ps.current_peek)
        self.assertEqual(1, ps.peek_offset)
        self.assertEqual(1, ps.index)

        ps.peek()
        ps.peek()
        ps.peek()
        ps.reset_peek()

        self.assertEqual('b', ps.current_char)
        self.assertEqual('b', ps.current_peek)
        self.assertEqual(0, ps.peek_offset)
        self.assertEqual(1, ps.index)

        self.assertEqual('c', ps.peek())
        self.assertEqual('b', ps.current_char)
        self.assertEqual('c', ps.current_peek)
        self.assertEqual(1, ps.peek_offset)
        self.assertEqual(1, ps.index)

        self.assertEqual('d', ps.peek())
        self.assertEqual(None, ps.peek())
