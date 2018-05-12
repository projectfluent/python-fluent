from __future__ import absolute_import, unicode_literals

import attr
import six

from .syntax.ast import (ExternalArgument, Message, MessageReference, Pattern,
                         Placeable, StringExpression, TextElement)

try:
    from functools import singledispatch
except ImportError:
    # Python < 3.4
    from singledispatch import singledispatch


@attr.s
class ResolverEnvironment(object):
    context = attr.ib()
    args = attr.ib()
    errors = attr.ib()
    dirty = attr.ib(default=set)


@attr.s
class FluentNone(object):
    name = attr.ib()


class ReferenceError(ValueError):
    pass


def resolve(context, args, message, errors=None):
    if errors is None:
        errors = []
    env = ResolverEnvironment(context=context,
                              args=args,
                              errors=errors)
    return handle(message, env)


@singledispatch
def handle(expr, env):
    raise NotImplementedError("Cannot handle object of type {0}"
                              .format(type(expr)))


@handle.register(Message)
def handle_message(message, env):
    return handle(message.value, env)


@handle.register(Pattern)
def handle_pattern(pattern, env):
    # TODO: checking for cycles, max allowed length etc., use_isolating
    return "".join(handle(element, env) for element in pattern.elements)


@handle.register(TextElement)
def handle_text(text, env):
    return text.value


@handle.register(Placeable)
def handle_placeable(placeable, env):
    return handle(placeable.expression, env)


@handle.register(StringExpression)
def handle_string(string, env):
    return string.value


@handle.register(MessageReference)
def handle_message_reference(message_reference, env):
    name = message_reference.id.name
    message = None
    if name.startswith("-"):
        try:
            message = env.context._terms[name]
        except LookupError:
            env.context.errors.append(ReferenceError("Unknown term: {0}"
                                                     .format(name)))
    else:
        try:
            message = env.context._messages[name]
        except LookupError:
            env.context.errors.append(ReferenceError("Unknown message: {0}"
                                                     .format(name)))
    if message is None:
        message = FluentNone(name)

    return handle(message, env)


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
        env.errors.append(ReferenceError("Unknown external: {0}".format(name)))
        return handle(FluentNone(name), env)

    return handle_argument(arg_val, name, env)


@singledispatch
def handle_argument(arg, name, env):
    env.errors.append(TypeError("Unsupported external type: {0}, {1}"
                                .format(name, type(arg))))
    return handle(FluentNone(name), env)


@handle_argument.register(int)
def handle_argument_int(arg, name, env):
    # TODO FluentNumber or something
    return str(arg)


@handle_argument.register(six.text_type)
def handle_argument_text(arg, name, env):
    return arg


# TODO - everything is returning strings at the moment, which is no good for
# things that must delay conversion (e.g. numbers that are passed to function
# calls)
