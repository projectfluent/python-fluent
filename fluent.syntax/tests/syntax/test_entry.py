from __future__ import unicode_literals
import unittest
import sys

sys.path.append(".")

from tests.syntax import dedent_ftl
from fluent.syntax.ast import from_json
from fluent.syntax.parser import FluentParser
from fluent.syntax.serializer import FluentSerializer


class TestParseEntry(unittest.TestCase):
    maxDiff = None

    def setUp(self):
        self.parser = FluentParser(with_spans=False)

    def test_simple_message(self):
        input = """\
            foo = Foo
        """
        output = {
            "comment": None,
            "value": {
                "elements": [
                    {
                        "span": None,
                        "type": "TextElement",
                        "value": "Foo"
                    }
                ],
                "span": None,
                "type": "Pattern"
            },
            "attributes": [],
            "type": "Message",
            "span": None,
            "id": {
                "span": None,
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
            "value": {
                "elements": [
                    {
                        "span": None,
                        "type": "TextElement",
                        "value": "Foo"
                    }
                ],
                "span": None,
                "type": "Pattern"
            },
            "attributes": [],
            "type": "Message",
            "id": {
                "name": "foo",
                "span": None,
                "type": "Identifier"
            },
            "span": None,
            "type": "Message"
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
                    "arguments": ["="],
                    "code": "E0003",
                    "message": "Expected token: \"=\"",
                    "span": {
                        "end": 23,
                        "start": 23,
                        "type": "Span"
                    },
                    "type": "Annotation"
                }
            ],
            "span": None,
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
            "value": {
                "elements": [
                    {
                        "span": None,
                        "type": "TextElement",
                        "value": "Foo"
                    }
                ],
                "span": None,
                "type": "Pattern"
            },
            "attributes": [],
            "span": None,
            "type": "Message",
            "id": {
                "name": "foo",
                "span": None,
                "type": "Identifier"
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
                    "arguments": [" "],
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
            "span": None,
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
