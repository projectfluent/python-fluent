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
        te, cursor = p.get_text_element(0)
        self.assertEqual(cursor, 16)
        self.assertEqual(te.value, 'something\nfunky')
        p.source = '{ "hi" }'
        with self.assertRaises(ParseError):
            p.get_text_element(0)

    def test_pattern(self):
        p = FluentParser()
        p.source = 'something\n funky'
        te, cursor = p.get_pattern(0)
        self.assertEqual(cursor, 16)
        self.assertEqual(te.elements[0].value, 'something\nfunky')

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

    def test_blank_line(self):
        bl = re.compile(PATTERNS.BLANK_LINE)
        self.assertEqual(bl.match(' \na').group(), ' \n')
        self.assertIsNone(bl.match('a'))

    def test_break_indent(self):
        bi = re.compile(PATTERNS.BREAK_INDENT)
        self.assertEqual(bi.match('\n  \t ').group(), '\n  \t ')
        self.assertIsNone(bi.match('\n\n'))


class IntegrationTest(unittest.TestCase):
    def test_message_with_term_reference(self):
        p = FluentParser()
        resource = p.parse('msg = some { -term } reference')


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

    def test_text_element_chunk(self):
        tec = RE.text_element_chunk
        match = tec.match('foo')
        self.assertIsNotNone(match)
        self.assertEqual(match.group('text_char'), 'foo')
        self.assertIsNone(match.group('text_cont'))
        match = tec.match('\n foo')
        self.assertIsNotNone(match)
        self.assertIsNone(match.group('text_char'))
        self.assertEqual(match.group('text_cont'), '\n ')
        match = tec.match('\n  .attr')
        self.assertIsNone(match)

    def test_comment(self):
        comment = RE.comment
        match = comment.match('foo')
        self.assertIsNone(match)
        match = comment.match('#')
        self.assertIsNotNone(match)
        self.assertEqual(match.groups(), (None, ''))
        match = comment.match('# joe')
        self.assertIsNotNone(match)
        self.assertEqual(match.groups(), ('joe', ''))
        match = comment.match('# joe\n')
        self.assertIsNotNone(match)
        self.assertEqual(match.groups(), ('joe', '\n'))
        match = comment.match('#joe')
        self.assertIsNone(match)

    def test_blank(self):
        blank = RE.blank
        self.assertIsNotNone(blank.match(' '))
        self.assertIsNotNone(blank.match('\n'))
        self.assertIsNotNone(blank.match(''))
        self.assertIsNone(blank.match('a\n'))
