from __future__ import unicode_literals

import codecs
from collections import defaultdict
import os
import unittest
import timeit

from fluent.syntax.parser import FluentParser
from fluent.syntax import ast
from tests.syntax import dedent_ftl


class MockVisitor(ast.Visitor):
    def __init__(self):
        self.calls = defaultdict(int)
        self.pattern_calls = 0

    def generic_visit(self, node):
        self.calls[type(node).__name__] += 1
        return super(MockVisitor, self).generic_visit(node)

    def visit_Pattern(self, node):
        self.pattern_calls += 1
        return False


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


class WordCounter(object):
    def __init__(self):
        self.word_count = 0
    def __call__(self, node):
        if isinstance(node, ast.TextElement):
            self.word_count += len(node.value.split())
        return node

class VisitorCounter(ast.Visitor):
    def __init__(self):
        self.word_count = 0

    def generic_visit(self, node):
        return not isinstance(node, (ast.Span, ast.Annotation))

    def visit_TextElement(self, node):
        self.word_count += len(node.value.split())
        return False


class ReplaceText(object):
    def __init__(self, before, after):
        self.before = before
        self.after = after
    def __call__(self, node):
        """Perform find and replace on text values only"""
        if type(node) == ast.TextElement:
            node.value = node.value.replace(self.before, self.after)
        return node



class TestPerf(unittest.TestCase):
    def setUp(self):
        parser = FluentParser()
        workload = os.path.join(
            os.path.dirname(__file__), 'fixtures_perf', 'workload-low.ftl'
        )
        with codecs.open(workload, encoding='utf-8') as f:
            self.resource = parser.parse(f.read())

    def test_traverse(self):
        counter = WordCounter()
        self.resource.traverse(counter)
        self.assertEqual(counter.word_count, 277)

    def test_visitor(self):
        counter = VisitorCounter()
        counter.visit(self.resource)
        self.assertEqual(counter.word_count, 277)

    def test_edit_traverse(self):
        edited = self.resource.traverse(ReplaceText('Tab', 'Reiter'))
        self.assertEqual(
            edited.body[4].attributes[0].value.elements[0].value,
            'New Reiter'
        )


def gather_stats(method, repeat=10, number=50):
    t = timeit.Timer(
        setup='''
from tests.syntax import test_visitor
test = test_visitor.TestPerf('test_{}')
test.setUp()
'''.format(method),
        stmt='test.test_{}()'.format(method)
    )
    return [
        result/number for result in
        t.repeat(repeat=repeat, number=number)
    ]



if __name__=='__main__':
    for m in ('traverse', 'visitor', 'edit_traverse'):
        results = gather_stats(m)
        try:
            import statistics
            print("{}:\t{}".format(m, statistics.mean(results)))
        except ImportError:
            print("{}:\t{}".format(m, sum(results)/len(results)))
