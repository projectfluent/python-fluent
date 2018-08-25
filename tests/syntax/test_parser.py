from __future__ import unicode_literals
import unittest
import re

from fluent.syntax.parser import FluentParser, RE, PATTERNS
from fluent.syntax import ast
from fluent.syntax.errors import ParseError


class IdentifierTest(unittest.TestCase):
    def test_identifier(self):
        p = FluentParser()
        p.source = ' \nid = foo'
        with self.assertRaises(ParseError):
            p.get_identifier(0)
        id, cursor = p.get_identifier(2)
        self.assertEqual(cursor, 4)
        self.assertEqual(id.name, 'id')
        self.assertEqual(id.span.start, 2)
        self.assertEqual(id.span.end, 4)
        self.assertEqual(p.source[id.span.start:id.span.end], 'id')

    def test_term_identifier(self):
        p = FluentParser()
        p.source = ' \n-id = foo'
        with self.assertRaises(ParseError):
            p.get_term_identifier(0)
        id, cursor = p.get_term_identifier(2)
        self.assertEqual(cursor, 5)
        self.assertEqual(id.name, '-id')
        self.assertEqual(id.span.start, 2)
        self.assertEqual(id.span.end, 5)
        self.assertEqual(p.source[id.span.start:id.span.end], '-id')


class MessageTest(unittest.TestCase):
    def test_text_element(self):
        p = FluentParser()
        p.source = 'something\n funky'
        te, cursor = p.get_inline_text(0)
        self.assertEqual(cursor, 9)
        self.assertEqual(te.value, 'something')
        p.source = '{ "hi" }'
        with self.assertRaises(ParseError):
            p.get_inline_text(0)
        p.source = 'one\nidentifier'
        te, cursor = p.get_inline_text(0)
        self.assertEqual(cursor, 3)
        self.assertEqual(te.value, 'one')
        with self.assertRaises(ParseError):
            te, cursor = p.get_block_text(3)

    def test_pattern(self):
        p = FluentParser()
        p.source = '\n\n  something\n funky\n\n going on'
        pat, cursor = p.get_pattern(0)
        self.assertEqual(cursor, len(p.source))
        self.assertEqual(
            pat.elements[0].value,
            'something\nfunky\n\ngoing on'
        )
        # TODO: Confirm start position of span
        self.assertEqual(pat.span.start, 2)

    def test_message(self):
        p = FluentParser()
        p.source = 'message = is funky'
        msg, cursor = p.get_message(0)
        self.assertEqual(cursor, 18)
        self.assertEqual(msg.id.name, 'message')

    def test_attribute(self):
        p = FluentParser()
        p.source = '\n .key = value'
        attr, cursor = p.get_attribute(0)
        self.assertEqual(cursor, len(p.source))
        self.assertEqual(attr.id.name, 'key')
        self.assertEqual(attr.value.elements[0].value, 'value')
        p.source = '\n    .key = value'
        attr, cursor = p.get_attribute(0)
        self.assertEqual(cursor, len(p.source))
        self.assertEqual(attr.id.name, 'key')
        self.assertEqual(attr.value.elements[0].value, 'value')

    def test_just_attribute(self):
        p = FluentParser()
        p.source = 'msg = \n .key = value'
        msg, cursor = p.get_message(0)
        self.assertEqual(cursor, len(p.source))
        self.assertEqual(msg.attributes[0].id.name, 'key')


class TermTest(unittest.TestCase):

    def test_value(self):
        p = FluentParser()
        p.source = '-term = is funky'
        term, cursor = p.get_term(0)
        self.assertEqual(cursor, len(p.source))
        self.assertEqual(term.id.name, '-term')

    def test_value_and_attribute(self):
        p = FluentParser()
        p.source = '-term = val\n     .key = value\n\n'
        term, cursor = p.get_term(0)
        self.assertEqual(cursor, len(p.source) - 2)
        self.assertEqual(term.attributes[0].id.name, 'key')
        self.assertEqual(term.value.elements[0].value, 'val')

    def test_just_attribute(self):
        p = FluentParser()
        p.source = '-term = \n .key = value'
        with self.assertRaises(ParseError):
            p.get_term(0)


class CommentTest(unittest.TestCase):
    def test_comment(self):
        p = FluentParser()
        p.source = '# one\n#\n# two\njunk'
        comment, _ = p.get_comment(0)
        self.assertEqual(comment.content, 'one\n\ntwo')

    def test_group_comment(self):
        p = FluentParser()
        p.source = '## one\n'
        comment, _ = p.get_group_comment(0)
        self.assertEqual(comment.content, 'one')

    def test_resource_comment(self):
        p = FluentParser()
        p.source = '### one\n'
        comment, _ = p.get_resource_comment(0)
        self.assertEqual(comment.content, 'one')


class PlaceableTest(unittest.TestCase):
    def test_term_reference(self):
        p = FluentParser()
        p.source = '-term'
        ref, cursor = p.get_term_reference(0)
        self.assertEqual(cursor, len(p.source))
        self.assertEqual(ref.id.name, '-term')

    def test_placeable(self):
        p = FluentParser()
        p.source = '{ -term }'
        placeable, cursor = p.get_placeable(0)
        self.assertEqual(cursor, len(p.source))
        self.assertIsInstance(placeable, ast.Placeable)

    def test_relaxed_whitespace(self):
        p = FluentParser()
        p.source = '{\n-term\n}\n'
        placeable, cursor = p.get_placeable(0)
        self.assertEqual(cursor, len(p.source) - 1)
        self.assertIsInstance(placeable, ast.Placeable)


