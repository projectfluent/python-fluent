import unittest
import sys

sys.path.append('.')

from fluent.syntax.stream import ParserStream

class TestParserStream(unittest.TestCase):

    def test_next(self):
        ps = ParserStream("abcd")

        self.assertEqual('a', ps.current())
        self.assertEqual(0, ps.get_index())

        self.assertEqual('b', ps.next())
        self.assertEqual('b', ps.current())
        self.assertEqual(1, ps.get_index())

        self.assertEqual('c', ps.next())
        self.assertEqual('c', ps.current())
        self.assertEqual(2, ps.get_index())

        self.assertEqual('d', ps.next())
        self.assertEqual('d', ps.current())
        self.assertEqual(3, ps.get_index())

        self.assertEqual(None, ps.next())
        self.assertEqual(None, ps.current())
        self.assertEqual(4, ps.get_index())

    def test_peek(self):
        ps = ParserStream("abcd")

        self.assertEqual('a', ps.current_peek())
        self.assertEqual(0, ps.get_peek_index())

        self.assertEqual('b', ps.peek())
        self.assertEqual('b', ps.current_peek())
        self.assertEqual(1, ps.get_peek_index())

        self.assertEqual('c', ps.peek())
        self.assertEqual('c', ps.current_peek())
        self.assertEqual(2, ps.get_peek_index())

        self.assertEqual('d', ps.peek())
        self.assertEqual('d', ps.current_peek())
        self.assertEqual(3, ps.get_peek_index())

        self.assertEqual(None, ps.peek())
        self.assertEqual(None, ps.current_peek())
        self.assertEqual(4, ps.get_peek_index())

    def test_peek_and_next(self):
        ps = ParserStream("abcd")

        self.assertEqual('b', ps.peek())
        self.assertEqual(1, ps.get_peek_index())
        self.assertEqual(0, ps.get_index())

        self.assertEqual('b', ps.next())
        self.assertEqual(1, ps.get_peek_index())
        self.assertEqual(1, ps.get_index())

        self.assertEqual('c', ps.peek())
        self.assertEqual(2, ps.get_peek_index())
        self.assertEqual(1, ps.get_index())

        self.assertEqual('c', ps.next())
        self.assertEqual(2, ps.get_peek_index())
        self.assertEqual(2, ps.get_index())
        self.assertEqual('c', ps.current())
        self.assertEqual('c', ps.current_peek())

        self.assertEqual('d', ps.peek())
        self.assertEqual(3, ps.get_peek_index())
        self.assertEqual(2, ps.get_index())

        self.assertEqual('d', ps.next())
        self.assertEqual(3, ps.get_peek_index())
        self.assertEqual(3, ps.get_index())
        self.assertEqual('d', ps.current())
        self.assertEqual('d', ps.current_peek())

        self.assertEqual(None, ps.peek())
        self.assertEqual(4, ps.get_peek_index())
        self.assertEqual(3, ps.get_index())
        self.assertEqual('d', ps.current())
        self.assertEqual(None, ps.current_peek())

        self.assertEqual(None, ps.peek())
        self.assertEqual(4, ps.get_peek_index())
        self.assertEqual(3, ps.get_index())

        self.assertEqual(None, ps.next())
        self.assertEqual(4, ps.get_peek_index())
        self.assertEqual(4, ps.get_index())

    def test_skip_to_peek(self):
        ps = ParserStream("abcd")

        ps.peek()
        ps.peek()

        ps.skip_to_peek()

        self.assertEqual('c', ps.current())
        self.assertEqual('c', ps.current_peek())
        self.assertEqual(2, ps.get_peek_index())
        self.assertEqual(2, ps.get_index())

        ps.peek()

        self.assertEqual('c', ps.current())
        self.assertEqual('d', ps.current_peek())
        self.assertEqual(3, ps.get_peek_index())
        self.assertEqual(2, ps.get_index())

        ps.next()

        self.assertEqual('d', ps.current())
        self.assertEqual('d', ps.current_peek())
        self.assertEqual(3, ps.get_peek_index())
        self.assertEqual(3, ps.get_index())

    def test_reset_peek(self):
        ps = ParserStream("abcd")

        ps.next()
        ps.peek()
        ps.peek()
        ps.reset_peek()

        self.assertEqual('b', ps.current())
        self.assertEqual('b', ps.current_peek())
        self.assertEqual(1, ps.get_peek_index())
        self.assertEqual(1, ps.get_index())

        ps.peek()

        self.assertEqual('b', ps.current())
        self.assertEqual('c', ps.current_peek())
        self.assertEqual(2, ps.get_peek_index())
        self.assertEqual(1, ps.get_index())

        ps.peek()
        ps.peek()
        ps.peek()
        ps.reset_peek()

        self.assertEqual('b', ps.current())
        self.assertEqual('b', ps.current_peek())
        self.assertEqual(1, ps.get_peek_index())
        self.assertEqual(1, ps.get_index())

        self.assertEqual('c', ps.peek())
        self.assertEqual('b', ps.current())
        self.assertEqual('c', ps.current_peek())
        self.assertEqual(2, ps.get_peek_index())
        self.assertEqual(1, ps.get_index())

        self.assertEqual('d', ps.peek())
        self.assertEqual(None, ps.peek())

    def test_reset_peek(self):
        ps = ParserStream("abcd")

        ps.next()
        ps.peek()

        self.assertEqual(ps.peek_char_is('d'), True)

        self.assertEqual('b', ps.current())
        self.assertEqual('c', ps.current_peek())

        ps.skip_to_peek()

        self.assertEqual('c', ps.current())



if __name__ == '__main__':
    unittest.main()
