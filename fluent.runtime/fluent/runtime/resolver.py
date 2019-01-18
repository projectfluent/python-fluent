from __future__ import absolute_import, unicode_literals

from datetime import date, datetime
from decimal import Decimal

import attr
import six

from fluent.syntax.ast import (AttributeExpression, CallExpression, Message,
                               MessageReference, NumberLiteral, Pattern,
                               Placeable, SelectExpression, StringLiteral, Term,
                               TermReference, TextElement, VariableReference,
                               VariantExpression, VariantList, Identifier)

from .errors import FluentCyclicReferenceError, FluentReferenceError
from .types import FluentDateType, FluentNone, FluentNumber, fluent_date, fluent_number
from .utils import numeric_to_native

try:
    from functools import singledispatch
except ImportError:
    # Python < 3.4
    from singledispatch import singledispatch


text_type = six.text_type

# Prevent expansion of too long placeables, for memory DOS protection
MAX_PART_LENGTH = 2500

# Prevent messages with too many sub parts, for CPI DOS protection
MAX_PARTS = 1000


# Unicode bidi isolation characters.
FSI = "\u2068"
PDI = "\u2069"


@attr.s
class ResolverEnvironment(object):
    context = attr.ib()
    args = attr.ib()
    errors = attr.ib()
    dirty = attr.ib(factory=set)
    part_count = attr.ib(default=0)


def resolve(context, message, args):
    """
    Given a FluentBundle, a Message instance and some arguments,
    resolve the message to a string.

    This is the normal entry point for this module.
    """
    errors = []
    env = ResolverEnvironment(context=context,
                              args=args,
                              errors=errors)
    return fully_resolve(message, env), errors


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
    if pattern in env.dirty:
        env.errors.append(FluentCyclicReferenceError("Cyclic reference"))
        return FluentNone()

    env.dirty.add(pattern)

    parts = []
    use_isolating = env.context._use_isolating and len(pattern.elements) > 1

    for element in pattern.elements:
        env.part_count += 1
        if env.part_count > MAX_PARTS:
            if env.part_count == MAX_PARTS + 1:
                # Only append an error once.
                env.errors.append(ValueError("Too many parts in message (> {0}), "
                                             "aborting.".format(MAX_PARTS)))
                parts.append(fully_resolve(FluentNone(), env))
            break

        if isinstance(element, TextElement):
            # shortcut deliberately omits the FSI/PDI chars here.
            parts.append(element.value)
            continue

        part = fully_resolve(element, env)
        if use_isolating:
            parts.append(FSI)
        if len(part) > MAX_PART_LENGTH:
            env.errors.append(ValueError(
                "Too many characters in part, "
                "({0}, max allowed is {1})".format(len(part),
                                                   MAX_PART_LENGTH)))
            part = part[:MAX_PART_LENGTH]
        parts.append(part)
        if use_isolating:
            parts.append(PDI)
    retval = "".join(parts)
    env.dirty.remove(pattern)
    return retval


@handle.register(TextElement)
def handle_text_element(text_element, env):
    return text_element.value


@handle.register(Placeable)
def handle_placeable(placeable, env):
    return handle(placeable.expression, env)


@handle.register(StringLiteral)
def handle_string_expression(string_expression, env):
    return string_expression.value


@handle.register(NumberLiteral)
def handle_number_expression(number_expression, env):
    return numeric_to_native(number_expression.value)


@handle.register(MessageReference)
def handle_message_reference(message_reference, env):
    name = message_reference.id.name
    return handle(lookup_reference(name, env), env)


@handle.register(TermReference)
def handle_term_reference(term_reference, env):
    name = term_reference.id.name
    return handle(lookup_reference(name, env), env)


def lookup_reference(name, env):
    message = None
    try:
        message = env.context._messages_and_terms[name]
    except LookupError:
        if name.startswith("-"):
            env.errors.append(
                FluentReferenceError("Unknown term: {0}"
                                     .format(name)))
        else:
            env.errors.append(
                FluentReferenceError("Unknown message: {0}"
                                     .format(name)))
    if message is None:
        message = FluentNone(name)

    return message


