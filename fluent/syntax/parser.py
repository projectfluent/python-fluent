from __future__ import unicode_literals
import re
from . import ast
from .errors import ParseError


def with_span(fn):
    def decorated(self, cursor, *args):
        if not self.with_spans:
            return fn(self, cursor, *args)

        start = cursor
        node = fn(self, cursor, *args)

        if node is None:
            return node

        node, cursor = node
        # Don't re-add the span if the node already has it.  This may happen
        # when one decorated function calls another decorated function.
        if node.span is not None:
            return node, cursor

        end = cursor
        node.add_span(start, end)
        return node, cursor

    return decorated


class FluentParser(object):
    def __init__(self, with_spans=True):
        self.with_spans = with_spans
        self.source = None

    def parse(self, source):
        self.source = source
        entries = []
        cursor = 0
        while cursor < len(self.source):
            entry, cursor = self.get_entry_or_junk(cursor)
            if entry is not None:
                # Don't add top-level white-space
                entries.append(entry)
        res = ast.Resource(entries)

        if self.with_spans:
            res.add_span(0, cursor)

        return res

    def parse_entry(self, source):
        """Parse the first Message or Term in source.

        Skip all encountered comments and start parsing at the first Mesage
        or Term start. Return Junk if the parsing is not successful.

        Preceding comments are ignored unless they contain syntax errors
        themselves, in which case Junk for the invalid comment is returned.
        """
        self.source = source
        return None

    def get_entry_or_junk(self, cursor):

        rv = self.get_entry(cursor)
        if rv is not None:
            return rv
        rv = self.get_blank_line(cursor)
        if rv is not None:
            return rv

    def get_entry(self, cursor):
        rv = self.get_message(cursor)
        if rv is not None:
            entry, cursor = rv
            line_end = self.require_line_end(cursor)
            if line_end is None:
                return None
            return (entry, line_end)

        for comment in (
                self.get_comment,
                self.get_group_comment,
                self.get_resource_comment
        ):
            rv = comment(cursor)
            if rv is not None:
                return rv
        # raise ParseError('E0002')

    def get_blank_line(self, cursor):
        '''Parse top-level blank  lines.

        Returns None as AST node while we're not having a proper
        AST node for top-level white-space.
        '''
        m = RE.blank_line.match(self.source, cursor)
        return None if m is None else (None, m.end())

    @with_span
    def get_comment(self, cursor):
        return self._get_generic_comment(cursor, RE.comment, ast.Comment)

    @with_span
    def get_group_comment(self, cursor):
        return self._get_generic_comment(
            cursor, RE.group_comment, ast.GroupComment
        )

    @with_span
    def get_resource_comment(self, cursor):
        return self._get_generic_comment(
            cursor, RE.resource_comment, ast.ResourceComment
        )

    def _get_generic_comment(self, cursor, comment_re, Node):
        match = comment_re.match(self.source, cursor)
        if match is None:
            return None

        content = []
        while match:
            content += match.groups()
            cursor = match.end()
            match = comment_re.match(self.source, cursor)

        # strip trailing whitespace from last comment
        content.pop()
        # Filter out None
        content = [seg for seg in content if seg is not None]
        return Node(''.join(content)), cursor

    @with_span
    def get_message(self, cursor):
        rv = self.get_identifier(cursor)
        if rv is None:
            return rv
        id, cursor = rv

        cursor = self.skip_blank_inline(cursor)
        pattern = attrs = None

        cursor = self.expect_equals(cursor)
        if cursor is None:
            return None

        rv = self.get_pattern(cursor)
        if rv is not None:
            pattern, cursor = rv

        rv = self.get_attributes(cursor)
        if rv:
            attrs, cursor = rv

        if pattern is None and attrs is None:
            return None

        return ast.Message(id, pattern, attrs), cursor

    def expect_equals(self, cursor):
        '''Messages require an = after their ID.

        Overwrite this to disable that requirement.
        '''
        cursor = self.require_char(cursor, '=')
        if cursor is None:
            return cursor
        return self.skip_blank_inline(cursor)

    @with_span
    def get_attribute(self, cursor):
        cursor = self.require_line_end(cursor)
        if cursor is None:
            return None
        cursor = self.skip_blank(cursor)

        cursor = self.require_char(cursor, '.')
        if cursor is None:
            return None

        rv = self.get_identifier(cursor)
        if rv is None:
            return None
        key, cursor = rv

        cursor = self.skip_blank_inline(cursor)

        cursor = self.require_char(cursor, '=')
        if cursor is None:
            return None

        cursor = self.skip_blank_inline(cursor)
        if cursor >= len(self.source):
            return None

        rv = self.get_pattern(cursor)
        if rv is None:
            return None

        value, cursor = rv

        return ast.Attribute(key, value), cursor

    def get_attributes(self, cursor):
        attrs = []

        while True:
            rv = self.get_attribute(cursor)
            if rv is None:
                break
            attr, cursor = rv
            attrs.append(attr)

        if not attrs:
            return None
        return attrs, cursor

    @with_span
    def get_identifier(self, cursor):
        match = RE.identifier.match(self.source, cursor)
        if match is None:
            # TODO: ERROR
            return None
        name = match.group()
        cursor = match.end()
        return ast.Identifier(name), cursor

    @with_span
    def get_term_identifier(self, cursor):
        match = RE.term_identifier.match(self.source, cursor)
        if match is None:
            # TODO: ERROR
            return None
        name = match.group()
        cursor = match.end()
        return ast.Identifier(name), cursor

    @with_span
    def get_pattern(self, cursor):
        elements = []

        while cursor < len(self.source):
            rv = self.get_pattern_element(cursor)
            if rv is None:
                break
            element, cursor = rv
            elements.append(element)

        if not elements:
            return None

        # Trim trailing whitespace.
        last_element = elements[-1]
        if isinstance(last_element, ast.TextElement):
            last_element.value = last_element.value.rstrip(' \t\n\r')

        return ast.Pattern(elements), cursor

    def get_pattern_element(self, cursor):
        for element in (
                self.get_text_element,
                self.get_placeable
        ):
            rv = element(cursor)
            if rv is not None:
                return rv
        return None

    @with_span
    def get_text_element(self, cursor):
        buf = []

        while cursor < len(self.source):
            match = RE.text_element_chunk.match(self.source, cursor)
            if match is None:
                if buf:
                    break
                else:
                    return None
            if match.group('text_char') is not None:
                buf.append(match.group('text_char'))
            cursor = match.end()

        # The newline normalization here matches grammar.mjs'
        # break_indent production.
        return ast.TextElement('\n'.join(buf)), cursor

    @with_span
    def get_placeable(self, cursor):
        cursor = self.require_char(cursor, '{')
        if cursor is None:
            return None
        cursor = self.skip_blank_inline(cursor)
        if cursor >= len(self.source):
            return None
        rv = self.get_expression(cursor)
        if rv is None:
            return None
        expression, cursor = rv
        cursor = self.skip_blank_inline(cursor)
        if cursor >= len(self.source):
            return None
        cursor = self.require_char(cursor, '}')
        if cursor is None:
            return None
        return ast.Placeable(expression), cursor

    def get_expression(self, cursor):
        for expression in (
                self.get_term_reference,
        ):
            rv = expression(cursor)
            if rv is not None:
                return rv
        return None

    @with_span
    def get_term_reference(self, cursor):
        rv = self.get_term_identifier(cursor)
        if rv is None:
            return None
        term_ident, cursor = rv
        return ast.TermReference(term_ident), cursor

    def skip_blank_inline(self, cursor):
        m = RE.blank_inline.match(self.source, cursor)
        return cursor if m is None else m.end()

    def skip_blank(self, cursor):
        m = RE.blank.match(self.source, cursor)
        return cursor if m is None else m.end()

    def require_line_end(self, cursor):
        m = RE.line_end.match(self.source, cursor)
        return None if m is None else m.end()

    def require_char(self, cursor, char):
        if cursor >= len(self.source):
            return None
        if self.source[cursor] != char:
            return None
        return cursor + 1


