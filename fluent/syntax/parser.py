from .ftlstream import FTLParserStream
from . import ast


def parse(string):
    errors = []

    ps = FTLParserStream(string)

    ps.skip_ws_lines()

    entries = []

    while ps.current():
        entry = get_entry(ps)

        if entry:
            entries.append(entry)

        ps.skip_ws_lines()

    resource = ast.Resource(entries)


    return [resource.toJSON(), errors]

def get_entry(ps):
    comment = None

    if ps.current_is('#'):
        comment = get_comment(ps)

    if ps.current_is('['):
        return get_section(ps, comment)

    if ps.is_id_start():
        return get_message(ps, comment)

    return comment

def get_comment(ps):
    ps.expect_char('#')
    ps.take_char_if(' ')

    content = ''

    while True:
        while ps.take_char(lambda x: x != '\n'):
            content += ps.current()

        ps.next()

        if ps.current_is('#'):
            content += '\n'
            ps.next()
            ps.take_char_if(' ')
        else:
            break
    return ast.Comment(content)

def get_section(ps, comment):
    ps.expect_char('[')
    ps.expect_char('[')

    ps.skip_line_ws()

    key = get_keyword(ps)

    ps.skip_line_ws()

    ps.expect_char(']')
    ps.expect_char(']')

    ps.skip_line_ws()

    ps.expect_char('\n')

    return ast.Section(key, comment)

def get_message(ps, comment):
    id = get_identifier(ps)

    ps.skip_line_ws()

    pattern = None
    attrs = None

    if ps.current_is('='):
        ps.next()
        ps.skip_line_ws()

        pattern = get_pattern(ps)

    if ps.is_peek_next_line_attribute_start():
        attrs = get_attributes(ps)

    if pattern is None and attrs is None:
        raise Exception('MissingField')

    return ast.Message(id, pattern, attrs, comment)

def get_attributes(ps):
    attrs = []

    while True:
        ps.expect_char('\n')
        ps.skip_line_ws()

        ps.expect_char('.')

        key = get_identifier(ps)

        ps.skip_line_ws()

        value = get_pattern(ps)

        if value == None:
            raise Exception('ExpectedField')

        attrs.append(ast.Attribute(key, value))

        if not ps.is_peek_next_line_attribute_start():
            break
    return attrs

def get_identifier(ps):
    name = ''

    name += ps.take_id_start()

    ch = ps.take_id_char()
    while ch:
        name += ch
        ch = ps.take_id_char()

    return ast.Identifier(name)

def get_keyword(ps):
    name = ''

    name += ps.take_id_start()

    while True:
        ch = ps.take_kw_char()
        if ch:
            name += ch
        else:
            break

    return ast.Keyword(name.rstrip())

def get_pattern(ps):
    buffer = ''
    elements = []
    quote_delimited = False
    quote_open = False
    first_line = True
    is_indented = False

    if ps.take_char_if('"'):
        quote_delimited = True
        quote_open = True

    while ps.current():
        ch = ps.current()
        if ch == '\n':
            if quote_delimited:
                raise Exception('ExpectedToken')

            if first_line and len(buffer) != 0:
                break

            ps.peek()

            ps.peek_line_ws()

            if not ps.current_peek_is('|'):
                ps.reset_peek()
                break
            else:
                ps.skip_to_peek()
                ps.next()

            if first_line:
                if ps.take_char_if(' '):
                    is_indented = True
            else:
                if is_indented and not ps.take_char_if(' '):
                    raise Exception('Generic')

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
                elements.append(ast.StringExpression(buffer))

            buffer = ''

            elements.append(get_expression(ps))

            ps.expect_char('}')

            continue
        elif ch == '"' and quote_open:
            ps.next()
            quote_open = False
            break
        else:
            buffer += ps.ch
        ps.next()

    if len(buffer) != 0:
        elements.append(ast.StringExpression(buffer))

    return ast.Pattern(elements, quote_delimited)
