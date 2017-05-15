# coding=utf8
from __future__ import unicode_literals

import unittest

import fluent.syntax.ast as FTL
from fluent.util import fold
from fluent.migrate.transforms import CONCAT, LITERAL_FROM, SOURCE


def get_source(acc, cur):
    if isinstance(cur, SOURCE):
        return acc + ((cur.path, cur.key),)
    return acc


class TestTraverse(unittest.TestCase):
    def test_copy_concat(self):
        node = FTL.Message(
            FTL.Identifier('hello'),
            value=CONCAT(
                LITERAL_FROM('path1', 'key1'),
                LITERAL_FROM('path2', 'key2')
            )
        )

        result = node.traverse(lambda x: x)

        self.assertEqual(
            result.value.patterns[0].key,
            'key1'
        )
        self.assertEqual(
            result.value.patterns[1].key,
            'key2'
        )


class TestReduce(unittest.TestCase):
    def test_copy_value(self):
        node = FTL.Message(
            id=FTL.Identifier('key'),
            value=LITERAL_FROM('path', 'key')
        )

        self.assertEqual(
            fold(get_source, node, ()),
            (('path', 'key'),)
        )

    def test_copy_traits(self):
        node = FTL.Message(
            id=FTL.Identifier('key'),
            attributes=[
                FTL.Attribute(
                    FTL.Identifier('trait1'),
                    value=LITERAL_FROM('path1', 'key1')
                ),
                FTL.Attribute(
                    FTL.Identifier('trait2'),
                    value=LITERAL_FROM('path2', 'key2')
                )
            ]
        )

        self.assertEqual(
            fold(get_source, node, ()),
            (('path1', 'key1'), ('path2', 'key2'))
        )

    def test_copy_concat(self):
        node = FTL.Message(
            FTL.Identifier('hello'),
            value=CONCAT(
                LITERAL_FROM('path1', 'key1'),
                LITERAL_FROM('path2', 'key2')
            )
        )

        self.assertEqual(
            fold(get_source, node, ()),
            (('path1', 'key1'), ('path2', 'key2'))
        )
