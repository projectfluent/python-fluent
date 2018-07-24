from __future__ import unicode_literals
import re
from .ftlstream import FTLParserStream
from . import ast
from .errors import ParseError


def with_span(fn):
    def decorated(self, ps, *args):
        if not self.with_spans:
            return fn(self, ps, *args)

        start = ps.get_index()
        node = fn(self, ps, *args)

        # Don't re-add the span if the node already has it.  This may happen
        # when one decorated function calls another decorated function.
        if node.span is not None:
            return node

        end = ps.get_index()
        node.add_span(start, end)
        return node

    return decorated


class FluentParser(object):
    def __init__(self, with_spans=True):
        self.with_spans = with_spans

    def parse(self, source):
        ps = FTLParserStream(source)
        ps.skip_blank_lines()

        entries = []
        last_comment = None

        while ps.current():
            entry = self.get_entry_or_junk(ps)
            blank_lines = ps.skip_blank_lines()

            # Regular Comments require special logic. Comments may be attached
            # to Messages or Terms if they are followed immediately by them.
            # However they should parse as standalone when they're followed by
            # Junk. Consequently, we only attach Comments once we know that the
            # Message or the Term parsed successfully.
            if (
                isinstance(entry, ast.Comment)
                and blank_lines == 0 and ps.current()
            ):
                # Stash the comment and decide what to do with it
                # in the next pass.
                last_comment = entry
                continue

            if last_comment is not None:
                if isinstance(entry, (ast.Message, ast.Term)):
                    entry.comment = last_comment
                    if self.with_spans:
                        entry.span.start = entry.comment.span.start
                else:
                    entries.append(last_comment)
                # In either case, the stashed comment has been dealt with;
                # clear it.
                last_comment = None

            if isinstance(entry, ast.Comment) \
               and ps.last_comment_zero_four_syntax \
               and len(entries) == 0:
                comment = ast.ResourceComment(entry.content)
                comment.span = entry.span
                entries.append(comment)
            else:
                entries.append(entry)

            ps.last_comment_zero_four_syntax = False

        res = ast.Resource(entries)

        if self.with_spans:
            res.add_span(0, ps.get_index())

        return res

    def parse_entry(self, source):
        """Parse the first Message or Term in source.

        Skip all encountered comments and start parsing at the first Mesage
        or Term start. Return Junk if the parsing is not successful.

        Preceding comments are ignored unless they contain syntax errors
        themselves, in which case Junk for the invalid comment is returned.
        """
        ps = FTLParserStream(source)
        ps.skip_blank_lines()

        while ps.current_is('#'):
            skipped = self.get_entry_or_junk(ps)
            if isinstance(skipped, ast.Junk):
                # Don't skip Junk comments.
                return skipped
            ps.skip_blank_lines()

        return self.get_entry_or_junk(ps)

    def get_entry_or_junk(self, ps):
        entry_start_pos = ps.get_index()

        try:
            entry = self.get_entry(ps)
            ps.expect_line_end()
            return entry
        except ParseError as err:
            error_index = ps.get_index()
            ps.skip_to_next_entry_start()
            next_entry_start = ps.get_index()

            # Create a Junk instance
            slice = ps.get_slice(entry_start_pos, next_entry_start)
            junk = ast.Junk(slice)
            if self.with_spans:
                junk.add_span(entry_start_pos, next_entry_start)
            annot = ast.Annotation(err.code, err.args, err.message)
            annot.add_span(error_index, error_index)
            junk.add_annotation(annot)
            return junk

    def get_entry(self, ps):
        if ps.current_is('#'):
            return self.get_comment(ps)

        if ps.current_is('/'):
            return self.get_zero_four_style_comment(ps)

        if ps.current_is('['):
            return self.get_group_comment_from_section(ps)

        if ps.current_is('-'):
            return self.get_term(ps)

        if ps.is_identifier_start():
            return self.get_message(ps)

        raise ParseError('E0002')

    @with_span
    def get_zero_four_style_comment(self, ps):
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

    @with_span
    def get_comment(self, ps):
        # 0 - comment
        # 1 - group comment
        # 2 - resource comment
        level = -1
        content = ''

        while True:
            i = -1
            while ps.current_is('#') and (i < (2 if level == -1 else level)):
                ps.next()
                i += 1

            if level == -1:
                level = i

            if not ps.current_is('\n'):
                ps.expect_char(' ')
                ch = ps.take_char(lambda x: x != '\n')
                while ch:
                    content += ch
                    ch = ps.take_char(lambda x: x != '\n')

            if ps.is_peek_next_line_comment(level):
                content += ps.current()
                ps.next()
            else:
                break

        if level == 0:
            return ast.Comment(content)
        elif level == 1:
            return ast.GroupComment(content)
        elif level == 2:
            return ast.ResourceComment(content)

    @with_span
    def get_group_comment_from_section(self, ps):
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
    def get_message(self, ps):
        id = self.get_identifier(ps)

        ps.skip_inline_ws()
        pattern = None

        # XXX Syntax 0.4 compat
        if ps.current_is('='):
            ps.next()

            if ps.is_peek_value_start():
                ps.skip_indent()
                pattern = self.get_pattern(ps)
            else:
                ps.skip_inline_ws()

        if ps.is_peek_next_line_attribute_start():
            attrs = self.get_attributes(ps)
        else:
            attrs = None

        if pattern is None and attrs is None:
            raise ParseError('E0005', id.name)

        return ast.Message(id, pattern, attrs)

    @with_span
    def get_term(self, ps):
        id = self.get_term_identifier(ps)

        ps.skip_inline_ws()
        ps.expect_char('=')

        if ps.is_peek_value_start():
            ps.skip_indent()
            value = self.get_value(ps)
        else:
            raise ParseError('E0006', id.name)

        if ps.is_peek_next_line_attribute_start():
            attrs = self.get_attributes(ps)
        else:
            attrs = None

        return ast.Term(id, value, attrs)

    @with_span
    def get_attribute(self, ps):
        ps.expect_char('.')

        key = self.get_identifier(ps)

        ps.skip_inline_ws()
        ps.expect_char('=')

        if ps.is_peek_value_start():
            ps.skip_indent()
            value = self.get_pattern(ps)
            return ast.Attribute(key, value)

        raise ParseError('E0012')

    def get_attributes(self, ps):
        attrs = []

        while True:
            ps.expect_indent()
            attr = self.get_attribute(ps)
            attrs.append(attr)

            if not ps.is_peek_next_line_attribute_start():
                break
        return attrs

    @with_span
    def get_identifier(self, ps):
        name = ps.take_id_start()
        ch = ps.take_id_char()
        while ch:
            name += ch
            ch = ps.take_id_char()

        return ast.Identifier(name)

    @with_span
    def get_term_identifier(self, ps):
        ps.expect_char('-')
        id = self.get_identifier(ps)
        return ast.Identifier('-{}'.format(id.name))

    def get_variant_key(self, ps):
        ch = ps.current()

        if ch is None:
            raise ParseError('E0013')

        cc = ord(ch)
        if ((cc >= 48 and cc <= 57) or cc == 45):  # 0-9, -
            return self.get_number(ps)

        return self.get_variant_name(ps)

    @with_span
    def get_variant(self, ps, has_default):
        default_index = False

        if ps.current_is('*'):
            if has_default:
                raise ParseError('E0015')
            ps.next()
            default_index = True

        ps.expect_char('[')

        key = self.get_variant_key(ps)

        ps.expect_char(']')

        if ps.is_peek_value_start():
            ps.skip_indent()
            value = self.get_value(ps)
            return ast.Variant(key, value, default_index)

        raise ParseError('E0012')

    def get_variants(self, ps):
        variants = []
        has_default = False

        while True:
            ps.expect_indent()
            variant = self.get_variant(ps, has_default)

            if variant.default:
                has_default = True

            variants.append(variant)

            if not ps.is_peek_next_line_variant_start():
                break

        if not has_default:
            raise ParseError('E0010')

        return variants

    @with_span
    def get_variant_name(self, ps):
        name = ps.take_id_start()
        while True:
            ch = ps.take_variant_name_char()
            if ch:
                name += ch
            else:
                break

        return ast.VariantName(name.rstrip(' \t\n\r'))

    def get_digits(self, ps):
        num = ''

        ch = ps.take_digit()
        while ch:
            num += ch
            ch = ps.take_digit()

        if len(num) == 0:
            raise ParseError('E0004', '0-9')

        return num

    @with_span
    def get_number(self, ps):
        num = ''

        if ps.current_is('-'):
            num += '-'
            ps.next()

        num += self.get_digits(ps)

        if ps.current_is('.'):
            num += '.'
            ps.next()
            num += self.get_digits(ps)

        return ast.NumberLiteral(num)

    @with_span
    def get_value(self, ps):
        if ps.current_is('{'):
            ps.peek()
            ps.peek_inline_ws()
            if ps.is_peek_next_line_variant_start():
                return self.get_variant_list(ps)

        return self.get_pattern(ps)

    @with_span
    def get_variant_list(self, ps):
        ps.expect_char('{')
        ps.skip_inline_ws()
        variants = self.get_variants(ps)
        ps.expect_indent()
        ps.expect_char('}')
        return ast.VariantList(variants)

    @with_span
    def get_pattern(self, ps):
        elements = []
        ps.skip_inline_ws()

        while ps.current():
            ch = ps.current()

            # The end condition for get_pattern's while loop is a newline
            # which is not followed by a valid pattern continuation.
            if ch == '\n' and not ps.is_peek_next_line_value():
                break

            if ch == '{':
                element = self.get_placeable(ps)
            else:
                element = self.get_text_element(ps)
            elements.append(element)

        # Trim trailing whitespace.
        last_element = elements[-1]
        if isinstance(last_element, ast.TextElement):
            last_element.value = last_element.value.rstrip(' \t\n\r')

        return ast.Pattern(elements)

    @with_span
    def get_text_element(self, ps):
        buf = ''

        while ps.current():
            ch = ps.current()

            if ch == '{':
                return ast.TextElement(buf)

            if ch == '\n':
                if not ps.is_peek_next_line_value():
                    return ast.TextElement(buf)

                ps.next()
                ps.skip_inline_ws()

                # Add the new line to the buffer
                buf += ch
                continue

            if ch == '\\':
                ps.next()
                buf += self.get_escape_sequence(ps)
            else:
                buf += ch
                ps.next()

        return ast.TextElement(buf)

    def get_escape_sequence(self, ps, specials=('{', '\\')):
        next = ps.current()

        if next in specials:
            ps.next()
            return '\\{}'.format(next)

        if next == 'u':
            sequence = ''
            ps.next()

            for _ in range(4):
                ch = ps.take_hex_digit()
                if ch is None:
                    raise ParseError('E0026', sequence + ps.current())
                sequence += ch

            return '\\u{}'.format(sequence)

        raise ParseError('E0025', next)

    @with_span
    def get_placeable(self, ps):
        ps.expect_char('{')
        expression = self.get_expression(ps)
        ps.expect_char('}')
        return ast.Placeable(expression)

    @with_span
    def get_expression(self, ps):
        ps.skip_inline_ws()

        selector = self.get_selector_expression(ps)

        ps.skip_inline_ws()

        if ps.current_is('-'):
            ps.peek()

            if not ps.current_peek_is('>'):
                ps.reset_peek()
                return selector

            if isinstance(selector, ast.MessageReference):
                raise ParseError('E0016')

            if isinstance(selector, ast.AttributeExpression) \
               and isinstance(selector.ref, ast.MessageReference):
                raise ParseError('E0018')

            if isinstance(selector, ast.VariantExpression):
                raise ParseError('E0017')

            ps.next()
            ps.next()

            ps.skip_inline_ws()

            variants = self.get_variants(ps)

            if len(variants) == 0:
                raise ParseError('E0011')

            # VariantLists are only allowed in other VariantLists.
            if any(isinstance(v.value, ast.VariantList) for v in variants):
                raise ParseError('E0023')

            ps.expect_indent()

            return ast.SelectExpression(selector, variants)
        elif (
            isinstance(selector, ast.AttributeExpression)
            and isinstance(selector.ref, ast.TermReference)
        ):
            raise ParseError('E0019')

        return selector

    @with_span
    def get_selector_expression(self, ps):
        if ps.current_is('{'):
            return self.get_placeable(ps)

        literal = self.get_literal(ps)

        if not isinstance(literal, (ast.MessageReference, ast.TermReference)):
            return literal

        ch = ps.current()

        if (ch == '.'):
            ps.next()
            attr = self.get_identifier(ps)
            return ast.AttributeExpression(literal, attr)

        if (ch == '['):
            ps.next()

            if isinstance(literal, ast.MessageReference):
                raise ParseError('E0024')

            key = self.get_variant_key(ps)
            ps.expect_char(']')
            return ast.VariantExpression(literal, key)

        if (ch == '('):
            ps.next()

            if not re.match('^[A-Z][A-Z_?-]*$', literal.id.name):
                raise ParseError('E0008')

            positional, named = self.get_call_args(ps)
            ps.expect_char(')')

            func = ast.Function(literal.id.name)
            if (self.with_spans):
                func.add_span(literal.span.start, literal.span.end)

            return ast.CallExpression(func, positional, named)

        return literal

    @with_span
    def get_call_arg(self, ps):
        exp = self.get_selector_expression(ps)

        ps.skip_inline_ws()

        if not ps.current_is(':'):
            return exp

        if not isinstance(exp, ast.MessageReference):
            raise ParseError('E0009')

        ps.next()
        ps.skip_inline_ws()

        val = self.get_arg_val(ps)

        return ast.NamedArgument(exp.id, val)

    def get_call_args(self, ps):
        positional = []
        named = []
        argument_names = set()

        ps.skip_inline_ws()
        ps.skip_indent()

        while True:
            if ps.current_is(')'):
                break

            arg = self.get_call_arg(ps)
            if isinstance(arg, ast.NamedArgument):
                if arg.name.name in argument_names:
                    raise ParseError('E0022')
                named.append(arg)
                argument_names.add(arg.name.name)
            elif len(argument_names) > 0:
                raise ParseError('E0021')
            else:
                positional.append(arg)

            ps.skip_inline_ws()
            ps.skip_indent()

            if ps.current_is(','):
                ps.next()
                ps.skip_inline_ws()
                ps.skip_indent()
                continue
            else:
                break

        return positional, named

    def get_arg_val(self, ps):
        if ps.is_number_start():
            return self.get_number(ps)
        elif ps.current_is('"'):
            return self.get_string(ps)
        raise ParseError('E0012')

    @with_span
    def get_string(self, ps):
        val = ''

        ps.expect_char('"')

        ch = ps.take_char(lambda x: x != '"' and x != '\n')
        while ch:
            if ch == '\\':
                val += self.get_escape_sequence(ps, ('{', '\\', '"'))
            else:
                val += ch
            ch = ps.take_char(lambda x: x != '"' and x != '\n')

        if ps.current_is('\n'):
            raise ParseError('E0020')

        ps.next()

        return ast.StringLiteral(val)

    @with_span
    def get_literal(self, ps):
        ch = ps.current()

        if ch is None:
            raise ParseError('E0014')

        if ch == '$':
            ps.next()
            id = self.get_identifier(ps)
            return ast.VariableReference(id)

        elif ps.is_identifier_start():
            id = self.get_identifier(ps)
            return ast.MessageReference(id)

        elif ps.is_number_start():
            return self.get_number(ps)

        elif ch == '-':
            id = self.get_term_identifier(ps)
            return ast.TermReference(id)

        elif ch == '"':
            return self.get_string(ps)

        raise ParseError('E0014')
