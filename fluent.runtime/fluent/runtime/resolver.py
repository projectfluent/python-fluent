from __future__ import absolute_import, unicode_literals

import contextlib
from datetime import date, datetime
from decimal import Decimal

import attr
import six

from fluent.syntax import ast as FTL
from .errors import FluentCyclicReferenceError, FluentFormatError, FluentReferenceError
from .types import FluentType, FluentNone, FluentInt, FluentFloat
from .utils import reference_to_id, unknown_reference_error_obj


"""
The classes in this module are used to transform the source
AST to a partially evaluated resolver tree. They're subclasses
to the syntax AST node, and `BaseResolver`. Syntax nodes that
don't require special handling, but have children that need to be
transformed, need to just inherit from their syntax base class and
`BaseResolver`. When adding to the module namespace here, watch
out for naming conflicts with `fluent.syntax.ast`.

`ResolverEnvironment` is the `env` passed to the `__call__` method
in the resolver tree. The `CurrentEnvironment` keeps track of the
modifyable state in the resolver environment.
"""


# Prevent expansion of too long placeables, for memory DOS protection
MAX_PART_LENGTH = 2500


@attr.s
class CurrentEnvironment(object):
    # The parts of ResolverEnvironment that we want to mutate (and restore)
    # temporarily for some parts of a call chain.

    # The values of attributes here must not be mutated, they must only be
    # swapped out for different objects using `modified` (see below).

    # For Messages, VariableReference nodes are interpreted as external args,
    # but for Terms they are the values explicitly passed using CallExpression
    # syntax. So we have to be able to change 'args' for this purpose.
    args = attr.ib()
    # This controls whether we need to report an error if a VariableReference
    # refers to an arg that is not present in the args dict.
    error_for_missing_arg = attr.ib(default=True)


@attr.s
class ResolverEnvironment(object):
    context = attr.ib()
    errors = attr.ib()
    part_count = attr.ib(default=0, init=False)
    active_patterns = attr.ib(factory=set, init=False)
    current = attr.ib(factory=CurrentEnvironment)

    @contextlib.contextmanager
    def modified(self, **replacements):
        """
        Context manager that modifies the 'current' attribute of the
        environment, restoring the old data at the end.
        """
        # CurrentEnvironment only has args that we never mutate, so the shallow
        # copy returned by attr.evolve is fine (at least for now).
        old_current = self.current
        self.current = attr.evolve(old_current, **replacements)
        yield self
        self.current = old_current

    def modified_for_term_reference(self, args=None):
        return self.modified(args=args if args is not None else {},
                             error_for_missing_arg=False)


class BaseResolver(object):
    """
    Abstract base class of all partially evaluated resolvers.

    Subclasses should implement __call__, with a
    ResolverEnvironment as parameter. An exception are wrapper
    classes that don't show up in the evaluation, but need to
    be part of the compiled tree structure.
    """
    def __call__(self, env):
        raise NotImplementedError


class Literal(BaseResolver):
    pass


class Message(FTL.Message, BaseResolver):
    pass


class Term(FTL.Term, BaseResolver):
    pass


class Pattern(FTL.Pattern, BaseResolver):
    # Prevent messages with too many sub parts, for CPI DOS protection
    MAX_PARTS = 1000

    def __init__(self, *args, **kwargs):
        super(Pattern, self).__init__(*args, **kwargs)

    def __call__(self, env):
        if self in env.active_patterns:
            env.errors.append(FluentCyclicReferenceError("Cyclic reference"))
            return FluentNone()
        env.active_patterns.add(self)
        elements = self.elements
        remaining_parts = self.MAX_PARTS - env.part_count
        if len(self.elements) > remaining_parts:
            env.active_patterns.remove(self)
            raise ValueError("Too many parts in message (> {0}), "
                             "aborting.".format(self.MAX_PARTS))
        retval = ''.join(
            resolve(element(env), env) for element in elements
        )
        env.part_count += len(elements)
        env.active_patterns.remove(self)
        return retval


def resolve(fluentish, env):
    if isinstance(fluentish, FluentType):
        return fluentish.format(env.context._babel_locale)
    if isinstance(fluentish, six.string_types):
        if len(fluentish) > MAX_PART_LENGTH:
            raise ValueError(
                "Too many characters in placeable "
                "({}, max allowed is {})".format(len(fluentish), Pattern.MAX_PARTS)
            )
    return fluentish


class TextElement(FTL.TextElement, Literal):
    def __call__(self, env):
        return self.value