class IntegrationTest(unittest.TestCase):
    def test_message_with_term_reference(self):
        p = FluentParser()
        resource = p.parse('''
msg = some { -term } reference

-term = terminology
   .with = metadata
''')
        self.assertEqual(len(resource.body), 2)
        self.assertFalse(
            any(isinstance(entry, ast.Junk) for entry in resource.body)
        )

    def test_attached_comment(self):
        p = FluentParser()
        resource = p.parse('''\
# attached
msg = val
''')
        self.assertEqual(len(resource.body), 1)
        self.assertIsNotNone(resource.body[0].comment)

    def test_standalone_comment(self):
        p = FluentParser()
        resource = p.parse('''\
# attached

msg = val
''')
        self.assertEqual(len(resource.body), 2)
        self.assertIsInstance(resource.body[0], p.ast.Comment)
        self.assertIsNone(resource.body[1].comment)


class PatternTest(unittest.TestCase):
    def test_text_char(self):
        c = re.compile(PATTERNS.TEXT_CHAR)
        self.assertIsNotNone(c.match(' '))
        self.assertIsNotNone(c.match('\t'))
        self.assertIsNotNone(c.match('a'))
        self.assertIsNotNone(c.match('\ue000'))
        self.assertIsNotNone(c.match(r'\\'))
        self.assertIsNotNone(c.match(r'\{'))
        self.assertIsNone(c.match(r'\a'))

    def test_line_end(self):
        le = re.compile(PATTERNS.LINE_END)
        self.assertIsNotNone(le.match(''))
        self.assertIsNotNone(le.match('\n'))
        self.assertIsNotNone(le.match('\r\n'))
        self.assertEqual(le.match('\r\n').group(), '\r\n')
        self.assertEqual(le.match('\n\n').group(), '\n')


class RETest(unittest.TestCase):
    def test_identifier(self):
        id = RE.identifier
        self.assertIsNone(id.match(' '))
        self.assertIsNone(id.match('{'))
        self.assertIsNone(id.match('.'))
        self.assertIsNone(id.match('['))
        self.assertIsNone(id.match(']'))
        self.assertIsNone(id.match(':'))
        self.assertIsNone(id.match(r'\\'))
        self.assertIsNotNone(id.match('a-_'))
        self.assertIsNone(id.match('-a_'))

    def test_term_identifier(self):
        id = RE.term_identifier
        self.assertIsNone(id.match(' '))
        self.assertIsNone(id.match('{'))
        self.assertIsNone(id.match('.'))
        self.assertIsNone(id.match('['))
        self.assertIsNone(id.match(']'))
        self.assertIsNone(id.match(':'))
        self.assertIsNone(id.match(r'\\'))
        self.assertIsNone(id.match('a-_'))
        self.assertIsNotNone(id.match('-a_'))

    def test_comment(self):
        comment = RE.comment
        match = comment.match('foo')
        self.assertIsNone(match)
        match = comment.match('#')
        self.assertIsNotNone(match)
        self.assertEqual(match.group(2), None)
        self.assertEqual(match.end(1), 1)
        self.assertEqual(match.end(), 1)
        match = comment.match('#\n')
        self.assertIsNotNone(match)
        self.assertEqual(match.group(2), None)
        self.assertEqual(match.end(1), 1)
        self.assertEqual(match.end(), 2)
        match = comment.match('# joe')
        self.assertIsNotNone(match)
        self.assertEqual(match.group(2), 'joe')
        match = comment.match('# joe\n')
        self.assertIsNotNone(match)
        self.assertEqual(match.group(2), 'joe')
        match = comment.match('# joe\r\n')
        self.assertIsNotNone(match)
        self.assertEqual(match.group(2), 'joe')
        match = comment.match('#joe')
        self.assertIsNone(match)

    def test_string_literal(self):
        sl = RE.string_literal
        match = sl.match('""')
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), '')
        match = sl.match('  ""')
        self.assertIsNone(match)
        match = sl.match(r'"\"some"')
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), r'\"some')

    def test_number_literal(self):
        num = RE.number_literal
        match = num.match('0')
        self.assertIsNotNone(match)
        self.assertEqual(match.group(), '0')
        match = num.match('-0')
        self.assertIsNotNone(match)
        self.assertEqual(match.group(), '-0')
        match = num.match('10.0')
        self.assertIsNotNone(match)
        self.assertEqual(match.group(), '10.0')
        self.assertIsNone(num.match('.'))
        self.assertIsNone(num.match('.0'))
        self.assertIsNone(num.match('-'))
        self.assertIsNone(num.match('a'))
        self.assertIsNone(num.match('"'))


    def test_blank(self):
        blank = RE.blank
        self.assertIsNotNone(blank.match(' '))
        self.assertIsNotNone(blank.match('\n'))
        self.assertIsNotNone(blank.match(''))
        self.assertIsNone(blank.match('a\n'))
