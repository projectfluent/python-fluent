from __future__ import absolute_import, print_function, unicode_literals

from fluent.syntax import ast as FTL
from fluent.syntax import parse

from pygments.lexer import Lexer
from pygments.token import Token


class FluentLexer(Lexer):
    name = 'Fluent Lexer'
    aliases = ['fluent', 'ftl']
    filenames = ['*.ftl']

    def get_tokens_unprocessed(self, text):
        last_end = 0
        tokenizer = Tokenizer(text)
        for token in tokenizer.tokenize():
            node, start, token, span = token
            if start > last_end:
                yield last_end, Token.Punctuation, text[last_end:start]
            last_end = node.span.end
            yield start, token, span
        if last_end < len(text):
            yield last_end, Token.Punctuation, text[last_end:]


ATOMIC = {
    'Comment': Token.Comment.Multiline,
    'GroupComment': Token.Comment.Multiline,
    'ResourceComment': Token.Comment.Multiline,
    'Identifier': Token.Name.Constant,
    'TextElement': Token.Literal,
    'NumberLiteral': Token.Literal.Number,
    'StringLiteral': Token.Literal.String,
    'VariableReference': Token.Name.Variable,
    'Junk': Token.Generic.Error,
}


class Tokenizer(object):
    def __init__(self, text):
        self.text = text
        self.ast = parse(text)

    def tokenize(self, node=None):
        if node is None:
            node = self.ast
        if isinstance(node, (FTL.Annotation, FTL.Span)):
            return
        if isinstance(node, FTL.SyntaxNode):
            for token in self.tokenize_node(node):
                yield token
        elif isinstance(node, list):
            for child in node:
                for token in self.tokenize(child):
                    yield token

    def tokenize_node(self, node):
        nodename = type(node).__name__
        if nodename in ATOMIC:
            yield self._token(node, ATOMIC[nodename])
        else:
            tokenize = getattr(self, 'tokenize_{}'.format(nodename), self.generic_tokenize)
            for token in tokenize(node):
                yield token

    def generic_tokenize(self, node):
        children = [
            child for child in vars(node).values()
            if isinstance(child, (FTL.SyntaxNode, list)) and child != []
        ]
        children.sort(
            key=lambda child: child.span.start if isinstance(child, FTL.SyntaxNode) else child[0].span.start
        )
        for child in children:
            for token in self.tokenize(child):
                yield token

    def tokenize_Variant(self, node):
        yield self._token(node.key, Token.Name.Attribute)
        for token in self.tokenize(node.value):
            yield token

    def _token(self, node, token):
        return (
            node,
            node.span.start,
            token,
            self.text[node.span.start:node.span.end],
        )
