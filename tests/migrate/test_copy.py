# coding=utf8
from __future__ import unicode_literals

import unittest
from compare_locales.parser import PropertiesParser, DTDParser

import fluent.syntax.ast as FTL
from fluent.migrate.util import parse, ftl_message_to_json
from fluent.migrate.transforms import evaluate, COPY


class MockContext(unittest.TestCase):
    def get_source(self, path, key):
        # Ignore path (test.properties) and get translations from self.strings
        # defined in setUp.
        return self.strings.get(key, None).val


class TestCopy(MockContext):
    def setUp(self):
        self.strings = parse(PropertiesParser, '''
            foo = Foo
            foo.unicode.begin = \\u0020Foo
            foo.unicode.end = Foo\\u0020
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

    @unittest.skip('Parser/Serializer trim whitespace')
    def test_copy_escape_unicode_begin(self):
        msg = FTL.Message(
            FTL.Identifier('foo-unicode-begin'),
            value=COPY('test.properties', 'foo.unicode.begin')
        )

        self.assertEqual(
            evaluate(self, msg).to_json(),
            ftl_message_to_json('''
                foo-unicode-begin = Foo
            ''')
        )

    @unittest.skip('Parser/Serializer trim whitespace')
    def test_copy_escape_unicode_end(self):
        msg = FTL.Message(
            FTL.Identifier('foo-unicode-end'),
            value=COPY('test.properties', 'foo.unicode.end')
        )

        self.assertEqual(
            evaluate(self, msg).to_json(),
            ftl_message_to_json('''
                foo-unicode-end = Foo
            ''')
        )


class TestCopyAttributes(MockContext):
    def setUp(self):
        self.strings = parse(DTDParser, '''
            <!ENTITY checkForUpdatesButton.label       "Check for updates">
            <!ENTITY checkForUpdatesButton.accesskey   "C">
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
            ]
        )

        self.assertEqual(
            evaluate(self, msg).to_json(),
            ftl_message_to_json('''
                check-for-updates
                  .label = Check for updates
                  .accesskey = C
            ''')
        )


if __name__ == '__main__':
    unittest.main()
