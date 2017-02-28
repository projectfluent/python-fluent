#!/usr/bin/python

import sys

sys.path.append('./')
import codecs
import fluent.syntax.parser
import fluent.syntax.serializer


def read_file(path):
    with codecs.open(path, 'r', encoding='utf-8') as file:
        text = file.read()
    return text


def pretty_print(fileType, data):
    [ast, _] = fluent.syntax.parser.parse(data)
    print(fluent.syntax.serializer.serialize(ast))

if __name__ == "__main__":
    file_type = 'ftl'
    f = read_file(sys.argv[1])
    pretty_print(file_type, f)