class CompatFluentParser(FluentParser):
    def expect_equals(self, cursor):
        '''Messages require an = after their ID.

        Overwritten to disable that requirement.
        '''
        cursor = self.require_char(cursor, '=')
        if cursor is None:
            return None
        return self.skip_blank_inline(cursor)

    @with_span
    def get_group_comment_from_section(self, cursor):
        raise NotImplementedError
        ps.expect_char('[')
        ps.expect_char('[')

        ps.skip_inline_ws()

        self.get_variant_name(ps)

        ps.skip_inline_ws()

        ps.expect_char(']')
        ps.expect_char(']')

        # A Section without a comment is like an empty Group Comment.
        # Semantically it ends the previous group and starts a new one.
        return ast.GroupComment('')

    @with_span
    def get_zero_four_style_comment(self, cursor):
        ps.expect_char('/')
        ps.expect_char('/')
        ps.take_char(lambda x: x == ' ')

        content = ''

        while True:
            ch = ps.take_char(lambda x: x != '\n')
            while ch:
                content += ch
                ch = ps.take_char(lambda x: x != '\n')

            if ps.is_peek_next_line_zero_four_style_comment():
                content += ps.current()
                ps.next()
                ps.expect_char('/')
                ps.expect_char('/')
                ps.take_char(lambda x: x == ' ')
            else:
                break

        # Comments followed by Sections become GroupComments.
        ps.peek()
        if ps.current_peek_is('['):
            ps.skip_to_peek()
            self.get_group_comment_from_section(ps)
            return ast.GroupComment(content)

        ps.reset_peek()
        ps.last_comment_zero_four_syntax = True
        return ast.Comment(content)


