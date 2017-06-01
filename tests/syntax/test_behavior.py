from __future__ import unicode_literals
import os
import re
import sys
import codecs
import unittest

sys.path.append('.')

from fluent.syntax import parse


sigil = r'^\/\/~ '
re_directive = re.compile(r'{}(.*)[\n$]'.format(sigil), re.MULTILINE)


def preprocess(source):
    return [
        re.findall(re_directive, source),
        re.sub(re_directive, '', source)
    ]


def get_code_name(code):
    first = code[0]
    if first == 'E':
        return 'ERROR {}'.format(code)
    if first == 'W':
        return 'ERROR {}'.format(code)
    if first == 'H':
        return 'ERROR {}'.format(code)
    raise Exception('Unknown Annotation code')


def serialize_annotation(annot):
    parts = [get_code_name(annot.code)]
    span = annot.span

    if (span.start == span.end):
        parts.append('pos {}'.format(span.start))
    else:
        parts.append(
            'start {}'.format(span.start),
            'end {}'.format(span.end)
        )

    if len(annot.args):
        pretty_args = ' '.join([
            '"{}"'.format(arg)
            for arg in annot.args
        ])
        parts.append('args {}'.format(pretty_args))

    return ', '.join(parts)


def read_file(path):
    with codecs.open(path, 'r', encoding='utf-8') as file:
        text = file.read()
    return text


fixtures = os.path.join(
    os.path.dirname(__file__), 'fixtures_behavior'
)


class TestBehaviorMeta(type):
    def __new__(mcs, name, bases, attrs):

        def gen_test(file_name):
            def test(self):
                ftl_path = os.path.join(fixtures, file_name + '.ftl')
                ftl_file = read_file(ftl_path)

                [expected_directives, source] = preprocess(ftl_file)
                expected = '{}\n'.format('\n'.join(expected_directives))
                ast = parse(source)
                actual_directives = [
                    serialize_annotation(annot)
                    for entry in ast.body
                    for annot in entry.annotations
                ]
                actual = '{}\n'.format('\n'.join(actual_directives))

                self.assertEqual(actual, expected)

            return test

        for f in os.listdir(fixtures):
            file_name, ext = os.path.splitext(f)

            if ext != '.ftl':
                continue

            test_name = 'test_{}'.format(file_name)
            attrs[test_name] = gen_test(file_name)

        return type.__new__(mcs, name, bases, attrs)


class TestBehavior(unittest.TestCase):
    maxDiff = None

    __metaclass__ = TestBehaviorMeta
