from __future__ import unicode_literals
from .ftlstream import FTLParserStream
from . import ast
from .errors import ParseError


class FluentParser(object):
    def __init__(self, with_spans=True, with_annotations=True):
        self.with_spans = with_spans
        self.with_annotations = with_annotations

    def parse(self, source):
        comment = None

        ps = FTLParserStream(source)
        ps.skip_ws_lines()

        entries = []

        while ps.current():
            entry = self.get_entry_or_junk(ps)

            if isinstance(entry, ast.Comment) and len(entries) == 0:
                comment = entry
            else:
                entries.append(entry)

            ps.skip_ws_lines()

        return ast.Resource(entries, comment)

    def parse_entry(self, source):
        ps = FTLParserStream(source)
        ps.skip_ws_lines()
        return self.get_entry_or_junk(ps)

    def get_entry_or_junk(self, ps):
        entry_start_pos = ps.get_index()

        try:
            entry = self.get_entry(ps)
            if self.with_spans:
                entry.add_span(entry_start_pos, ps.get_index())
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
            if self.with_annotations:
                annot = ast.Annotation(err.code, err.args, err.message)
                annot.add_span(error_index, error_index)
                junk.add_annotation(annot)
            return junk

    def get_entry(self, ps):
        comment = None

        if ps.current_is('/'):
            comment = self.get_comment(ps)

        if ps.current_is('['):
            return self.get_section(ps, comment)

        if ps.is_id_start():
            return self.get_message(ps, comment)

        if comment:
            return comment

        raise ParseError('E0002')

    def get_comment(self, ps):
        ps.expect_char('/')
        ps.expect_char('/')
        ps.take_char_if(' ')

        content = ''

        def until_eol(x):
            return x != '\n'

        while True:
            ch = ps.take_char(until_eol)
            while ch:
                content += ch
                ch = ps.take_char(until_eol)

            ps.next()

            if ps.current_is('/'):
                content += '\n'
                ps.next()
                ps.expect_char('/')
                ps.take_char_if(' ')
            else:
                break
        return ast.Comment(content)

    def get_section(self, ps, comment):
        ps.expect_char('[')
        ps.expect_char('[')

        ps.skip_line_ws()

        symb = self.get_symbol(ps)

        ps.skip_line_ws()

        ps.expect_char(']')
        ps.expect_char(']')

        ps.skip_line_ws()

        ps.expect_char('\n')

        return ast.Section(symb, comment)

    def get_message(self, ps, comment):
        id = self.get_identifier(ps)

        ps.skip_line_ws()

        pattern = None
        attrs = None
        tags = None

        if ps.current_is('='):
            ps.next()
            ps.skip_line_ws()

            pattern = self.get_pattern(ps)

        if ps.is_peek_next_line_attribute_start():
            attrs = self.get_attributes(ps)

        if ps.is_peek_next_line_tag_start():
            if attrs is not None:
                raise ParseError('E0012')
            tags = self.get_tags(ps)

        if pattern is None and attrs is None and tags is None:
            raise ParseError('E0005', id.name)

        return ast.Message(id, pattern, attrs, tags, comment)

    def get_attributes(self, ps):
        attrs = []

        while True:
            ps.expect_char('\n')
            ps.skip_line_ws()

            ps.expect_char('.')

            key = self.get_identifier(ps)

            ps.skip_line_ws()
            ps.expect_char('=')
            ps.skip_line_ws()

            value = self.get_pattern(ps)

            if value is None:
                raise ParseError('E0006', 'value')

            attrs.append(ast.Attribute(key, value))

            if not ps.is_peek_next_line_attribute_start():
                break
        return attrs

    def get_tags(self, ps):
        tags = []

        while True:
            ps.expect_char('\n')
            ps.skip_line_ws()

            ps.expect_char('#')

            symb = self.get_symbol(ps)

            tags.append(ast.Tag(symb))

            if not ps.is_peek_next_line_tag_start():
                break
        return tags

    def get_identifier(self, ps):
        name = ''

        name += ps.take_id_start()

        ch = ps.take_id_char()
        while ch:
            name += ch
            ch = ps.take_id_char()

        return ast.Identifier(name)

    def get_variant_key(self, ps):
        ch = ps.current()

        if ch is None:
            raise ParseError('E0013')

        if ps.is_number_start():
            return self.get_number(ps)

        return self.get_symbol(ps)

    def get_variants(self, ps):
        variants = []
        has_default = False

        while True:
            default_index = False

            ps.expect_char('\n')
            ps.skip_line_ws()

            if ps.current_is('*'):
                if has_default:
                    raise ParseError('E0015')
                ps.next()
                default_index = True
                has_default = True

            ps.expect_char('[')

            key = self.get_variant_key(ps)

            ps.expect_char(']')

            ps.skip_line_ws()

            value = self.get_pattern(ps)

            if value is None:
                raise ParseError('E0006', 'value')

            variants.append(ast.Variant(key, value, default_index))

            if not ps.is_peek_next_line_variant_start():
                break

        if not has_default:
            raise ParseError('E0010')

        return variants

    def get_symbol(self, ps):
        name = ''

        name += ps.take_id_start()

        while True:
            ch = ps.take_symb_char()
            if ch:
                name += ch
            else:
                break

        return ast.Symbol(name.rstrip())

    def get_digits(self, ps):
        num = ''

        ch = ps.take_digit()
        while ch:
            num += ch
            ch = ps.take_digit()

        if len(num) == 0:
            raise ParseError('E0004', '0-9')

        return num

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

        return ast.NumberExpression(num)

    def get_pattern(self, ps):
        buffer = ''
        elements = []
        first_line = True

        while ps.current():
            ch = ps.current()
            if ch == '\n':
                if first_line and len(buffer) != 0:
                    break

                if not ps.is_peek_next_line_pattern():
                    break

                ps.next()
                ps.skip_line_ws()

                if not first_line:
                    buffer += ch

                first_line = False
                continue
            elif ch == '\\':
                ch2 = ps.peek()

                if ch2 == '{' or ch2 == '"':
                    buffer += ch2
                else:
                    buffer += ch + ch2
                ps.next()
            elif ch == '{':
                ps.next()

                ps.skip_line_ws()

                if len(buffer) != 0:
                    elements.append(ast.TextElement(buffer))

                buffer = ''

                elements.append(self.get_expression(ps))

                ps.expect_char('}')

                continue
            else:
                buffer += ps.ch
            ps.next()

        if len(buffer) != 0:
            elements.append(ast.TextElement(buffer))

        return ast.Pattern(elements)

    def get_expression(self, ps):
        if ps.is_peek_next_line_variant_start():
            variants = self.get_variants(ps)

            ps.expect_char('\n')
            ps.expect_char(' ')
            ps.skip_line_ws()

            return ast.SelectExpression(None, variants)

        selector = self.get_selector_expression(ps)

        ps.skip_line_ws()

        if ps.current_is('-'):
            ps.peek()
            if not ps.current_peek_is('>'):
                ps.reset_peek()
            else:
                ps.next()
                ps.next()

                ps.skip_line_ws()

                variants = self.get_variants(ps)

                if len(variants) == 0:
                    raise ParseError('E0011')

                ps.expect_char('\n')
                ps.expect_char(' ')
                ps.skip_line_ws()

                return ast.SelectExpression(selector, variants)

        return selector

    def get_selector_expression(self, ps):
        literal = self.get_literal(ps)

        if not isinstance(literal, ast.MessageReference):
            return literal

        ch = ps.current()

        if (ch == '.'):
            ps.next()
            attr = self.get_identifier(ps)
            return ast.AttributeExpression(literal.id, attr)

        if (ch == '['):
            ps.next()
            key = self.get_variant_key(ps)
            ps.expect_char(']')
            return ast.VariantExpression(literal.id, key)

        if (ch == '('):
            ps.next()

            args = self.get_call_args(ps)

            ps.expect_char(')')

            return ast.CallExpression(literal.id, args)

        return literal

    def get_call_args(self, ps):
        args = []

        ps.skip_line_ws()

        while True:
            if ps.current_is(')'):
                break

            exp = self.get_selector_expression(ps)

            ps.skip_line_ws()

            if ps.current_is(':'):
                if not isinstance(exp, ast.MessageReference):
                    raise ParseError('E0009')

                ps.next()
                ps.skip_line_ws()

                val = self.get_arg_val(ps)

                args.append(ast.NamedArgument(exp.id, val))
            else:
                args.append(exp)

            ps.skip_line_ws()

            if ps.current_is(','):
                ps.next()
                ps.skip_line_ws()
                continue
            else:
                break

        return args

    def get_arg_val(self, ps):
        if ps.is_number_start():
            return self.get_number(ps)
        elif ps.current_is('"'):
            return self.get_string(ps)
        raise ParseError('E0006', 'value')

    def get_string(self, ps):
        val = ''

        ps.expect_char('"')

        ch = ps.take_char(lambda x: x != '"')
        while ch:
            val += ch
            ch = ps.take_char(lambda x: x != '"')

        ps.next()

        return ast.StringExpression(val)

    def get_literal(self, ps):
        ch = ps.current()

        if ch is None:
            raise ParseError('E0014')

        if ps.is_number_start():
            return self.get_number(ps)
        elif ch == '"':
            return self.get_string(ps)
        elif ch == '$':
            ps.next()
            name = self.get_identifier(ps)
            return ast.ExternalArgument(name)

        name = self.get_identifier(ps)
        return ast.MessageReference(name)
