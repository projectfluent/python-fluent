# coding=utf8
from __future__ import unicode_literals

import unittest

try:
    from compare_locales.parser import PropertiesParser, DTDParser
except ImportError:
    PropertiesParser = DTDParser = None

import fluent.syntax.ast as FTL

from fluent.migrate.errors import NotSupportedError
from fluent.migrate.transforms import Source, COPY, PLURALS, REPLACE
from fluent.migrate.util import parse
from fluent.migrate.helpers import EXTERNAL_ARGUMENT


class TestNotSupportedError(unittest.TestCase):
    def test_source(self):
        pattern = ('Migrating translations from Fluent files is not supported')
        with self.assertRaisesRegexp(NotSupportedError, pattern):
            Source('test.ftl', 'foo')

    def test_copy(self):
        pattern = ('Migrating translations from Fluent files is not supported')
        with self.assertRaisesRegexp(NotSupportedError, pattern):
            FTL.Message(
                FTL.Identifier('foo'),
                value=COPY('test.ftl', 'foo')
            )

    def test_plurals(self):
        pattern = ('Migrating translations from Fluent files is not supported')
        with self.assertRaisesRegexp(NotSupportedError, pattern):
            FTL.Message(
                FTL.Identifier('delete-all'),
                value=PLURALS(
                    'test.ftl',
                    'deleteAll',
                    EXTERNAL_ARGUMENT('num')
                )
            )

    def test_replace(self):
        pattern = ('Migrating translations from Fluent files is not supported')
        with self.assertRaisesRegexp(NotSupportedError, pattern):
            FTL.Message(
                FTL.Identifier(u'hello'),
                value=REPLACE(
                    'test.ftl',
                    'hello',
                    {
                        '#1': EXTERNAL_ARGUMENT('username')
                    }
                )
            )


class MockContext(unittest.TestCase):
    def get_source(self, _path, key):
        # Ignore _path (test.properties) and get translations from self.strings.
        return self.strings[key].val


@unittest.skipUnless(PropertiesParser, 'compare-locales required')
class TestProperties(MockContext):
    def setUp(self):
        self.strings = parse(PropertiesParser, '''
            foo = Foo

            unicode-start = \\u0020Foo
            unicode-middle = Foo\\u0020Bar
            unicode-end = Foo\\u0020

            html-entity = &lt;&#x21E7;&#x2318;K&gt;
        ''')

    def test_simple_text(self):
        source = Source('test.properties', 'foo')
        self.assertEqual(source(self), 'Foo')

    def test_escape_unicode_start(self):
        source = Source('test.properties', 'unicode-start')
        self.assertEqual(source(self), ' Foo')

    def test_escape_unicode_middle(self):
        source = Source('test.properties', 'unicode-middle')
        self.assertEqual(source(self), 'Foo Bar')

    def test_escape_unicode_end(self):
        source = Source('test.properties', 'unicode-end')
        self.assertEqual(source(self), 'Foo ')

    def test_html_entity(self):
        source = Source('test.properties', 'html-entity')
        self.assertEqual(source(self), '&lt;&#x21E7;&#x2318;K&gt;')


@unittest.skipUnless(DTDParser, 'compare-locales required')
class TestDTD(MockContext):
    def setUp(self):
        self.strings = parse(DTDParser, '''
            <!ENTITY foo "Foo">

            <!ENTITY unicodeEscape "Foo\\u0020Bar">

            <!ENTITY named "&amp;">
            <!ENTITY decimal "&#38;">
            <!ENTITY shorthexcode "&#x26;">
            <!ENTITY longhexcode "&#x0026;">
            <!ENTITY unknown "&unknownEntity;">
        ''')

    def test_simple_text(self):
        source = Source('test.dtd', 'foo')
        self.assertEqual(source(self), 'Foo')

    def test_backslash_unicode_escape(self):
        source = Source('test.dtd', 'unicodeEscape')
        self.assertEqual(source(self), 'Foo\\u0020Bar')

    def test_named_entity(self):
        source = Source('test.dtd', 'named')
        self.assertEqual(source(self), '&')

    def test_decimal_entity(self):
        source = Source('test.dtd', 'decimal')
        self.assertEqual(source(self), '&')

    def test_shorthex_entity(self):
        source = Source('test.dtd', 'shorthexcode')
        self.assertEqual(source(self), '&')

    def test_longhex_entity(self):
        source = Source('test.dtd', 'longhexcode')
        self.assertEqual(source(self), '&')

    def test_unknown_entity(self):
        source = Source('test.dtd', 'unknown')
        self.assertEqual(source(self), '&unknownEntity;')
