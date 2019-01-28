from fluent.syntax.ast import AttributeExpression, TermReference

from .errors import FluentReferenceError


def numeric_to_native(val):
    """
    Given a numeric string (as defined by fluent spec),
    return an int or float
    """
    # val matches this EBNF:
    #  '-'? [0-9]+ ('.' [0-9]+)?
    if '.' in val:
        return float(val)
    else:
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
        return "{0}.{1}".format(reference_to_id(ref.ref),
                                ref.name.name)
    return ('-' if isinstance(ref, TermReference) else '') + ref.id.name


def unknown_reference_error_obj(ref_id):
    if '.' in ref_id:
        return FluentReferenceError("Unknown attribute: {0}".format(ref_id))
    elif ref_id.startswith('-'):
        return FluentReferenceError("Unknown term: {0}".format(ref_id))
    else:
        return FluentReferenceError("Unknown message: {0}".format(ref_id))
