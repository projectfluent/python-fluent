from __future__ import absolute_import, unicode_literals

import attr

from .syntax.ast import Message, Pattern, TextElement

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
    return "".join(handle(element, env) for element in pattern.elements)


@handle.register(TextElement)
def handle_text(text, env):
    return text.value
