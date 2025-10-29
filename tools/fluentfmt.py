#!/usr/bin/python

import sys

from fluent.syntax import parse, serialize

sys.path.append("./")


def read_file(path):
    with open(path, "r", encoding="utf-8") as file:
        text = file.read()
    return text


def pretty_print(fileType, data):
    ast = parse(data)
    print(serialize(ast))


if __name__ == "__main__":
    file_type = "ftl"
    f = read_file(sys.argv[1])
    pretty_print(file_type, f)
