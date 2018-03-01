# coding=utf8
from __future__ import unicode_literals

import unittest
from compare_locales.parser import PropertiesParser, DTDParser

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


class TestProperties(MockContext):
    def setUp(self):
        self.strings = parse(PropertiesParser, '''
            foo = Foo
            value-empty =
            value-whitespace =    

            unicode-all = \\u0020
            unicode-start = \\u0020Foo
            unicode-middle = Foo\\u0020Bar
            unicode-end = Foo\\u0020

            html-entity = &lt;&#x21E7;&#x2318;K&gt;
        ''')

    def test_simple_text(self):
        source = Source('test.properties', 'foo')
        element = source(self)
        self.assertIsInstance(element, FTL.TextElement)
        self.assertEqual(element.value, 'Foo')

    def test_empty_value(self):
        source = Source('test.properties', 'value-empty')
        element = source(self)
        self.assertIsInstance(element, FTL.TextElement)
        self.assertEqual(element.value, '')

    def test_whitespace_value(self):
        source = Source('test.properties', 'value-whitespace')
        element = source(self)
        self.assertIsInstance(element, FTL.TextElement)
        self.assertEqual(element.value, '')

    def test_escape_unicode_all(self):
        source = Source('test.properties', 'unicode-all')
        element = source(self)
        self.assertIsInstance(element, FTL.TextElement)
        self.assertEqual(element.value, ' ')

    def test_escape_unicode_start(self):
        source = Source('test.properties', 'unicode-start')
        element = source(self)
        self.assertIsInstance(element, FTL.TextElement)
        self.assertEqual(element.value, ' Foo')

    def test_escape_unicode_middle(self):
        source = Source('test.properties', 'unicode-middle')
        element = source(self)
        self.assertIsInstance(element, FTL.TextElement)
        self.assertEqual(element.value, 'Foo Bar')

    def test_escape_unicode_end(self):
        source = Source('test.properties', 'unicode-end')
        element = source(self)
        self.assertIsInstance(element, FTL.TextElement)
        self.assertEqual(element.value, 'Foo ')

    def test_html_entity(self):
        source = Source('test.properties', 'html-entity')
        element = source(self)
        self.assertIsInstance(element, FTL.TextElement)
        self.assertEqual(element.value, '&lt;&#x21E7;&#x2318;K&gt;')


class TestDTD(MockContext):
    def setUp(self):
        self.strings = parse(DTDParser, '''
            <!ENTITY foo "Foo">

            <!ENTITY valueEmpty "">
            <!ENTITY valueWhitespace "    ">

            <!ENTITY unicodeEscape "Foo\\u0020Bar">

            <!ENTITY named "&amp;">
            <!ENTITY decimal "&#38;">
            <!ENTITY shorthexcode "&#x26;">
            <!ENTITY longhexcode "&#x0026;">
            <!ENTITY unknown "&unknownEntity;">
        ''')

    def test_simple_text(self):
        source = Source('test.dtd', 'foo')
        element = source(self)
        self.assertIsInstance(element, FTL.TextElement)
        self.assertEqual(element.value, 'Foo')

    def test_empty_value(self):
        source = Source('test.dtd', 'valueEmpty')
        element = source(self)
        self.assertIsInstance(element, FTL.TextElement)
        self.assertEqual(element.value, '')

    def test_whitespace_value(self):
        source = Source('test.dtd', 'valueWhitespace')
        element = source(self)
        self.assertIsInstance(element, FTL.TextElement)
        self.assertEqual(element.value, '    ')

    def test_backslash_unicode_escape(self):
        source = Source('test.dtd', 'unicodeEscape')
        element = source(self)
        self.assertIsInstance(element, FTL.TextElement)
        self.assertEqual(element.value, 'Foo\\u0020Bar')

    def test_named_entity(self):
        source = Source('test.dtd', 'named')
        element = source(self)
        self.assertIsInstance(element, FTL.TextElement)
        self.assertEqual(element.value, '&')

    def test_decimal_entity(self):
        source = Source('test.dtd', 'decimal')
        element = source(self)
        self.assertIsInstance(element, FTL.TextElement)
        self.assertEqual(element.value, '&')

    def test_shorthex_entity(self):
        source = Source('test.dtd', 'shorthexcode')
        element = source(self)
        self.assertIsInstance(element, FTL.TextElement)
        self.assertEqual(element.value, '&')

    def test_longhex_entity(self):
        source = Source('test.dtd', 'longhexcode')
        element = source(self)
        self.assertIsInstance(element, FTL.TextElement)
        self.assertEqual(element.value, '&')

    def test_unknown_entity(self):
        source = Source('test.dtd', 'unknown')
        element = source(self)
        self.assertIsInstance(element, FTL.TextElement)
        self.assertEqual(element.value, '&unknownEntity;')
