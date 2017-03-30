from __future__ import unicode_literals
from .ftlstream import FTLParserStream
from . import ast
from .errors import ParseError


def parse(source):
    comment = None

    ps = FTLParserStream(source)
    ps.skip_ws_lines()

    entries = []

    while ps.current():
        entry = get_entry_or_junk(ps)

        if isinstance(entry, ast.Comment) and len(entries) == 0:
            comment = entry
        else:
            entries.append(entry)

        ps.skip_ws_lines()

    return ast.Resource(entries, comment)


def parse_entry(source):
    ps = FTLParserStream(source)
    ps.skip_ws_lines()
    return get_entry_or_junk(ps)


def get_entry_or_junk(ps):
    entry_start_pos = ps.get_index()

    try:
        entry = get_entry(ps)
        entry.add_span(entry_start_pos, ps.get_index())
        return entry
    except ParseError as err:
        annot = ast.Annotation("ParseError", err.message, ps.get_index())

        ps.skip_to_next_entry_start()
        next_entry_start = ps.get_index()

        # Create a Junk instance
        slice = ps.get_slice(entry_start_pos, next_entry_start)
        junk = ast.Junk(slice)
        junk.add_span(entry_start_pos, next_entry_start)
        junk.add_annotation(annot)
        return junk


def get_entry(ps):
    comment = None

    if ps.current_is('/'):
        comment = get_comment(ps)

    if ps.current_is('['):
        return get_section(ps, comment)

    if ps.is_id_start():
        return get_message(ps, comment)

    if comment:
        return comment
    raise ParseError('Expected entry')

def get_comment(ps):
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

def get_section(ps, comment):
    ps.expect_char('[')
    ps.expect_char('[')

    ps.skip_line_ws()

    symb = get_symbol(ps)

    ps.skip_line_ws()

    ps.expect_char(']')
    ps.expect_char(']')

    ps.skip_line_ws()

    ps.expect_char('\n')

    return ast.Section(symb, comment)

def get_message(ps, comment):
    id = get_identifier(ps)

    ps.skip_line_ws()

    pattern = None
    attrs = None
    tags = None

    if ps.current_is('='):
        ps.next()
        ps.skip_line_ws()

        pattern = get_pattern(ps)

    if ps.is_peek_next_line_attribute_start():
        attrs = get_attributes(ps)

    if ps.is_peek_next_line_tag_start():
        if attrs is not None:
            raise ParseError(
                'Tags cannot be added to messages with attributes')
        tags = get_tags(ps)

    if pattern is None and attrs is None and tags is None:
        raise ParseError('Missing field')

    return ast.Message(id, pattern, attrs, tags, comment)

def get_attributes(ps):
    attrs = []

    while True:
        ps.expect_char('\n')
        ps.skip_line_ws()

        ps.expect_char('.')

        key = get_identifier(ps)

        ps.skip_line_ws()
        ps.expect_char('=')
        ps.skip_line_ws()

        value = get_pattern(ps)

        if value is None:
            raise ParseError('Expected field')

        attrs.append(ast.Attribute(key, value))

        if not ps.is_peek_next_line_attribute_start():
            break
    return attrs

def get_tags(ps):
    tags = []

    while True:
        ps.expect_char('\n')
        ps.skip_line_ws()

        ps.expect_char('#')

        symb = get_symbol(ps)

        tags.append(ast.Tag(symb))

        if not ps.is_peek_next_line_tag_start():
            break
    return tags

def get_identifier(ps):
    name = ''

    name += ps.take_id_start()

    ch = ps.take_id_char()
    while ch:
        name += ch
        ch = ps.take_id_char()

    return ast.Identifier(name)

def get_variant_key(ps):
    ch = ps.current()

    if ch is None:
        raise ParseError('Expected variant key')

    if ps.is_number_start():
        return get_number(ps)

    return get_symbol(ps)

def get_variants(ps):
    variants = []
    has_default = False

    while True:
        default_index = False

        ps.expect_char('\n')
        ps.skip_line_ws()

        if ps.current_is('*'):
            ps.next()
            default_index = True
            has_default = True

        ps.expect_char('[')

        key = get_variant_key(ps)

        ps.expect_char(']')

        ps.skip_line_ws()

        value = get_pattern(ps)

        if value is None:
            raise ParseError('Expected field')

        variants.append(ast.Variant(key, value, default_index))

        if not ps.is_peek_next_line_variant_start():
            break

    if not has_default:
        raise ParseError('Missing default variant')

    return variants

