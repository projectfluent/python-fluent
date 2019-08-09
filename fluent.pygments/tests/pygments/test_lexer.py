from __future__ import absolute_import, print_function, unicode_literals

import unittest
from pygments.token import Token

from fluent.pygments.lexer import FluentLexer


class LexerTest(unittest.TestCase):
    def setUp(self):
        self.lexer = FluentLexer()

    def test_comment(self):
        fragment = '# comment\n'
        tokens = [
            (Token.Comment.Multiline, '# comment'),
            (Token.Punctuation, '\n'),
        ]
        self.assertEqual(tokens, list(self.lexer.get_tokens(fragment)))

    def test_message(self):
        fragment = 'msg = some value\n'
        tokens = [
            (Token.Name.Constant, 'msg'),
            (Token.Punctuation, ' = '),
            (Token.Literal, 'some value'),
            (Token.Punctuation, '\n'),
        ]
        self.assertEqual(tokens, list(self.lexer.get_tokens(fragment)))

    def test_message_with_comment(self):
        fragment = '# good comment\nmsg = some value\n'
        tokens = [
            (Token.Comment.Multiline, '# good comment'),
            (Token.Punctuation, '\n'),
            (Token.Name.Constant, 'msg'),
            (Token.Punctuation, ' = '),
            (Token.Literal, 'some value'),
            (Token.Punctuation, '\n'),
        ]
        self.assertEqual(tokens, list(self.lexer.get_tokens(fragment)))
