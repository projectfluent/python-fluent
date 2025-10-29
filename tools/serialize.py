#!/usr/bin/python

import json
import sys

from fluent.syntax import ast, serialize

sys.path.append("./")


def read_json(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def pretty_print(fileType, data):
    resource = ast.from_json(data)
    print(serialize(resource))


if __name__ == "__main__":
    file_type = "ftl"
    f = read_json(sys.argv[1])
    pretty_print(file_type, f)