@handle.register(FluentNone)
def handle_fluent_none(none, env):
    return none.format(env.context._babel_locale)


@handle.register(type(None))
def handle_none(none, env):
    # We raise the same error type here as when a message is completely missing.
    raise LookupError("Message body not defined")


@handle.register(VariableReference)
def handle_variable_reference(argument, env):
    name = argument.id.name
    try:
        arg_val = env.args[name]
    except LookupError:
        env.errors.append(
            FluentReferenceError("Unknown external: {0}".format(name)))
        return FluentNone(name)

    if isinstance(arg_val,
                  (int, float, Decimal,
                   date, datetime,
                   text_type)):
        return arg_val
    env.errors.append(TypeError("Unsupported external type: {0}, {1}"
                                .format(name, type(arg_val))))
    return FluentNone(name)


@handle.register(AttributeExpression)
def handle_attribute_expression(attribute, env):
    parent_id = attribute.ref.id.name
    attr_name = attribute.name.name
    message = lookup_reference(parent_id, env)
    if isinstance(message, FluentNone):
        return message

    for message_attr in message.attributes:
        if message_attr.id.name == attr_name:
            return handle(message_attr.value, env)

    env.errors.append(
        FluentReferenceError("Unknown attribute: {0}.{1}"
                             .format(parent_id, attr_name)))
    return handle(message, env)


@handle.register(VariantList)
def handle_variant_list(variant_list, env):
    return select_from_variant_list(variant_list, env, None)


def select_from_variant_list(variant_list, env, key):
    found = None
    for variant in variant_list.variants:
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
        if (key is not None and not isinstance(key, FluentNone)):
            env.errors.append(FluentReferenceError("Unknown variant: {0}"
                                                   .format(key)))
        found = default
    if found is None:
        return FluentNone()
    else:
        return handle(found.value, env)


@handle.register(SelectExpression)
def handle_select_expression(expression, env):
    key = handle(expression.selector, env)
    return select_from_select_expression(expression, env,
                                         key=key)


def select_from_select_expression(expression, env, key):
    default = None
    found = None
    for variant in expression.variants:
        if variant.default:
            default = variant

        compare_value = handle(variant.key, env)
        if match(key, compare_value, env):
            found = variant
            break

    if found is None:
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
            return env.context._plural_form(val1) == val2
    else:
        if is_number(val2):
            return match(val2, val1, env)

    return val1 == val2


@handle.register(Identifier)
def handle_indentifier(identifier, env):
    return identifier.name


@handle.register(VariantExpression)
def handle_variant_expression(expression, env):
    message = lookup_reference(expression.ref.id.name, env)
    if isinstance(message, FluentNone):
        return message

    # TODO What to do if message is not a VariantList?
    # Need test at least.
    assert isinstance(message.value, VariantList)

    variant_name = expression.key.name
    return select_from_variant_list(message.value,
                                    env,
                                    variant_name)


@handle.register(CallExpression)
def handle_call_expression(expression, env):
    function_name = expression.callee.name
    try:
        function = env.context._functions[function_name]
    except LookupError:
        env.errors.append(FluentReferenceError("Unknown function: {0}"
                                               .format(function_name)))
        return FluentNone(function_name + "()")

    args = [handle(arg, env) for arg in expression.positional]
    kwargs = {kwarg.name.name: handle(kwarg.value, env) for kwarg in expression.named}
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


@handle.register(Decimal)
def handle_decimal(d, env):
    return fluent_number(d).format(env.context._babel_locale)


@handle.register(FluentDateType)
def handle_fluent_date_type(d, env):
    return d.format(env.context._babel_locale)


@handle.register(date)
def handle_date(d, env):
    return fluent_date(d).format(env.context._babel_locale)


@handle.register(datetime)
def handle_datetime(d, env):
    return fluent_date(d).format(env.context._babel_locale)
