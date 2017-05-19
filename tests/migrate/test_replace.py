# coding=utf8
from __future__ import unicode_literals

import unittest

import fluent.syntax.ast as FTL
try:
    from compare_locales.parser import PropertiesParser
except ImportError:
    PropertiesParser = None

from fluent.migrate.util import parse, ftl_message_to_json
from fluent.migrate.helpers import EXTERNAL_ARGUMENT
from fluent.migrate.transforms import evaluate, REPLACE


class MockContext(unittest.TestCase):
    def get_source(self, path, key):
        return self.strings.get(key, None).get_val()


@unittest.skipUnless(PropertiesParser, 'compare-locales required')
class TestReplace(MockContext):
    def setUp(self):
        self.strings = parse(PropertiesParser, '''
            hello = Hello, #1!
            welcome = Welcome, #1, to #2!
            first = #1 Bar
            last = Foo #1
        ''')

    def test_replace_one(self):
        msg = FTL.Message(
            FTL.Identifier(u'hello'),
            value=REPLACE(
                self.strings,
                'hello',
                {
                    '#1': EXTERNAL_ARGUMENT('username')
                }
            )
        )

        self.assertEqual(
            evaluate(self, msg).to_json(),
            ftl_message_to_json('''
                hello = Hello, { $username }!
            ''')
        )

    def test_replace_two(self):
        msg = FTL.Message(
            FTL.Identifier(u'welcome'),
            value=REPLACE(
                self.strings,
                'welcome',
                {
                    '#1': EXTERNAL_ARGUMENT('username'),
                    '#2': EXTERNAL_ARGUMENT('appname')
                }
            )
        )

        self.assertEqual(
            evaluate(self, msg).to_json(),
            ftl_message_to_json('''
                welcome = Welcome, { $username }, to { $appname }!
            ''')
        )

    def test_replace_too_many(self):
        msg = FTL.Message(
            FTL.Identifier(u'welcome'),
            value=REPLACE(
                self.strings,
                'welcome',
                {
                    '#1': EXTERNAL_ARGUMENT('username'),
                    '#2': EXTERNAL_ARGUMENT('appname'),
                    '#3': EXTERNAL_ARGUMENT('extraname')
                }
            )
        )

        self.assertEqual(
            evaluate(self, msg).to_json(),
            ftl_message_to_json('''
                welcome = Welcome, { $username }, to { $appname }!
            ''')
        )

    def test_replace_too_few(self):
        msg = FTL.Message(
            FTL.Identifier(u'welcome'),
            value=REPLACE(
                self.strings,
                'welcome',
                {
                    '#1': EXTERNAL_ARGUMENT('username')
                }
            )
        )

        self.assertEqual(
            evaluate(self, msg).to_json(),
            ftl_message_to_json('''
                welcome = Welcome, { $username }, to #2!
            ''')
        )

    def test_replace_first(self):
        msg = FTL.Message(
            FTL.Identifier(u'first'),
            value=REPLACE(
                self.strings,
                'first',
                {
                    '#1': EXTERNAL_ARGUMENT('foo')
                }
            )
        )

        self.assertEqual(
            evaluate(self, msg).to_json(),
            ftl_message_to_json('''
                first = { $foo } Bar
            ''')
        )

    def test_replace_last(self):
        msg = FTL.Message(
            FTL.Identifier(u'last'),
            value=REPLACE(
                self.strings,
                'last',
                {
                    '#1': EXTERNAL_ARGUMENT('bar')
                }
            )
        )

        self.assertEqual(
            evaluate(self, msg).to_json(),
            ftl_message_to_json('''
                last = Foo { $bar }
            ''')
        )


if __name__ == '__main__':
    unittest.main()
