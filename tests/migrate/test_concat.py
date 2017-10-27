# coding=utf8
from __future__ import unicode_literals

import unittest

import fluent.syntax.ast as FTL
try:
    from compare_locales.parser import PropertiesParser, DTDParser
except ImportError:
    DTDParser = PropertiesParser = None

from fluent.migrate.util import parse, ftl_message_to_json
from fluent.migrate.helpers import EXTERNAL_ARGUMENT, MESSAGE_REFERENCE
from fluent.migrate.transforms import evaluate, CONCAT, COPY, REPLACE


class MockContext(unittest.TestCase):
    def get_source(self, path, key):
        # Ignore path (test.properties) and get translations from self.strings
        # defined in setUp.
        return self.strings.get(key, None).val


@unittest.skipUnless(PropertiesParser, 'compare-locales required')
class TestConcatCopy(MockContext):
    def setUp(self):
        self.strings = parse(PropertiesParser, '''
            hello = Hello, world!
            hello.start = Hello,\\u0020
            hello.end = world!
            whitespace.begin.start = \\u0020Hello,\\u0020
            whitespace.begin.end = world!
            whitespace.end.start = Hello,\\u0020
            whitespace.end.end = world!\\u0020
        ''')

    def test_concat_one(self):
        msg = FTL.Message(
            FTL.Identifier('hello'),
            value=CONCAT(
                COPY('test.properties', 'hello'),
            )
        )

        self.assertEqual(
            evaluate(self, msg).to_json(),
            ftl_message_to_json('''
                hello = Hello, world!
            ''')
        )

    def test_concat_two(self):
        msg = FTL.Message(
            FTL.Identifier('hello'),
            value=CONCAT(
                COPY('test.properties', 'hello.start'),
                COPY('test.properties', 'hello.end'),
            )
        )

        result = evaluate(self, msg)

        self.assertEqual(
            len(result.value.elements),
            1,
            'The constructed value should have only one element'
        )
        self.assertIsInstance(
            result.value.elements[0],
            FTL.TextElement,
            'The constructed element should be a TextElement.'
        )
        self.assertEqual(
            result.value.elements[0].value,
            'Hello, world!',
            'The TextElement should be a concatenation of the sources.'
        )

        self.assertEqual(
            result.to_json(),
            ftl_message_to_json('''
                hello = Hello, world!
            ''')
        )

    @unittest.skip('Parser/Serializer trim whitespace')
    def test_concat_whitespace_begin(self):
        msg = FTL.Message(
            FTL.Identifier('hello'),
            value=CONCAT(
                COPY('test.properties', 'whitespace.begin.start'),
                COPY('test.properties', 'whitespace.begin.end'),
            )
        )

        self.assertEqual(
            evaluate(self, msg).to_json(),
            ftl_message_to_json('''
                hello = {" "}Hello, world!
            ''')
        )

    @unittest.skip('Parser/Serializer trim whitespace')
    def test_concat_whitespace_end(self):
        msg = FTL.Message(
            FTL.Identifier('hello'),
            value=CONCAT(
                COPY('test.properties', 'whitespace.end.start'),
                COPY('test.properties', 'whitespace.end.end'),
            )
        )

        self.assertEqual(
            evaluate(self, msg).to_json(),
            ftl_message_to_json('''
                hello = Hello, world!
            ''')
        )


@unittest.skipUnless(DTDParser, 'compare-locales required')
class TestConcatLiteral(MockContext):
    def setUp(self):
        self.strings = parse(DTDParser, '''
            <!ENTITY update.failed.start        "Update failed. ">
            <!ENTITY update.failed.linkText     "Download manually">
            <!ENTITY update.failed.end          "!">
        ''')

    def test_concat_literal(self):
        msg = FTL.Message(
            FTL.Identifier('update-failed'),
            value=CONCAT(
                COPY('test.properties', 'update.failed.start'),
                FTL.TextElement('<a>'),
                COPY('test.properties', 'update.failed.linkText'),
                FTL.TextElement('</a>'),
                COPY('test.properties', 'update.failed.end'),
            )
        )

        self.assertEqual(
            evaluate(self, msg).to_json(),
            ftl_message_to_json('''
                update-failed = Update failed. <a>Download manually</a>!
            ''')
        )


@unittest.skipUnless(DTDParser, 'compare-locales required')
class TestConcatInterpolate(MockContext):
    def setUp(self):
        self.strings = parse(DTDParser, '''
            <!ENTITY channel.description.start  "You are on the ">
            <!ENTITY channel.description.end    " channel.">
        ''')

    def test_concat_replace(self):
        msg = FTL.Message(
            FTL.Identifier('channel-desc'),
            value=CONCAT(
                COPY('test.properties', 'channel.description.start'),
                FTL.Placeable(EXTERNAL_ARGUMENT('channelname')),
                COPY('test.properties', 'channel.description.end'),
            )
        )

        self.assertEqual(
            evaluate(self, msg).to_json(),
            ftl_message_to_json('''
                channel-desc = You are on the { $channelname } channel.
            ''')
        )


@unittest.skipUnless(DTDParser, 'compare-locales required')
class TestConcatReplace(MockContext):
    def setUp(self):
        self.strings = parse(DTDParser, '''
            <!ENTITY community.start       "&brandShortName; is designed by ">
            <!ENTITY community.mozillaLink "&vendorShortName;">
            <!ENTITY community.middle      ", a ">
            <!ENTITY community.creditsLink "global community">
            <!ENTITY community.end         " working together to…">
        ''')

    def test_concat_replace(self):
        msg = FTL.Message(
            FTL.Identifier('community'),
            value=CONCAT(
                REPLACE(
                    'test.properties',
                    'community.start',
                    {
                        '&brandShortName;': MESSAGE_REFERENCE(
                            'brand-short-name'
                        )
                    }
                ),
                FTL.TextElement('<a>'),
                REPLACE(
                    'test.properties',
                    'community.mozillaLink',
                    {
                        '&vendorShortName;': MESSAGE_REFERENCE(
                            'vendor-short-name'
                        )
                    }
                ),
                FTL.TextElement('</a>'),
                COPY('test.properties', 'community.middle'),
                FTL.TextElement('<a>'),
                COPY('test.properties', 'community.creditsLink'),
                FTL.TextElement('</a>'),
                COPY('test.properties', 'community.end')
            )
        )

        self.assertEqual(
            evaluate(self, msg).to_json(),
            ftl_message_to_json(
                'community = { brand-short-name } is designed by '
                '<a>{ vendor-short-name }</a>, a <a>global community</a> '
                'working together to…'
            )
        )


if __name__ == '__main__':
    unittest.main()
