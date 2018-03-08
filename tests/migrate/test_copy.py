# coding=utf8
from __future__ import unicode_literals

import unittest
from compare_locales.parser import PropertiesParser, DTDParser

import fluent.syntax.ast as FTL
from fluent.migrate.util import parse, ftl_message_to_json
from fluent.migrate.transforms import evaluate, COPY


class MockContext(unittest.TestCase):
    maxDiff = None

    def get_source(self, path, key):
        # Ignore path (test.properties) and get translations from self.strings
        # defined in setUp.
        return self.strings.get(key, None).val


class TestCopy(MockContext):
    def setUp(self):
        self.strings = parse(PropertiesParser, '''
            foo = Foo
            empty =
            unicode.all = \\u0020
            unicode.begin1 = \\u0020Foo
            unicode.begin2 = \\u0020\\u0020Foo
            unicode.end1 = Foo\\u0020
            unicode.end2 = Foo\\u0020\\u0020
        ''')

    def test_copy(self):
        msg = FTL.Message(
            FTL.Identifier('foo'),
            value=COPY('test.properties', 'foo')
        )

        self.assertEqual(
            evaluate(self, msg).to_json(),
            ftl_message_to_json('''
                foo = Foo
            ''')
        )

    def test_copy_empty(self):
        msg = FTL.Message(
            FTL.Identifier('empty'),
            value=COPY('test.properties', 'empty')
        )

        self.assertEqual(
            evaluate(self, msg).to_json(),
            ftl_message_to_json('''
                empty = {""}
            ''')
        )

    def test_copy_escape_unicode_all(self):
        msg = FTL.Message(
            FTL.Identifier('unicode-all'),
            value=COPY('test.properties', 'unicode.all')
        )

        self.assertEqual(
            evaluate(self, msg).to_json(),
            ftl_message_to_json('''
                unicode-all = {" "}
            ''')
        )

    def test_copy_escape_unicode_begin(self):
        msg = FTL.Message(
            FTL.Identifier('unicode-begin'),
            value=COPY('test.properties', 'unicode.begin1')
        )

        self.assertEqual(
            evaluate(self, msg).to_json(),
            ftl_message_to_json('''
                unicode-begin = {" "}Foo
            ''')
        )

    def test_copy_escape_unicode_begin_many(self):
        msg = FTL.Message(
            FTL.Identifier('unicode-begin'),
            value=COPY('test.properties', 'unicode.begin2')
        )

        self.assertEqual(
            evaluate(self, msg).to_json(),
            ftl_message_to_json('''
                unicode-begin = {"  "}Foo
            ''')
        )

    def test_copy_escape_unicode_end(self):
        msg = FTL.Message(
            FTL.Identifier('unicode-end'),
            value=COPY('test.properties', 'unicode.end1')
        )

        self.assertEqual(
            evaluate(self, msg).to_json(),
            ftl_message_to_json('''
                unicode-end = Foo{" "}
            ''')
        )

    def test_copy_escape_unicode_end_many(self):
        msg = FTL.Message(
            FTL.Identifier('unicode-end'),
            value=COPY('test.properties', 'unicode.end2')
        )

        self.assertEqual(
            evaluate(self, msg).to_json(),
            ftl_message_to_json('''
                unicode-end = Foo{"  "}
            ''')
        )


class TestCopyAttributes(MockContext):
    def setUp(self):
        self.strings = parse(DTDParser, '''
            <!ENTITY checkForUpdatesButton.label       "Check for updates">
            <!ENTITY checkForUpdatesButton.accesskey   "C">
            <!ENTITY checkForUpdatesButton.empty   "">
        ''')

    def test_copy_accesskey(self):
        msg = FTL.Message(
            FTL.Identifier('check-for-updates'),
            attributes=[
                FTL.Attribute(
                    FTL.Identifier('label'),
                    COPY('test.properties', 'checkForUpdatesButton.label')
                ),
                FTL.Attribute(
                    FTL.Identifier('accesskey'),
                    COPY(
                        'test.properties', 'checkForUpdatesButton.accesskey'
                    )
                ),
                FTL.Attribute(
                    FTL.Identifier('empty'),
                    COPY(
                        'test.properties', 'checkForUpdatesButton.empty'
                    )
                ),
            ]
        )

        self.assertEqual(
            evaluate(self, msg).to_json(),
            ftl_message_to_json('''
                check-for-updates =
                  .label = Check for updates
                  .accesskey = C
                  .empty = {""}
            ''')
        )


if __name__ == '__main__':
    unittest.main()