class PATTERNS(object):
    BLANK_INLINE = '[ \t]+'
    LINE_END = r'(?:\r\n|\n|\Z)'
    BLANK_LINE = '(?:{})?{}'.format(BLANK_INLINE, LINE_END)
    BREAK_INDENT = '{}(?:{})*{}'.format(LINE_END, BLANK_LINE, BLANK_INLINE)
    REGULAR_CHAR = '[!-\ud7ff\ue000-\ufffd]'
    TEXT_CHAR = (
        BLANK_INLINE +
        r'|'
        r'\\u[0-9a-fA-F]{4}'
        r'|'
        r'\\\\'
        r'|'
        r'\\{'
        r'|'
        r'(?![{\\])' + REGULAR_CHAR
    )
    COMMENT_LINE = '(?: (.*))?(' + LINE_END + ')'


class RE(object):
    comment = re.compile(r'#' + PATTERNS.COMMENT_LINE)
    group_comment = re.compile(r'##' + PATTERNS.COMMENT_LINE)
    resource_comment = re.compile(r'###' + PATTERNS.COMMENT_LINE)
    identifier = re.compile(r'[a-zA-Z][a-zA-Z0-9_-]*')
    term_identifier = re.compile(r'-[a-zA-Z][a-zA-Z0-9_-]*')
    # text_cont needs to exclude BLANK_INLINE and EOF, as they're
    # otherwise part of the negative lookahead.
    # compared to the ebnf, this does not contain the first char of
    # the new line.
    text_element_chunk = re.compile(
        r'(?P<text_char>(?:{})+)'.format(PATTERNS.TEXT_CHAR) +
        r'|' +
        r'(?P<text_cont>{}(?!\}}|\[|\*|\.| |\t|\Z))'.format(
            PATTERNS.BREAK_INDENT
        )
    )
    blank_inline = re.compile(PATTERNS.BLANK_INLINE)
    line_end = re.compile(PATTERNS.LINE_END)
    blank_line = re.compile(PATTERNS.BLANK_LINE)
    blank = re.compile(r'(?:{})|(?:{})'.format(
        PATTERNS.BLANK_INLINE, PATTERNS.LINE_END
    ))
    break_indent = re.compile(PATTERNS.BREAK_INDENT)
