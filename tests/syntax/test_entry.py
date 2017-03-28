from __future__ import unicode_literals
import unittest
import sys

sys.path.append('.')

from tests.syntax import dedent_ftl
from fluent.syntax.ast import from_json
from fluent.syntax.parser import parse_entry
from fluent.syntax.serializer import serialize_entry


class TestParseEntry(unittest.TestCase):
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
            "tags": None,
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
            "attributes": None,
            "type": "Message",
            "id": {
                "type": "Identifier",
                "name": "foo"
            }
        }

        message = parse_entry(dedent_ftl(input))
        self.assertEqual(message.to_json(), output)


class TestSerializeEntry(unittest.TestCase):
    def test_simple_message(self):
        input = {
            "comment": None,
            "span": {
                "start": 0,
                "end": 9,
                "type": "Span"
            },
            "tags": None,
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
            "attributes": None,
            "type": "Message",
            "id": {
                "type": "Identifier",
                "name": "foo"
            }
        }
        output = """\
            foo = Foo
        """

        message = serialize_entry(from_json(input))
        self.assertEqual(message, dedent_ftl(output))
