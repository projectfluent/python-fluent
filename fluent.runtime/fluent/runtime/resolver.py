import attr
import contextlib
from typing import Any, Dict, Generator, List, Set, TYPE_CHECKING, Union, cast

from fluent.syntax import ast as FTL
from .errors import FluentCyclicReferenceError, FluentFormatError, FluentReferenceError
from .types import FluentType, FluentNone, FluentInt, FluentFloat
from .utils import reference_to_id, unknown_reference_error_obj

if TYPE_CHECKING:
    from .bundle import FluentBundle


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
class CurrentEnvironment:
    # The parts of ResolverEnvironment that we want to mutate (and restore)
    # temporarily for some parts of a call chain.

    # The values of attributes here must not be mutated, they must only be
    # swapped out for different objects using `modified` (see below).

    # For Messages, VariableReference nodes are interpreted as external args,
    # but for Terms they are the values explicitly passed using CallExpression
    # syntax. So we have to be able to change 'args' for this purpose.
    args: Dict[str, Any] = attr.ib(factory=dict)
    # This controls whether we need to report an error if a VariableReference
    # refers to an arg that is not present in the args dict.
    error_for_missing_arg: bool = attr.ib(default=True)


@attr.s
class ResolverEnvironment:
    context: 'FluentBundle' = attr.ib()
    errors: List[Exception] = attr.ib()
    part_count: int = attr.ib(default=0, init=False)
    active_patterns: Set[FTL.Pattern] = attr.ib(factory=set, init=False)
    current: CurrentEnvironment = attr.ib(factory=CurrentEnvironment)

    @contextlib.contextmanager
    def modified(self, **replacements: Any) -> Generator['ResolverEnvironment', None, None]:
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

    def modified_for_term_reference(self, args: Union[Dict[str, Any], None] = None) -> Any:
        return self.modified(args=args if args is not None else {},
                             error_for_missing_arg=False)


class BaseResolver:
    """
    Abstract base class of all partially evaluated resolvers.

    Subclasses should implement __call__, with a
    ResolverEnvironment as parameter. An exception are wrapper
    classes that don't show up in the evaluation, but need to
    be part of the compiled tree structure.
    """

    def __call__(self, env: ResolverEnvironment) -> Any:
        raise NotImplementedError


class Literal(BaseResolver):
    value: str


class Message(FTL.Entry, BaseResolver):
    id: 'Identifier'
    value: Union['Pattern', None]
    attributes: Dict[str, 'Pattern']

    def __init__(self,
                 id: 'Identifier',
                 value: Union['Pattern', None] = None,
                 attributes: Union[List['Attribute'], None] = None,
                 comment: Any = None,
                 **kwargs: Any):
        super().__init__(**kwargs)
        self.id = id
        self.value = value
        self.attributes = {attr.id.name: attr.value for attr in attributes} if attributes else {}


class Term(FTL.Entry, BaseResolver):
    id: 'Identifier'
    value: 'Pattern'
    attributes: Dict[str, 'Pattern']

    def __init__(self,
                 id: 'Identifier',
                 value: 'Pattern',
                 attributes: Union[List['Attribute'], None] = None,
                 comment: Any = None,
                 **kwargs: Any):
        super().__init__(**kwargs)
        self.id = id
        self.value = value
        self.attributes = {attr.id.name: attr.value for attr in attributes} if attributes else {}


class Pattern(FTL.Pattern, BaseResolver):
    # Prevent messages with too many sub parts, for CPI DOS protection
    MAX_PARTS = 1000

    elements: List[Union['TextElement', 'Placeable']]  # type: ignore

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)

    def __call__(self, env: ResolverEnvironment) -> Union[str, FluentNone]:
        if self in env.active_patterns:
            env.errors.append(FluentCyclicReferenceError("Cyclic reference"))
            return FluentNone()
        env.active_patterns.add(self)
        elements = self.elements
        remaining_parts = self.MAX_PARTS - env.part_count
        if len(self.elements) > remaining_parts:
            env.active_patterns.remove(self)
            raise ValueError("Too many parts in message (> {}), "
                             "aborting.".format(self.MAX_PARTS))
        retval = ''.join(
            resolve(element(env), env) for element in elements
        )
        env.part_count += len(elements)
        env.active_patterns.remove(self)
        return retval


def resolve(fluentish: Any, env: ResolverEnvironment) -> Any:
    if isinstance(fluentish, FluentType):
        return fluentish.format(env.context._babel_locale)
    if isinstance(fluentish, str):
        if len(fluentish) > MAX_PART_LENGTH:
            raise ValueError(
                "Too many characters in placeable "
                "({}, max allowed is {})".format(len(fluentish), Pattern.MAX_PARTS)
            )
    return fluentish


class TextElement(FTL.TextElement, Literal):
    value: str

    def __call__(self, env: ResolverEnvironment) -> str:
        return self.value


class Placeable(FTL.Placeable, BaseResolver):
    expression: Union['InlineExpression', 'Placeable', 'SelectExpression']

    def __call__(self, env: ResolverEnvironment) -> Any:
        inner = resolve(self.expression(env), env)
        if not env.context.use_isolating:
            return inner
        return "\u2068" + inner + "\u2069"


class NeverIsolatingPlaceable(FTL.Placeable, BaseResolver):
    expression: Union['InlineExpression', Placeable, 'SelectExpression']

    def __call__(self, env: ResolverEnvironment) -> Any:
        inner = resolve(self.expression(env), env)
        return inner


class StringLiteral(FTL.StringLiteral, Literal):
    value: str

    def __call__(self, env: ResolverEnvironment) -> str:
        return self.parse()['value']


