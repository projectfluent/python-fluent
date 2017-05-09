# coding=utf8
from __future__ import unicode_literals

import unittest

from fluent.migrate.changesets import convert_blame_to_changesets


class TestBlameToChangesets(unittest.TestCase):
    def test_convert(self):
        blame = {
            'authors': [
                'A',
                'B'
            ],
            'blame': {
                'path/one': {
                    'key1': [0, 1346095921.0],
                    'key2': [1, 1218121409.0]
                },
                'path/two': {
                    'key1': [1, 1440596526.0],
                    'key3': [0, 1346095921.0]
                }
            }
        }

        expected = [
            {
                'author': 'B',
                'first_commit': 1218121409.0,
                'changes': {
                    ('path/one', 'key2'),
                    ('path/two', 'key1'),
                }
            },
            {
                'author': 'A',
                'first_commit': 1346095921.0,
                'changes': {
                    ('path/one', 'key1'),
                    ('path/two', 'key3'),
                }
            },
        ]

        self.assertEqual(
            convert_blame_to_changesets(blame),
            expected
        )
