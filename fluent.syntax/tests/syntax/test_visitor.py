from collections import defaultdict
import unittest

from fluent.syntax.parser import FluentParser
from fluent.syntax import ast
from fluent.syntax import visitor
from tests.syntax import dedent_ftl


class MockVisitor(visitor.Visitor):
    def __init__(self):
        self.calls = defaultdict(int)
        self.pattern_calls = 0

    def generic_visit(self, node):
        self.calls[type(node).__name__] += 1
        super().generic_visit(node)

    def visit_Pattern(self, node):
        self.pattern_calls += 1


class TestVisitor(unittest.TestCase):
    def test_resource(self):
        resource = FluentParser().parse(dedent_ftl('''\
        one = Message
        # Comment
        two = Messages
        three = Messages with
            .an = Attribute
        '''))
        mv = MockVisitor()
        mv.visit(resource)
        self.assertEqual(mv.pattern_calls, 4)
        self.assertDictEqual(
            mv.calls,
            {
                'Resource': 1,
                'Comment': 1,
                'Message': 3,
                'Identifier': 4,
                'Attribute': 1,
                'Span': 10,
            }
        )


class TestTransformer(unittest.TestCase):
    def test(self):
        resource = FluentParser().parse(dedent_ftl('''\
        one = Message
        two = Messages
        three = Has a
            .an = Message string in the Attribute
        '''))
        prior_res_id = id(resource)
        prior_msg_id = id(resource.body[1].value)
        backup = resource.clone()
        transformed = ReplaceTransformer('Message', 'Term').visit(resource)
        self.assertEqual(prior_res_id, id(transformed))
        self.assertEqual(
            prior_msg_id,
            id(transformed.body[1].value)
        )
        self.assertFalse(transformed.equals(backup))
        self.assertEqual(
            transformed.body[1].value.elements[0].value,
            'Terms'
        )


class WordCounter:
    def __init__(self):
        self.word_count = 0

    def __call__(self, node):
        if isinstance(node, ast.TextElement):
            self.word_count += len(node.value.split())
        return node


class VisitorCounter(visitor.Visitor):
    def __init__(self):
        self.word_count = 0

    def generic_visit(self, node):
        if not isinstance(node, (ast.Span, ast.Annotation)):
            super().generic_visit(node)

    def visit_TextElement(self, node):
        self.word_count += len(node.value.split())


class ReplaceText:
    def __init__(self, before, after):
        self.before = before
        self.after = after

    def __call__(self, node):
        """Perform find and replace on text values only"""
        if type(node) == ast.TextElement:
            node.value = node.value.replace(self.before, self.after)
        return node


class ReplaceTransformer(visitor.Transformer):
    def __init__(self, before, after):
        self.before = before
        self.after = after

    def generic_visit(self, node):
        if isinstance(node, (ast.Span, ast.Annotation)):
            return node
        return super().generic_visit(node)

    def visit_TextElement(self, node):
        """Perform find and replace on text values only"""
        node.value = node.value.replace(self.before, self.after)
        return node
