from . import ast


def indent(content):
    return "    ".join(
        content.splitlines(True)
    )


def contain_new_line(elems):
    return bool([
        elem for elem in elems
        if isinstance(elem, ast.TextElement) and "\n" in elem.value
    ])


def serialize(resource, with_junk=False):
    parts = []
    if resource.comment:
        parts.append(
            "{}\n\n".format(
                serialize_comment(resource.comment)
            )
        )
    for entry in resource.body:
        if isinstance(entry, ast.JunkEntry) and with_junk:
            parts.append(serialize_junk(entry))
        if isinstance(entry, ast.Section):
            parts.append(serialize_section(entry))
        if isinstance(entry, ast.Message):
            parts.append(serialize_message(entry))

    return ''.join(parts).strip()


def serialize_comment(comment):
    return ''.join([
        "{}{}".format("# ", line)
        for line in comment.content.splitlines(True)
    ])


def serialize_section(section):
    if section.comment:
        return "\n\n{}\n[[ {} ]]\n\n".format(
            serialize_comment(section.comment),
            serialize_variant_key(section.key)
        )
    else:
        return "\n\n[[ {} ]]\n\n".format(
            serialize_variant_key(section.key)
        )


def serialize_junk(junk):
    return junk.content


def serialize_message(message):
    parts = []

    if message.comment:
        parts.append(serialize_comment(message.comment))
        parts.append("\n")

    parts.append(serialize_identifier(message.id))

    if message.value:
        parts.append(" =")
        parts.append(serialize_value(message.value))

    if message.attributes:
        for attribute in message.attributes:
            parts.append(serialize_attribute(attribute))

    parts.append("\n")

    return ''.join(parts)


def serialize_attribute(attribute):
    return "\n    .{} ={}".format(
        serialize_identifier(attribute.id),
        serialize_value(attribute.value, indent=1)
    )


def serialize_value(pattern, indent=0):
    multi = bool(filter(
        contains_new_line, pattern.elements
    ))

    schema = " {}"

    if (multi):
        indent += 1
        schema = "\n{}| {{}}".format(" " * 4 * indent)

    return schema.format(
        serialize_pattern(pattern, indent, multi)
    )


def serialize_pattern(pattern, indent=0, multi=False):
    schema = "\"{}\"" if pattern.quoted else "{}"
    return schema.format(
        "".join([
            serialize_element(elem, indent, multi)
            for elem in pattern.elements
        ])
    )


def serialize_element(element, indent=0, multi=False):
    if isinstance(element, ast.StringExpression):
        return serialize_string_expression(element, indent, multi)
    if isinstance(element, ast.Pattern):
        return "{{ {} }}".format(
            serialize_pattern(element, indent)
        )
    if isinstance(element, ast.SelectExpression):
        return "{{{}}}".format(
            serialize_select_expression(element, indent)
        )
    if isinstance(element, ast.Expression):
        return "{{ {} }}".format(
            serialize_expression(element)
        )


def serialize_expression(expression):
    if isinstance(expression, ast.Pattern):
        return serialize_pattern(expression)
    if isinstance(expression, ast.NumberExpression):
        return serialize_number_expression(expression)
    if isinstance(expression, ast.MessageReference):
        return serialize_message_reference(expression)
    if isinstance(expression, ast.ExternalArgument):
        return serialize_external_argument(expression)
    if isinstance(expression, ast.AttributeExpression):
        return serialize_attribute_expression(expression)
    if isinstance(expression, ast.VariantExpression):
        return serialize_variant_expression(expression)
    if isinstance(expression, ast.CallExpression):
        return serialize_call_expression(expression)


def serialize_string_expression(expr, indent=0, multi=False):
    if multi:
        return "{}| ".format(" " * 4 * indent).join(
            expr.value.splitlines(True)
        )
    else:
        return expr.value


def serialize_number_expression(expr):
    return expr.value


def serialize_message_reference(expr):
    return serialize_identifier(expr.id)


def serialize_external_argument(expr):
    return "${}".format(serialize_identifier(expr.id))


def serialize_select_expression(expr, indent=0):
    parts = []

    if expr.expression:
        selector = " {} ->".format(
            serialize_expression(expr.expression)
        )
        parts.append(selector)

    for variant in expr.variants:
        parts.append(serialize_variant(variant, indent + 1))

    parts.append("\n{}".format(" " * 4 * indent))

    return "".join(parts)


def serialize_variant(variant, indent=0):
    return "\n{}{}[{}]{}".format(
        " " * (4 * indent - 1),
        "*" if variant.default else " ",
        serialize_variant_key(variant.key),
        serialize_value(variant.value, indent)
    )


def serialize_attribute_expression(expr):
    return "{}.{}".format(
        serialize_identifier(expr.id),
        serialize_identifier(expr.name),
    )


def serialize_variant_expression(expr):
    return "{}[{}]".format(
        serialize_identifier(expr.id),
        serialize_variant_key(expr.key),
    )


def serialize_call_expression(expr):
    return "{}({})".format(
        serialize_function(expr.callee),
        ", ".join([
            serialize_call_argument(arg)
            for arg in expr.args
        ])
    )


def serialize_call_argument(arg):
    if isinstance(arg, ast.Pattern):
        return serialize_pattern(arg)
    if isinstance(arg, ast.Expression):
        return serialize_expression(arg)
    if isinstance(arg, ast.NamedArgument):
        return serialize_named_argument(arg)


def serialize_named_argument(arg):
    return "{}: {}".format(
        serialize_identifier(arg.name),
        serialize_argument_value(arg.val)
    )


def serialize_argument_value(argval):
    if isinstance(argval, ast.StringExpression):
        return "\"{}\"".format(
            serialize_string_expression(argval)
        )
    if isinstance(argval, ast.NumberExpression):
        return serialize_number_expression(argval)


def serialize_identifier(identifier):
    return identifier.name


def serialize_variant_key(key):
    if isinstance(key, ast.Keyword):
        return key.name
    if isinstance(key, ast.NumberExpression):
        return serialize_number_expression(key)


def serialize_function(function):
    return function.name
