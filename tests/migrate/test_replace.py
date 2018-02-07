# coding=utf8
from __future__ import unicode_literals

import unittest
from compare_locales.parser import PropertiesParser

import fluent.syntax.ast as FTL
from fluent.migrate.util import parse, ftl_message_to_json
from fluent.migrate.helpers import EXTERNAL_ARGUMENT
from fluent.migrate.transforms import evaluate, REPLACE


class MockContext(unittest.TestCase):
    maxDiff = None

    def get_source(self, path, key):
        # Ignore path (test.properties) and get translations from self.strings
        # defined in setUp.
        return self.strings.get(key, None).val


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
                'test.properties',
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
                'test.properties',
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
                'test.properties',
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
                'test.properties',
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
                'test.properties',
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
                'test.properties',
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

    def test_replace_with_placeable(self):
        msg = FTL.Message(
            FTL.Identifier(u'hello'),
            value=REPLACE(
                'test.properties',
                'hello',
                {
                    '#1': FTL.Placeable(
                        EXTERNAL_ARGUMENT('user')
                    )
                }
            )
        )

        self.assertEqual(
            evaluate(self, msg).to_json(),
            ftl_message_to_json('''
                hello = Hello, { $user }!
            ''')
        )

    def test_replace_with_text_element(self):
        msg = FTL.Message(
            FTL.Identifier(u'hello'),
            value=REPLACE(
                'test.properties',
                'hello',
                {
                    '#1': FTL.TextElement('you')
                }
            )
        )

        self.assertEqual(
            evaluate(self, msg).to_json(),
            ftl_message_to_json('''
                hello = Hello, you!
            ''')
        )

    def test_replace_with_pattern(self):
        msg = FTL.Message(
            FTL.Identifier(u'hello'),
            value=REPLACE(
                'test.properties',
                'hello',
                {
                    '#1': FTL.Pattern(
                        elements=[
                            FTL.TextElement('<img> '),
                            FTL.Placeable(
                                EXTERNAL_ARGUMENT('user')
                            )
                        ]
                    )
                }
            )
        )

        self.assertEqual(
            evaluate(self, msg).to_json(),
            ftl_message_to_json('''
                hello = Hello, <img> { $user }!
            ''')
        )


if __name__ == '__main__':
    unittest.main()
