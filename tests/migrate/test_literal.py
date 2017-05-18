# coding=utf8
from __future__ import unicode_literals

import unittest

import fluent.syntax.ast as FTL
try:
    from compare_locales.parser import PropertiesParser, DTDParser
except ImportError:
    PropertiesParser = DTDParser = None

from fluent.migrate.util import parse, ftl_message_to_json
from fluent.migrate.transforms import evaluate, COPY


class MockContext(unittest.TestCase):
    def get_source(self, path, key):
        return self.strings.get(key, None).get_val()


@unittest.skipUnless(PropertiesParser, 'compare-locales required')
class TestCopy(MockContext):
    def setUp(self):
        self.strings = parse(PropertiesParser, '''
            foo = Foo
            foo.unicode.middle = Foo\\u0020Bar
            foo.unicode.begin = \\u0020Foo
            foo.unicode.end = Foo\\u0020

            foo.html.entity = &lt;&#x21E7;&#x2318;K&gt;
        ''')

    def test_copy(self):
        msg = FTL.Message(
            FTL.Identifier('foo'),
            value=COPY(self.strings, 'foo')
        )

        self.assertEqual(
            evaluate(self, msg).to_json(),
            ftl_message_to_json('''
                foo = Foo
            ''')
        )

    def test_copy_escape_unicode_middle(self):
        msg = FTL.Message(
            FTL.Identifier('foo-unicode-middle'),
            value=COPY(self.strings, 'foo.unicode.middle')
        )

        self.assertEqual(
            evaluate(self, msg).to_json(),
            ftl_message_to_json('''
                foo-unicode-middle = Foo Bar
            ''')
        )

    @unittest.skip('Parser/Serializer trim whitespace')
    def test_copy_escape_unicode_begin(self):
        msg = FTL.Message(
            FTL.Identifier('foo-unicode-begin'),
            value=COPY(self.strings, 'foo.unicode.begin')
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
            value=COPY(self.strings, 'foo.unicode.end')
        )

        self.assertEqual(
            evaluate(self, msg).to_json(),
            ftl_message_to_json('''
                foo-unicode-end = Foo
            ''')
        )

    def test_copy_html_entity(self):
        msg = FTL.Message(
            FTL.Identifier('foo-html-entity'),
            value=COPY(self.strings, 'foo.html.entity')
        )

        self.assertEqual(
            evaluate(self, msg).to_json(),
            ftl_message_to_json('''
                foo-html-entity = &lt;&#x21E7;&#x2318;K&gt;
            ''')
        )


@unittest.skipUnless(DTDParser, 'compare-locales required')
class TestCopyTraits(MockContext):
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
                    COPY(self.strings, 'checkForUpdatesButton.label')
                ),
                FTL.Attribute(
                    FTL.Identifier('accesskey'),
                    COPY(
                        self.strings, 'checkForUpdatesButton.accesskey'
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