class NumberLiteral(FTL.NumberLiteral, BaseResolver):
    value: Union[FluentFloat, FluentInt]  # type: ignore

    def __init__(self, value: str, **kwargs: Any):
        super().__init__(value, **kwargs)
        if '.' in cast(str, self.value):
            self.value = FluentFloat(self.value)
        else:
            self.value = FluentInt(self.value)

    def __call__(self, env: ResolverEnvironment) -> Union[FluentFloat, FluentInt]:
        return self.value


def resolveEntryReference(
        ref: Union['MessageReference', 'TermReference'],
        env: ResolverEnvironment
) -> Union[str, FluentNone]:
    try:
        entry = env.context._lookup(ref.id.name, term=isinstance(ref, FTL.TermReference))
        pattern: Pattern
        if ref.attribute:
            pattern = entry.attributes[ref.attribute.name]
        else:
            pattern = entry.value  # type: ignore
        return pattern(env)
    except LookupError:
        ref_id = reference_to_id(ref)
        env.errors.append(unknown_reference_error_obj(ref_id))
        return FluentNone(f'{{{ref_id}}}')
    except TypeError:
        ref_id = reference_to_id(ref)
        env.errors.append(FluentReferenceError(f"No pattern: {ref_id}"))
        return FluentNone(ref_id)


class MessageReference(FTL.MessageReference, BaseResolver):
    id: 'Identifier'
    attribute: Union['Identifier', None]

    def __call__(self, env: ResolverEnvironment) -> Union[str, FluentNone]:
        return resolveEntryReference(self, env)


class TermReference(FTL.TermReference, BaseResolver):
    id: 'Identifier'
    attribute: Union['Identifier', None]
    arguments: Union['CallArguments', None]

    def __call__(self, env: ResolverEnvironment) -> Union[str, FluentNone]:
        if self.arguments:
            if self.arguments.positional:
                env.errors.append(FluentFormatError("Ignored positional arguments passed to term '{}'"
                                                    .format(reference_to_id(self))))
            kwargs = {kwarg.name.name: kwarg.value(env) for kwarg in self.arguments.named}
        else:
            kwargs = None
        with env.modified_for_term_reference(args=kwargs):
            return resolveEntryReference(self, env)


class VariableReference(FTL.VariableReference, BaseResolver):
    id: 'Identifier'

    def __call__(self, env: ResolverEnvironment) -> Any:
        name = self.id.name
        try:
            arg_val = env.current.args[name]
        except LookupError:
            if env.current.error_for_missing_arg:
                env.errors.append(
                    FluentReferenceError(f"Unknown external: {name}"))
            return FluentNone(name)

        if isinstance(arg_val, (FluentType, str)):
            return arg_val
        env.errors.append(TypeError("Unsupported external type: {}, {}"
                                    .format(name, type(arg_val))))
        return FluentNone(name)


class Attribute(FTL.Attribute, BaseResolver):
    id: 'Identifier'
    value: Pattern


class SelectExpression(FTL.SelectExpression, BaseResolver):
    selector: 'InlineExpression'
    variants: List['Variant']  # type: ignore

    def __call__(self, env: ResolverEnvironment) -> Union[str, FluentNone]:
        key = self.selector(env)
        default: Union['Variant', None] = None
        found: Union['Variant', None] = None
        for variant in self.variants:
            if variant.default:
                default = variant

            if match(key, variant.key(env), env):
                found = variant
                break

        if found is None:
            if default is None:
                env.errors.append(FluentFormatError("No default"))
                return FluentNone()
            found = default
        return found.value(env)


def is_number(val: Any) -> bool:
    return isinstance(val, (int, float))


def match(val1: Any, val2: Any, env: ResolverEnvironment) -> bool:
    if val1 is None or isinstance(val1, FluentNone):
        return False
    if val2 is None or isinstance(val2, FluentNone):
        return False
    if is_number(val1):
        if not is_number(val2):
            # Could be plural rule match
            return cast(bool, env.context._plural_form(val1) == val2)
    elif is_number(val2):
        return match(val2, val1, env)

    return cast(bool, val1 == val2)


class Variant(FTL.Variant, BaseResolver):
    key: Union['Identifier', NumberLiteral]
    value: Pattern
    default: bool


class Identifier(FTL.Identifier, BaseResolver):
    name: str

    def __call__(self, env: ResolverEnvironment) -> str:
        return self.name


class CallArguments(FTL.CallArguments, BaseResolver):
    positional: List[Union['InlineExpression', Placeable]]  # type: ignore
    named: List['NamedArgument']  # type: ignore


class FunctionReference(FTL.FunctionReference, BaseResolver):
    id: Identifier
    arguments: CallArguments

    def __call__(self, env: ResolverEnvironment) -> Any:
        args = [arg(env) for arg in self.arguments.positional]
        kwargs = {kwarg.name.name: kwarg.value(env) for kwarg in self.arguments.named}
        function_name = self.id.name
        try:
            function = env.context._functions[function_name]
        except LookupError:
            env.errors.append(FluentReferenceError("Unknown function: {}"
                                                   .format(function_name)))
            return FluentNone(function_name + "()")

        try:
            return function(*args, **kwargs)
        except Exception as e:
            env.errors.append(e)
            return FluentNone(function_name + "()")


class NamedArgument(FTL.NamedArgument, BaseResolver):
    name: Identifier
    value: Union[NumberLiteral, StringLiteral]


InlineExpression = Union[NumberLiteral, StringLiteral, MessageReference,
                         TermReference, VariableReference, FunctionReference]
