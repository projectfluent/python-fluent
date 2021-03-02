import os
import json
import codecs
import unittest

from fluent.syntax import parse


def read_file(path):
    with codecs.open(path, 'r', encoding='utf-8') as file:
        text = file.read()
    return text


fixtures = os.path.join(
    os.path.dirname(__file__), 'fixtures_reference')


class TestReferenceMeta(type):
    def __new__(mcs, name, bases, attrs):

        def remove_untested(obj):
            if obj['type'] == 'Junk':
                obj['annotations'] = []
            if 'span' in obj:
                del obj['span']
            return obj

        def gen_test(file_name):
            def test(self):
                ftl_path = os.path.join(fixtures, file_name + '.ftl')
                ast_path = os.path.join(fixtures, file_name + '.json')

                source = read_file(ftl_path)
                expected = read_file(ast_path)

                ast = parse(source)
                self.assertEqual(
                    ast.to_json(remove_untested), json.loads(expected))

            return test

        for f in os.listdir(fixtures):
            file_name, ext = os.path.splitext(f)

            if ext != '.ftl':
                continue

            # Skip fixtures which are known to differ between the reference
            # parser and the tooling parser.
            if file_name in ('leading_dots', 'variant_lists'):
                continue

            test_name = f'test_{file_name}'
            attrs[test_name] = gen_test(file_name)

        return type.__new__(mcs, name, bases, attrs)


class TestReference(unittest.TestCase, metaclass=TestReferenceMeta):
    maxDiff = None
