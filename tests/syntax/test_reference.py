from __future__ import unicode_literals
import six.moves
from six import with_metaclass

import os
import json
import codecs
import unittest

from fluent.syntax import parse
from fluent.syntax import ast


def read_file(path):
    with codecs.open(path, 'r', encoding='utf-8') as file:
        text = file.read()
    return text


fixtures = os.path.join(
    os.environ['REFERENCE'], 'test', 'fixtures'
)


class TestReferenceMeta(type):
    def __new__(mcs, name, bases, attrs):

        def gen_test(file_name):
            def test(self):
                ftl_path = os.path.join(fixtures, file_name + '.ftl')
                ast_path = os.path.join(fixtures, file_name + '.json')

                source = read_file(ftl_path)
                expected = read_file(ast_path)

                actual = parse(source, with_spans=False)
                expected = ast.from_json(json.loads(expected))

                for a, b in six.moves.zip_longest(actual.body, expected.body):
                    if a is None or b is None or not a.equals(b):
                        self.assertEqual(
                            a.to_json() if a is not None else None,
                            b.to_json() if b is not None else None
                        )

            return test

        for f in os.listdir(fixtures):
            file_name, ext = os.path.splitext(f)

            if ext != '.ftl':
                continue

            test_name = 'test_{}'.format(file_name)
            attrs[test_name] = gen_test(file_name)

        return type.__new__(mcs, name, bases, attrs)


class TestReference(with_metaclass(TestReferenceMeta, unittest.TestCase)):
    maxDiff = None
