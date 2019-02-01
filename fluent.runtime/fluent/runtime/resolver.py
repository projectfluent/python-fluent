from __future__ import absolute_import, unicode_literals

import contextlib

import attr
import six

from fluent.syntax import ast as FTL

from .errors import FluentCyclicReferenceError, FluentFormatError, FluentReferenceError
from .types import FluentFloat, FluentInt, FluentNone, FluentType
from .utils import args_match, inspect_function_args, reference_to_id, unknown_reference_error_obj

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
    part_count = attr.ib(default=0)
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
        self.dirty = False

    def __call__(self, env):
        if self.dirty:
            env.errors.append(FluentCyclicReferenceError("Cyclic reference"))
            return FluentNone()
        if env.part_count > self.MAX_PARTS:
            return ""
        self.dirty = True
        elements = self.elements
        remaining_parts = self.MAX_PARTS - env.part_count
        if len(self.elements) > remaining_parts:
            elements = elements[:remaining_parts + 1]
            env.errors.append(ValueError("Too many parts in message (> {0}), "
                                         "aborting.".format(self.MAX_PARTS)))
        retval = ''.join(
            resolve(element(env), env) for element in elements
        )
        env.part_count += len(elements)
        self.dirty = False
        return retval


def resolve(fluentish, env):
    if isinstance(fluentish, FluentType):
        return fluentish.format(env.context._babel_locale)
    if isinstance(fluentish, six.string_types):
        if len(fluentish) > MAX_PART_LENGTH:
            return fluentish[:MAX_PART_LENGTH]
    return fluentish


class TextElement(FTL.TextElement, Literal):
    def __call__(self, env):
        return self.value


class Placeable(FTL.Placeable, BaseResolver):
    def __call__(self, env):
        return self.expression(env)


class IsolatingPlaceable(FTL.Placeable, BaseResolver):
    def __call__(self, env):
        inner = self.expression(env)
        return "\u2068" + resolve(inner, env) + "\u2069"


class StringLiteral(FTL.StringLiteral, Literal):
    def __call__(self, env):
        return self.value


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
        with env.modified_for_term_reference():
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

        if isinstance(ref, AttributeExpression):
            # Fallback
            parent_id = reference_to_id(ref.ref)
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


class AttributeExpression(FTL.AttributeExpression, BaseResolver):
    def __call__(self, env):
        return lookup_reference(self, env)(env)


class Attribute(FTL.Attribute, BaseResolver):
    pass


class VariantList(FTL.VariantList, BaseResolver):
    def __call__(self, env, key=None):
        found = None
        for variant in self.variants:
            if variant.default:
                default = variant
                if key is None:
                    # We only want the default
                    break

            compare_value = variant.key(env)
            if match(key, compare_value, env):
                found = variant
                break

        if found is None:
            if (key is not None and not isinstance(key, FluentNone)):
                env.errors.append(FluentReferenceError("Unknown variant: {0}"
                                                       .format(key)))
            found = default
        assert found, "Not having a default variant is a parse error"

        return found.value(env)


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


class VariantExpression(FTL.VariantExpression, BaseResolver):
    def __call__(self, env):
        message = lookup_reference(self.ref, env)

        # TODO What to do if message is not a VariantList?
        # Need test at least.
        assert isinstance(message, VariantList), "Found unexpected {!r}".format(message)

        variant_name = self.key.name
        return message(env, variant_name)


class CallExpression(FTL.CallExpression, BaseResolver):
    def __call__(self, env):
        args = [arg(env) for arg in self.positional]
        kwargs = {kwarg.name.name: kwarg.value(env) for kwarg in self.named}

        if isinstance(self.callee, (TermReference, AttributeExpression)):
            term = lookup_reference(self.callee, env)
            if args:
                env.errors.append(FluentFormatError("Ignored positional arguments passed to term '{0}'"
                                                    .format(reference_to_id(self.callee))))
            with env.modified_for_term_reference(args=kwargs):
                return term(env)

        # builtin or custom function call
        function_name = self.callee.id.name
        try:
            function = env.context._functions[function_name]
        except LookupError:
            env.errors.append(FluentReferenceError("Unknown function: {0}"
                                                   .format(function_name)))
            return FluentNone(function_name + "()")

        arg_spec = inspect_function_args(function, function_name, env.errors)
        match, sanitized_args, sanitized_kwargs, errors = args_match(function_name, args, kwargs, arg_spec)
        env.errors.extend(errors)
        if match:
            return function(*sanitized_args, **sanitized_kwargs)
        return FluentNone(function_name + "()")


class NamedArgument(FTL.NamedArgument, BaseResolver):
    pass
