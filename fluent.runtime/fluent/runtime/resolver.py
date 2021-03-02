from __future__ import absolute_import, unicode_literals

import contextlib

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

    def to_type(self, env):
        """
        Resolve this to a FluentType.

        For simple resolvers of one part, this retains the type of that part.
        For multi-part resolvers, format each part to a string and concat
        the formatted parts.
        """
        parts = list(self(env))
        if len(parts) == 1:
            return parts[0]
        return ''.join(env.context.format_part(part) for part in parts)


class Literal(BaseResolver):
    pass


class EntryResolver(BaseResolver):
    '''Entries (Messages and Terms) have attributes.
    In the AST they're a list, the resolver wants a dict. The helper method
    here should be called from the constructor.
    '''
    def _fix_attributes(self):
        self.attributes = {
            attr.id.name: attr.value
            for attr in self.attributes
        }


class Message(FTL.Message, EntryResolver):
    def __init__(self, id, **kwargs):
        super(Message, self).__init__(id, **kwargs)
        self._fix_attributes()


class Term(FTL.Term, EntryResolver):
    def __init__(self, id, value, **kwargs):
        super(Term, self).__init__(id, value, **kwargs)
        self._fix_attributes()


class Pattern(FTL.Pattern, BaseResolver):
    # Prevent messages with too many sub parts, for CPI DOS protection
    MAX_PARTS = 1000

    def __init__(self, *args, **kwargs):
        super(Pattern, self).__init__(*args, **kwargs)

    def __call__(self, env):
        if self in env.active_patterns:
            env.errors.append(FluentCyclicReferenceError("Cyclic reference"))
            yield FluentNone()
            return
        env.active_patterns.add(self)
        for element in self.elements:
            for part in element(env):
                yield part
                env.part_count += 1
                if env.part_count > self.MAX_PARTS:
                    raise ValueError("Too many parts in message (> {0}), "
                                     "aborting.".format(self.MAX_PARTS))
        env.active_patterns.remove(self)


class TextElement(FTL.TextElement, Literal):
    def __call__(self, env):
        yield self.value


class NeverIsolatingPlaceable(FTL.Placeable, BaseResolver):
    def __call__(self, env):
        for part in self.expression(env):
            yield part


class Placeable(NeverIsolatingPlaceable):
    def __call__(self, env):
        if env.context.use_isolating:
            yield "\u2068"
        for part in self.expression(env):
            yield part
        if env.context.use_isolating:
            yield "\u2069"


class StringLiteral(FTL.StringLiteral, Literal):
    def __call__(self, env):
        yield self.parse()['value']


class NumberLiteral(FTL.NumberLiteral, BaseResolver):
    def __init__(self, value, **kwargs):
        super(NumberLiteral, self).__init__(value, **kwargs)
        if '.' in self.value:
            self.value = FluentFloat(self.value)
        else:
            self.value = FluentInt(self.value)

    def __call__(self, env):
        yield self.value


class EntryReference(BaseResolver):
    def __call__(self, env):
        try:
            entry = env.context._lookup(self.id.name, term=isinstance(self, FTL.TermReference))
            if self.attribute:
                pattern = entry.attributes[self.attribute.name]
            else:
                pattern = entry.value
            for part in pattern(env):
                yield part
        except LookupError:
            ref_id = reference_to_id(self)
            env.errors.append(unknown_reference_error_obj(ref_id))
            yield FluentNone('{{{}}}'.format(ref_id))


class MessageReference(FTL.MessageReference, EntryReference):
    pass


class TermReference(FTL.TermReference, EntryReference):
    def __call__(self, env):
        if self.arguments:
            if self.arguments.positional:
                env.errors.append(FluentFormatError("Ignored positional arguments passed to term '{0}'"
                                                    .format(reference_to_id(self))))
            kwargs = {kwarg.name.name: kwarg.value.to_type(env) for kwarg in self.arguments.named}
        else:
            kwargs = None
        with env.modified_for_term_reference(args=kwargs):
            for part in super(TermReference, self).__call__(env):
                yield part


class VariableReference(FTL.VariableReference, BaseResolver):
    def __call__(self, env):
        name = self.id.name
        try:
            arg_val = env.current.args[name]
        except LookupError:
            if env.current.error_for_missing_arg:
                env.errors.append(
                    FluentReferenceError("Unknown external: {0}".format(name)))
            yield FluentNone(name)
            return

        if isinstance(arg_val, (FluentType, six.text_type)):
            yield arg_val
        else:
            env.errors.append(TypeError(
                "Unsupported external type: {0}, {1}".format(name, type(arg_val))
            ))
            yield FluentNone(name)


class Attribute(FTL.Attribute, BaseResolver):
    pass


class SelectExpression(FTL.SelectExpression, BaseResolver):
    def __call__(self, env):
        key = self.selector.to_type(env)
        for part in self.select_from_select_expression(env, key=key):
            yield part

    def select_from_select_expression(self, env, key):
        default = None
        found = None
        for variant in self.variants:
            if variant.default:
                default = variant

            if match(key, variant.key, env):
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
    def __init__(self, key, value, default=False, **kwargs):
        key = key.to_type(None)
        super(Variant, self).__init__(key, value, default=default, **kwargs)


class Identifier(FTL.Identifier, BaseResolver):
    def __call__(self, env):
        yield self.name


class CallArguments(FTL.CallArguments, BaseResolver):
    pass


class FunctionReference(FTL.FunctionReference, BaseResolver):
    def __call__(self, env):
        args = [arg.to_type(env) for arg in self.arguments.positional]
        kwargs = {kwarg.name.name: kwarg.value.to_type(env) for kwarg in self.arguments.named}
        function_name = self.id.name
        try:
            function = env.context._functions[function_name]
        except LookupError:
            env.errors.append(FluentReferenceError("Unknown function: {0}"
                                                   .format(function_name)))
            yield FluentNone(function_name + "()")
            return

        try:
            yield function(*args, **kwargs)
        except Exception as e:
            env.errors.append(e)
            yield FluentNone(function_name + "()")


class NamedArgument(FTL.NamedArgument, BaseResolver):
    pass
