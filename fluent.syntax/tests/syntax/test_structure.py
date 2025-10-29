import json
import os
import unittest

from fluent.syntax import parse


def read_file(path):
    with open(path, "r", encoding="utf-8") as file:
        text = file.read()
    return text


def without_spans(expected):
    """
    Given an expected JSON fragment with span information, recursively replace all of the spans
    with None.
    """
    if isinstance(expected, dict):
        result = {}
        for key, value in expected.items():
            if key == "span":
                result[key] = None
            else:
                result[key] = without_spans(value)

        return result
    elif isinstance(expected, list):
        return [without_spans(item) for item in expected]
    else:
        # We have been passed something which would not have span information in it
        return expected


fixtures = os.path.join(os.path.dirname(__file__), "fixtures_structure")


class TestStructureMeta(type):
    def __new__(mcs, name, bases, attrs):

        def gen_test(file_name, with_spans):
            def test(self):
                ftl_path = os.path.join(fixtures, file_name + ".ftl")
                ast_path = os.path.join(fixtures, file_name + ".json")

                source = read_file(ftl_path)
                expected = json.loads(read_file(ast_path))

                if not with_spans:
                    expected = without_spans(expected)

                ast = parse(source, with_spans=with_spans)

                self.assertEqual(ast.to_json(), expected)

            return test

        for f in os.listdir(fixtures):
            file_name, ext = os.path.splitext(f)

            if ext != ".ftl":
                continue

            attrs[f"test_{file_name}_with_spans"] = gen_test(file_name, with_spans=True)
            attrs[f"test_{file_name}_without_spans"] = gen_test(file_name, with_spans=False)

        return type.__new__(mcs, name, bases, attrs)


class TestStructure(unittest.TestCase, metaclass=TestStructureMeta):
    maxDiff = None
