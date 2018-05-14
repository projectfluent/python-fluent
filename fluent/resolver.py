from __future__ import absolute_import, unicode_literals

import attr
import six

from .syntax.ast import (AttributeExpression, ExternalArgument, Message,
                         MessageReference, Pattern, Placeable,
                         StringExpression, TextElement)

try:
    from functools import singledispatch
except ImportError:
    # Python < 3.4
    from singledispatch import singledispatch


text_type = six.text_type
string_types = six.string_types


@attr.s
class ResolverEnvironment(object):
    context = attr.ib()
    args = attr.ib()
    errors = attr.ib()
    dirty = attr.ib(default=set)


@attr.s
class FluentNone(object):
    name = attr.ib()


class FluentReferenceError(ValueError):
    pass


def resolve(context, args, message, errors=None):
    if errors is None:
        errors = []
    env = ResolverEnvironment(context=context,
                              args=args,
                              errors=errors)
    return fully_resolve(message, env)


def fully_resolve(expr, env):
    """
    Fully resolve an expression to a string
    """
    # This differs from 'handle' in that 'handle' will often return non-string
    # objects, even if a string could have been returned, to allow for further
    # handling of that object e.g. attributes of messages. fully_resolve is
    # only used when we must have a string.
    retval = handle(expr, env)
    if isinstance(retval, string_types):
        return retval
    else:
        return fully_resolve(retval, env)


@singledispatch
def handle(expr, env):
    raise NotImplementedError("Cannot handle object of type {0}"
                              .format(type(expr).__name__))


@handle.register(Message)
def handle_message(message, env):
    return handle(message.value, env)


@handle.register(Pattern)
def handle_pattern(pattern, env):
    # TODO: checking for cycles, max allowed length etc., use_isolating
    return "".join(fully_resolve(element, env) for element in pattern.elements)


@handle.register(TextElement)
def handle_text_element(text_element, env):
    return text_element.value


@handle.register(Placeable)
def handle_placeable(placeable, env):
    return handle(placeable.expression, env)


@handle.register(StringExpression)
def handle_string_expression(string_expression, env):
    return string_expression.value


@handle.register(MessageReference)
def handle_message_reference(message_reference, env):
    name = message_reference.id.name
    message = None
    if name.startswith("-"):
        try:
            message = env.context._terms[name]
        except LookupError:
            env.context.errors.append(
                FluentReferenceError("Unknown term: {0}"
                                     .format(name)))
    else:
        try:
            message = env.context._messages[name]
        except LookupError:
            env.context.errors.append(
                FluentReferenceError("Unknown message: {0}"
                                     .format(name)))
    if message is None:
        message = FluentNone(name)

    return message


@handle.register(FluentNone)
def handle_fluent_none(none, env):
    # TODO - tests.
    return none.name or "???"


@handle.register(ExternalArgument)
def handle_external_argument(argument, env):
    name = argument.id.name
    try:
        arg_val = env.args[name]
    except LookupError:
        env.errors.append(
            FluentReferenceError("Unknown external: {0}".format(name)))
        return FluentNone(name)

    return handle_argument(arg_val, name, env)


@handle.register(AttributeExpression)
def handle_attribute_expression(attribute, env):
    parent_id = attribute.id
    attr_name = attribute.name.name
    message = handle(MessageReference(parent_id), env)
    if isinstance(message, FluentNone):
        return message

    for message_attr in message.attributes:
        if message_attr.id.name == attr_name:
            return handle(message_attr.value, env)

    env.errors.append(
        FluentReferenceError("Unknown attribute: {0}.{0}"
                             .format(parent_id.name, attr_name)))
    return handle(message, env)


@singledispatch
def handle_argument(arg, name, env):
    env.errors.append(TypeError("Unsupported external type: {0}, {1}"
                                .format(name, type(arg))))
    return FluentNone(name)


@handle_argument.register(int)
def handle_argument_int(arg, name, env):
    # TODO FluentNumber or something
    return text_type(arg)


@handle_argument.register(text_type)
def handle_argument_text(arg, name, env):
    return arg
