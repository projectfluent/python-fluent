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
            "span": {
                "start": 0,
                "end": 9,
                "type": "Span"
            },
            "value": {
                "elements": [
                    {
                        "type": "TextElement",
                        "value": "Foo",
                        "span": {
                            "start": 6,
                            "end": 9,
                            "type": "Span"
                        }
                    }
                ],
                "type": "Pattern",
                "span": {
                    "start": 6,
                    "end": 9,
                    "type": "Span"
                }
            },
            "annotations": [],
            "attributes": [],
            "type": "Message",
            "id": {
                "type": "Identifier",
                "name": "foo",
                "span": {
                    "start": 0,
                    "end": 3,
                    "type": "Span"
                }
            }
        }

        message = self.parser.parse_entry(dedent_ftl(input))
        self.assertEqual(message.to_json(), output)


class TestSerializeEntry(unittest.TestCase):
    def setUp(self):
        self.serializer = FluentSerializer()

    def test_simple_message(self):
        input = {
            "comment": None,
            "span": {
                "start": 0,
                "end": 9,
                "type": "Span"
            },
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
