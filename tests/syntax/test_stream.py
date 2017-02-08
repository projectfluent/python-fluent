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

if __name__ == '__main__':
    unittest.main()
