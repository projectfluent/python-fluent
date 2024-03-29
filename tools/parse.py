#!/usr/bin/python

import codecs
import json
import sys

from fluent.syntax import parse

sys.path.append("./")


def read_file(path):
    with codecs.open(path, "r", encoding="utf-8") as file:
        text = file.read()
    return text


def print_ast(fileType, data):
    ast = parse(data)
    print(json.dumps(ast.to_json(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    file_type = "ftl"
    f = read_file(sys.argv[1])
    print_ast(file_type, f)
