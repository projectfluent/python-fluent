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

def get_identifier(ps):
    name = ''

    name += ps.take_id_start()

    ch = ps.take_id_char()
    while ch:
        name += ch
        ch = ps.take_id_char()

    return ast.Identifier(name)