class Placeable(FTL.Placeable, BaseResolver):
    def __call__(self, env):
        inner = resolve(self.expression(env), env)
        if not env.context.use_isolating:
            return inner
        return "\u2068" + inner + "\u2069"


class NeverIsolatingPlaceable(FTL.Placeable, BaseResolver):
    def __call__(self, env):
        inner = resolve(self.expression(env), env)
        return inner


class StringLiteral(FTL.StringLiteral, Literal):
    def __call__(self, env):
        return self.parse()['value']


class NumberLiteral(FTL.NumberLiteral, BaseResolver):
    def __init__(self, value, **kwargs):
        super(NumberLiteral, self).__init__(value, **kwargs)
        if '.' in self.value:
            self.value = FluentFloat(self.value)
        else:
            self.value = FluentInt(self.value)

    def __call__(self, env):
        return self.value


class MessageReference(FTL.MessageReference, BaseResolver):
    def __call__(self, env):
        return lookup_reference(self, env)(env)


class TermReference(FTL.TermReference, BaseResolver):
    def __call__(self, env):
        if self.arguments:
            if self.arguments.positional:
                env.errors.append(FluentFormatError("Ignored positional arguments passed to term '{0}'"
                                                    .format(reference_to_id(self))))
            kwargs = {kwarg.name.name: kwarg.value(env) for kwarg in self.arguments.named}
        else:
            kwargs = None
        with env.modified_for_term_reference(args=kwargs):
            return lookup_reference(self, env)(env)


class FluentNoneResolver(FluentNone, BaseResolver):
    def __call__(self, env):
        return self.format(env.context._babel_locale)


def lookup_reference(ref, env):
    """
    Given a MessageReference, TermReference or AttributeExpression, returns the
    AST node, or FluentNone if not found, including fallback logic
    """
    ref_id = reference_to_id(ref)
    try:
        return env.context.lookup(ref_id)
    except LookupError:
        env.errors.append(unknown_reference_error_obj(ref_id))

        if ref.attribute:
            # Fallback
            parent_id = reference_to_id(ref, ignore_attributes=True)
            try:
                return env.context.lookup(parent_id)
            except LookupError:
                # Don't add error here, because we already added error for the
                # actual thing we were looking for.
                pass

    return FluentNoneResolver(ref_id)


class VariableReference(FTL.VariableReference, BaseResolver):
    def __call__(self, env):
        name = self.id.name
        try:
            arg_val = env.current.args[name]
        except LookupError:
            if env.current.error_for_missing_arg:
                env.errors.append(
                    FluentReferenceError("Unknown external: {0}".format(name)))
            return FluentNoneResolver(name)

        if isinstance(arg_val, (FluentType, six.text_type)):
            return arg_val
        env.errors.append(TypeError("Unsupported external type: {0}, {1}"
                                    .format(name, type(arg_val))))
        return FluentNone(name)


class Attribute(FTL.Attribute, BaseResolver):
    pass


class SelectExpression(FTL.SelectExpression, BaseResolver):
    def __call__(self, env):
        key = self.selector(env)
        return self.select_from_select_expression(env, key=key)

    def select_from_select_expression(self, env, key):
        default = None
        found = None
        for variant in self.variants:
            if variant.default:
                default = variant

            if match(key, variant.key(env), env):
                found = variant
                break

        if found is None:
            found = default
        return found.value(env)


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
    elif is_number(val2):
        return match(val2, val1, env)

    return val1 == val2


class Variant(FTL.Variant, BaseResolver):
    pass


class Identifier(FTL.Identifier, BaseResolver):
    def __call__(self, env):
        return self.name


class CallArguments(FTL.CallArguments, BaseResolver):
    pass


class FunctionReference(FTL.FunctionReference, BaseResolver):
    def __call__(self, env):
        args = [arg(env) for arg in self.arguments.positional]
        kwargs = {kwarg.name.name: kwarg.value(env) for kwarg in self.arguments.named}
        function_name = self.id.name
        try:
            function = env.context._functions[function_name]
        except LookupError:
            env.errors.append(FluentReferenceError("Unknown function: {0}"
                                                   .format(function_name)))
            return FluentNone(function_name + "()")

        try:
            return function(*args, **kwargs)
        except Exception as e:
            env.errors.append(e)
            return FluentNoneResolver(function_name + "()")


class NamedArgument(FTL.NamedArgument, BaseResolver):
    pass
