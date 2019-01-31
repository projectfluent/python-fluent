from fluent.syntax.ast import AttributeExpression, Term, TermReference

from .errors import FluentReferenceError

TERM_SIGIL = '-'
ATTRIBUTE_SEPARATOR = '.'


def ast_to_id(ast):
    """
    Returns a string reference for a Term or Message
    """
    if isinstance(ast, Term):
        return TERM_SIGIL + ast.id.name
    return ast.id.name


def add_message_and_attrs_to_store(store, ref_id, item, is_parent=True):
    store[ref_id] = item
    if is_parent:
        for attr in item.attributes:
            add_message_and_attrs_to_store(store,
                                           _make_attr_id(ref_id, attr.id.name),
                                           attr,
                                           is_parent=False)


def numeric_to_native(val):
    """
    Given a numeric string (as defined by fluent spec),
    return an int or float
    """
    # val matches this EBNF:
    #  '-'? [0-9]+ ('.' [0-9]+)?
    if '.' in val:
        return float(val)
    return int(val)


def reference_to_id(ref):
    """
    Returns a string reference for a MessageReference, TermReference or AttributeExpression
    AST node.

    e.g.
       message
       message.attr
       -term
       -term.attr
    """
    if isinstance(ref, AttributeExpression):
        return _make_attr_id(reference_to_id(ref.ref),
                             ref.name.name)
    if isinstance(ref, TermReference):
        return TERM_SIGIL + ref.id.name
    return ref.id.name


def unknown_reference_error_obj(ref_id):
    if ATTRIBUTE_SEPARATOR in ref_id:
        return FluentReferenceError("Unknown attribute: {0}".format(ref_id))
    if ref_id.startswith(TERM_SIGIL):
        return FluentReferenceError("Unknown term: {0}".format(ref_id))
    return FluentReferenceError("Unknown message: {0}".format(ref_id))


def _make_attr_id(parent_ref_id, attr_name):
    """
    Given a parent id and the attribute name, return the attribute id
    """
    return ''.join([parent_ref_id, ATTRIBUTE_SEPARATOR, attr_name])
