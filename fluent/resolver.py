from __future__ import absolute_import, unicode_literals

import attr
import six

from .syntax.ast import (AttributeExpression, CallExpression, ExternalArgument,
                         Message, MessageReference, NamedArgument,
                         NumberExpression, Pattern, Placeable,
                         SelectExpression, StringExpression, Term, TextElement,
                         VariantExpression, VariantName)
from .types import fluent_number, FluentNumber
from .utils import partition

try:
    from functools import singledispatch
except ImportError:
    # Python < 3.4
    from singledispatch import singledispatch


text_type = six.text_type


@attr.s
class ResolverEnvironment(object):
    context = attr.ib()
    args = attr.ib()
    errors = attr.ib()
    dirty = attr.ib(factory=set)


@attr.s
class FluentNone(object):
    name = attr.ib(default=None)


class FluentFormatError(ValueError):
    def __eq__(self, other):
        return ((other.__class__ == self.__class__) and
                other.args == self.args)


class FluentReferenceError(FluentFormatError):
    pass


class FluentCyclicReferenceError(FluentFormatError):
    pass


def resolve(context, message, args, errors=None):
    """
    Given a MessageContext, a Message instance and some arguments,
    resolve the message to a string.

    This is the normal entry point for this module.
    """
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
    if isinstance(retval, text_type):
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


@handle.register(Term)
def handle_term(term, env):
    return handle(term.value, env)


@handle.register(Pattern)
def handle_pattern(pattern, env):
    # TODO: max allowed length etc., use_isolating
    if pattern in env.dirty:
        env.errors.append(FluentCyclicReferenceError("Cyclic reference"))
        return FluentNone()

    env.dirty.add(pattern)
    retval = "".join(fully_resolve(element, env) for element in pattern.elements)
    env.dirty.remove(pattern)
    return retval


@handle.register(TextElement)
def handle_text_element(text_element, env):
    return text_element.value


@handle.register(Placeable)
def handle_placeable(placeable, env):
    return handle(placeable.expression, env)


@handle.register(StringExpression)
def handle_string_expression(string_expression, env):
    return string_expression.value


@handle.register(NumberExpression)
def handle_number_expression(number_expression, env):
    return numeric_to_native(number_expression.value)


@handle.register(MessageReference)
def handle_message_reference(message_reference, env):
    name = message_reference.id.name
    message = None
    if name.startswith("-"):
        try:
            message = env.context._terms[name]
        except LookupError:
            env.errors.append(
                FluentReferenceError("Unknown term: {0}"
                                     .format(name)))
    else:
        try:
            message = env.context._messages[name]
        except LookupError:
            env.errors.append(
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
        FluentReferenceError("Unknown attribute: {0}.{1}"
                             .format(parent_id.name, attr_name)))
    return handle(message, env)


@handle.register(SelectExpression)
def handle_select_expression(expression, env):
    if expression.expression is None:
        key = None
    else:
        key = handle(expression.expression, env)
    return select_from_select_expression(expression, env,
                                         key=key)


def select_from_select_expression(expression, env, key=None):
    default = None
    found = None
    for variant in expression.variants:
        if variant.default:
            default = variant
            if key is None:
                # We only want the default
                break

        compare_value = handle(variant.key, env)
        if match(key, compare_value, env):
            found = variant
            break

    if found is None:
        if (expression.expression is None and key is not None and
                not isinstance(key, FluentNone)):
            # Variants, not full select expressions
            env.errors.append(FluentReferenceError("Unknown variant: {0}"
                                                   .format(key)))
        found = default
    if found is None:
        return FluentNone()
    else:
        return handle(found.value, env)


def is_number(val):
    return isinstance(val, (int, float))


def match(val1, val2, env):
    if val1 is None or isinstance(val1, FluentNone):
        return False
    if val2 is None or isinstance(val2, FluentNone):
        return False
    if is_number(val1):
        if not is_number(val2):
            # Could be plural rule match
            return env.context.plural_form_for_number(val1) == val2
    else:
        if is_number(val2):
            return match(val2, val1, env)

    return val1 == val2


@handle.register(VariantName)
def handle_variant_name(name, env):
    return name.name


@handle.register(VariantExpression)
def handle_variant_expression(expression, env):
    message = handle(MessageReference(expression.ref.id), env)
    if isinstance(message, FluentNone):
        return message

    # TODO How exactly should we handle the case where 'message'
    # is not simply a SelectExpression but has other stuff?
    assert len(message.value.elements) == 1
    select_expression = message.value.elements[0].expression
    assert isinstance(select_expression, SelectExpression)
    assert select_expression.expression is None

    variant_name = expression.key.name
    return select_from_select_expression(select_expression,
                                         env,
                                         key=variant_name)


@handle.register(CallExpression)
def handle_call_expression(expression, env):
    function_name = expression.callee.name
    try:
        function = env.context.functions[function_name]
    except LookupError:
        env.errors.append(FluentReferenceError("Unknown function: {0}"
                                               .format(function_name)))
        return FluentNone(function_name + "()")

    kwargs, args = partition(expression.args,
                             lambda i: isinstance(i, NamedArgument))
    args = [handle(arg, env) for arg in args]
    kwargs = {kwarg.name.name: handle(kwarg.val, env) for kwarg in kwargs}
    try:
        return function(*args, **kwargs)
    except Exception as e:
        env.errors.append(e)
        return FluentNone(function_name + "()")


@handle.register(FluentNumber)
def handle_fluent_number(number, env):
    return number.format(env.context._babel_locale)


@handle.register(int)
def handle_int(integer, env):
    return fluent_number(integer).format(env.context._babel_locale)


@handle.register(float)
def handle_float(f, env):
    return fluent_number(f).format(env.context._babel_locale)


@singledispatch
def handle_argument(arg, name, env):
    env.errors.append(TypeError("Unsupported external type: {0}, {1}"
                                .format(name, type(arg))))
    return FluentNone(name)


@handle_argument.register(int)
def handle_argument_int(arg, name, env):
    return arg


@handle_argument.register(float)
def handle_argument_float(arg, name, env):
    return arg


@handle_argument.register(text_type)
def handle_argument_text(arg, name, env):
    return arg


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
