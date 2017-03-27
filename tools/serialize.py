#!/usr/bin/python

import sys
import json

sys.path.append('./')
import codecs
import fluent.syntax.ast
import fluent.syntax.serializer


def read_json(path):
    with codecs.open(path, 'r', encoding='utf-8') as file:
        return json.load(file)


def pretty_print(fileType, data):
    ast = fluent.syntax.ast.from_json(data)
    print(fluent.syntax.serializer.serialize(ast))

if __name__ == "__main__":
    file_type = 'ftl'
    f = read_json(sys.argv[1])
    pretty_print(file_type, f)
