from __future__ import unicode_literals
import os
import sys
import json
import codecs
import unittest

sys.path.append('.')

from fluent.syntax.parser import parse


def read_file(path):
    with codecs.open(path, 'r', encoding='utf-8') as file:
        text = file.read()
    return text


fixtures = os.path.join(
    os.path.dirname(__file__), 'fixtures_structure'
)


class TestStructureMeta(type):
    def __new__(mcs, name, bases, attrs):

        def gen_test(file_name):
            def test(self):
                ftl_path = os.path.join(fixtures, file_name + '.ftl')
                ast_path = os.path.join(fixtures, file_name + '.json')

                source = read_file(ftl_path)
                expected = read_file(ast_path)

                ast = parse(source)

                self.assertEqual(ast.to_json(), json.loads(expected))

            return test

        for f in os.listdir(fixtures):
            file_name, ext = os.path.splitext(f)

            if ext != '.ftl':
                continue

            test_name = 'test_{}'.format(file_name)
            attrs[test_name] = gen_test(file_name)

        return type.__new__(mcs, name, bases, attrs)


class TestStructure(unittest.TestCase):
    __metaclass__ = TestStructureMeta
