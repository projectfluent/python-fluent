from json import loads
from os import listdir
from os.path import dirname, join, splitext

import pytest

from fluent.syntax import parse

fixtures_dir = join(dirname(__file__), "fixtures_structure")
fixture_names = [
    fp[0] for fn in listdir(fixtures_dir) if (fp := splitext(fn))[1] == ".ftl"
]


@pytest.mark.parametrize("name", fixture_names)
def test_structure_with_spans(name):
    source, expected = read_fixtures(name)
    ast = parse(source, with_spans=True)
    assert ast.to_json() == expected


@pytest.mark.parametrize("name", fixture_names)
def test_structure_without_spans(name):
    source, expected = read_fixtures(name)
    ast = parse(source, with_spans=False)
    assert ast.to_json() == without_spans(expected)


def read_fixtures(name: str):
    ftl_path = join(fixtures_dir, name + ".ftl")
    ast_path = join(fixtures_dir, name + ".json")

    with open(ftl_path, "r", encoding="utf-8", newline="\n") as file:
        source = file.read()
    with open(ast_path, "r", encoding="utf-8", newline="\n") as file:
        expected = loads(file.read())

    return source, expected


def without_spans(expected):
    """
    Recursively replace all of the spans with None.
    """
    if isinstance(expected, dict):
        return {
            key: None if key == "span" else without_spans(value)
            for key, value in expected.items()
        }
    elif isinstance(expected, list):
        return [without_spans(item) for item in expected]
    else:
        return expected
