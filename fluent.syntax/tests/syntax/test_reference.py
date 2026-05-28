from json import loads
from os import listdir
from os.path import dirname, join, splitext

import pytest

from fluent.syntax import parse

fixtures_dir = join(dirname(__file__), "fixtures_reference")
fixture_names = [
    fp[0] for fn in listdir(fixtures_dir) if (fp := splitext(fn))[1] == ".ftl"
]


@pytest.mark.parametrize("name", fixture_names)
def test_reference(name):
    if name in ("leading_dots",):
        pytest.skip("Known difference between reference and tooling parsers")

    ftl_path = join(fixtures_dir, name + ".ftl")
    ast_path = join(fixtures_dir, name + ".json")

    with open(ftl_path, "r", encoding="utf-8", newline="\n") as file:
        ast = parse(file.read())
    with open(ast_path, "r", encoding="utf-8", newline="\n") as file:
        expected = loads(file.read())

    assert ast.to_json(remove_untested) == expected


def remove_untested(obj):
    if obj["type"] == "Junk":
        obj["annotations"] = []
    if "span" in obj:
        del obj["span"]
    return obj
