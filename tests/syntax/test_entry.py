from __future__ import unicode_literals
import unittest
import sys

sys.path.append('.')

from tests.syntax import dedent_ftl
from fluent.syntax.ast import from_json
from fluent.syntax.parser import FluentParser
from fluent.syntax.serializer import FluentSerializer


class TestParseEntry(unittest.TestCase):
    maxDiff = None

    def setUp(self):
        self.parser = FluentParser()

    def test_simple_message(self):
        input = """\
            foo = Foo
        """
        output = {
            "comment": None,
            "value": {
                "elements": [
                    {
                        'span': {'end': 9, 'start': 6, 'type': 'Span'},
                        "type": "TextElement",
                        "value": "Foo"
                    }
                ],
                'span': {'end': 9, 'start': 6, 'type': 'Span'},
                "type": "Pattern"
            },
            "annotations": [],
            "attributes": [],
            "type": "Message",
            'span': {'end': 10, 'start': 0, 'type': 'Span'},
            "id": {
                'span': {'end': 3, 'start': 0, 'type': 'Span'},
                "type": "Identifier",
                "name": "foo"
            }
        }

        message = self.parser.parse_entry(dedent_ftl(input))
        self.assertEqual(message.to_json(), output)

    def test_ignore_attached_comment(self):
        input = """\
            # Attached Comment
            foo = Foo
        """
        output = {
            "comment": None,
            'value': {
                'elements': [
                    {
                        'span': {'end': 28, 'start': 25, 'type': 'Span'},
                        'type': 'TextElement',
                        'value': 'Foo'
                    }
                ],
                'span': {'end': 28, 'start': 25, 'type': 'Span'},
                'type': 'Pattern'
            }
            "annotations": [],
            "attributes": [],
            "type": "Message",
            'id': {
                'name': 'foo',
                'span': {'end': 22, 'start': 19, 'type': 'Span'},
                'type': 'Identifier'
            },
            'span': {'end': 29, 'start': 19, 'type': 'Span'},
            'type': 'Message'
        }

        message = self.parser.parse_entry(dedent_ftl(input))
        self.assertEqual(message.to_json(), output)

    def test_return_junk(self):
        input = """\
            # Attached Comment
            junk
        """
        output = {
            "content": "junk\n",
            "annotations": [
                {
                    "args": ["junk"],
                    "code": "E0005",
                    'message': 'Expected message "junk" to have a value or attributes',
                    "span": {
                        "end": 23,
                        "start": 23,
                        "type": "Span"
                    },
                    "type": "Annotation"
                }
            ],
            'span': {'end': 24, 'start': 19, 'type': 'Span'},
            "type": "Junk"
        }

        message = self.parser.parse_entry(dedent_ftl(input))
        self.assertEqual(message.to_json(), output)

    def test_ignore_all_valid_comments(self):
        input = """\
            # Attached Comment
            ## Group Comment
            ### Resource Comment
            foo = Foo
        """
        output = {
            "comment": None,
            'value': {
                'elements': [
                    {
                        'span': {'end': 66, 'start': 63, 'type': 'Span'},
                        'type': 'TextElement',
                        'value': 'Foo'
                    }
                ],
                'span': {'end': 66, 'start': 63, 'type': 'Span'},
                'type': 'Pattern'
            },
            "annotations": [],
            "attributes": [],
            'span': {'end': 67, 'start': 57, 'type': 'Span'},
            "type": "Message",
            'id': {
                'name': 'foo',
                'span': {'end': 60, 'start': 57, 'type': 'Span'},
                'type': 'Identifier'
            }
        }

        message = self.parser.parse_entry(dedent_ftl(input))
        self.assertEqual(message.to_json(), output)


    def test_do_not_ignore_invalid_comments(self):
        input = """\
        # Attached Comment
        ##Invalid Comment
        """
        output = {
            "content": "##Invalid Comment\n",
            "annotations": [
                {
                    "args": [" "],
                    "code": "E0003",
                    "message": "Expected token: \" \"",
                    "span": {
                        "end": 21,
                        "start": 21,
                        "type": "Span"
                    },
                    "type": "Annotation"
                }
            ],
            'span': {'end': 37, 'start': 19, 'type': 'Span'},
            "type": "Junk"
        }

        message = self.parser.parse_entry(dedent_ftl(input))
        self.assertEqual(message.to_json(), output)


class TestSerializeEntry(unittest.TestCase):
    def setUp(self):
        self.serializer = FluentSerializer()

    def test_simple_message(self):
        input = {
            "comment": None,
            "value": {
                "elements": [
                    {
                        "type": "TextElement",
                        "value": "Foo"
                    }
                ],
                "type": "Pattern"
            },
            "annotations": [],
            "attributes": [],
            "type": "Message",
            "id": {
                "type": "Identifier",
                "name": "foo"
            }
        }
        output = """\
            foo = Foo
        """

        message = self.serializer.serialize_entry(from_json(input))
        self.assertEqual(message, dedent_ftl(output))
