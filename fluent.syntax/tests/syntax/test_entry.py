import pytest

from fluent.syntax.ast import from_json
from fluent.syntax.parser import FluentParser
from fluent.syntax.serializer import FluentSerializer

from . import dedent_ftl


class TestParseEntry:
    @pytest.fixture
    def parser(self):
        return FluentParser(with_spans=False)

    def test_simple_message(self, parser):
        input = "foo = Foo\n"
        output = {
            "comment": None,
            "value": {
                "elements": [{"span": None, "type": "TextElement", "value": "Foo"}],
                "span": None,
                "type": "Pattern",
            },
            "attributes": [],
            "type": "Message",
            "span": None,
            "id": {"span": None, "type": "Identifier", "name": "foo"},
        }

        message = parser.parse_entry(dedent_ftl(input))
        assert message.to_json() == output

    def test_ignore_attached_comment(self, parser):
        input = """\
            # Attached Comment
            foo = Foo
        """
        output = {
            "comment": None,
            "value": {
                "elements": [{"span": None, "type": "TextElement", "value": "Foo"}],
                "span": None,
                "type": "Pattern",
            },
            "attributes": [],
            "type": "Message",
            "id": {"name": "foo", "span": None, "type": "Identifier"},
            "span": None,
        }

        message = parser.parse_entry(dedent_ftl(input))
        assert message.to_json() == output

    def test_return_junk(self, parser):
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
                    "message": 'Expected token: "="',
                    "span": None,
                    "type": "Annotation",
                }
            ],
            "span": None,
            "type": "Junk",
        }

        message = parser.parse_entry(dedent_ftl(input))
        assert message.to_json() == output

    def test_ignore_all_valid_comments(self, parser):
        input = """\
            # Attached Comment
            ## Group Comment
            ### Resource Comment
            foo = Foo
        """
        output = {
            "comment": None,
            "value": {
                "elements": [{"span": None, "type": "TextElement", "value": "Foo"}],
                "span": None,
                "type": "Pattern",
            },
            "attributes": [],
            "span": None,
            "type": "Message",
            "id": {"name": "foo", "span": None, "type": "Identifier"},
        }

        message = parser.parse_entry(dedent_ftl(input))
        assert message.to_json() == output

    def test_do_not_ignore_invalid_comments(self, parser):
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
                    "message": 'Expected token: " "',
                    "span": None,
                    "type": "Annotation",
                }
            ],
            "span": None,
            "type": "Junk",
        }

        message = parser.parse_entry(dedent_ftl(input))
        assert message.to_json() == output


class TestSerializeEntry:
    def test_simple_message(self):
        input = {
            "comment": None,
            "value": {
                "elements": [{"type": "TextElement", "value": "Foo"}],
                "type": "Pattern",
            },
            "attributes": [],
            "type": "Message",
            "id": {"type": "Identifier", "name": "foo"},
        }
        output = """\
            foo = Foo
        """

        message = FluentSerializer().serialize_entry(from_json(input))
        assert message == dedent_ftl(output)