def get_symbol(ps):
    name = ''

    name += ps.take_id_start()

    while True:
        ch = ps.take_symb_char()
        if ch:
            name += ch
        else:
            break

    return ast.Symbol(name.rstrip())

def get_digits(ps):
    num = ''

    ch = ps.take_digit()
    while ch:
        num += ch
        ch = ps.take_digit()

    if len(num) == 0:
        raise ParseError('Expected char range')

    return num

def get_number(ps):
    num = ''

    if ps.current_is('-'):
        num += '-'
        ps.next()

    num += get_digits(ps)

    if ps.current_is('.'):
        num += '.'
        ps.next()
        num += get_digits(ps)

    return ast.NumberExpression(num)

def get_pattern(ps):
    buffer = ''
    elements = []
    first_line = True

    while ps.current():
        ch = ps.current()
        if ch == '\n':
            if first_line and len(buffer) != 0:
                break

            ps.peek()

            if not ps.current_peek_is(' '):
                ps.reset_peek()
                break

            ps.peek_line_ws()
            ps.skip_to_peek()

            first_line = False

            if len(buffer) != 0:
                buffer += ch
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

            elements.append(get_expression(ps))

            ps.expect_char('}')

            continue
        else:
            buffer += ps.ch
        ps.next()

    if len(buffer) != 0:
        elements.append(ast.TextElement(buffer))

    return ast.Pattern(elements)

def get_expression(ps):
    if ps.is_peek_next_line_variant_start():
        variants = get_variants(ps)

        ps.expect_char('\n')
        ps.expect_char(' ')
        ps.skip_line_ws()

        return ast.SelectExpression(None, variants)

    selector = get_selector_expression(ps)

    ps.skip_line_ws()

    if ps.current_is('-'):
        ps.peek()
        if not ps.current_peek_is('>'):
            ps.reset_peek()
        else:
            ps.next()
            ps.next()

            ps.skip_line_ws()

            variants = get_variants(ps)

            if len(variants) == 0:
                raise ParseError('Missing variables')

            ps.expect_char('\n')
            ps.expect_char(' ')
            ps.skip_line_ws()

            return ast.SelectExpression(selector, variants)

    return selector

def get_selector_expression(ps):
    literal = get_literal(ps)

    if not isinstance(literal, ast.MessageReference):
        return literal

    ch = ps.current()

    if (ch == '.'):
        ps.next()
        attr = get_identifier(ps)
        return ast.AttributeExpression(literal.id, attr)

    if (ch == '['):
        ps.next()
        key = get_variant_key(ps)
        ps.expect_char(']')
        return ast.VariantExpression(literal.id, key)

    if (ch == '('):
        ps.next()

        args = get_call_args(ps)

        ps.expect_char(')')

        return ast.CallExpression(literal.id, args)

    return literal

def get_call_args(ps):
    args = []

    ps.skip_line_ws()

    while True:
        if ps.current_is(')'):
            break

        exp = get_selector_expression(ps)

        ps.skip_line_ws()

        if ps.current_is(':'):
            if not isinstance(exp, ast.MessageReference):
                raise ParseError('Forbidden key')

            ps.next()
            ps.skip_line_ws()

            val = get_arg_val(ps)

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

def get_arg_val(ps):
    if ps.is_number_start():
        return get_number(ps)
    elif ps.current_is('"'):
        return get_string(ps)
    raise ParseError('Expected field')

def get_string(ps):
    val = ''

    ps.expect_char('"')

    ch = ps.take_char(lambda x: x != '"')
    while ch:
        val += ch
        ch = ps.take_char(lambda x: x != '"')

    ps.next()

    return ast.StringExpression(val)

def get_literal(ps):
    ch = ps.current()

    if ch is None:
        raise ParseError('Expected literal')

    if ps.is_number_start():
        return get_number(ps)
    elif ch == '"':
        return get_string(ps)
    elif ch == '$':
        ps.next()
        name = get_identifier(ps)
        return ast.ExternalArgument(name)

    name = get_identifier(ps)
    return ast.MessageReference(name)
