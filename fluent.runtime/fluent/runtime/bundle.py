import babel
import babel.numbers
import babel.plural
from typing import Any, Callable, Dict, List, TYPE_CHECKING, Tuple, Union, cast
from typing_extensions import Literal

from fluent.syntax import ast as FTL

from .builtins import BUILTINS
from .prepare import Compiler
from .resolver import CurrentEnvironment, Message, Pattern, ResolverEnvironment
from .utils import native_to_fluent

if TYPE_CHECKING:
    from .types import FluentNone, FluentType

PluralCategory = Literal['zero', 'one', 'two', 'few', 'many', 'other']


class FluentBundle:
    """
    Bundles are single-language stores of translations.  They are
    aggregate parsed Fluent resources in the Fluent syntax and can
    format translation units (entities) to strings.

    Always use `FluentBundle.get_message` to retrieve translation units from
    a bundle. Generate the localized string by using `format_pattern` on
    `message.value` or `message.attributes['attr']`.
    Translations can contain references to other entities or
    external arguments, conditional logic in form of select expressions, traits
    which describe their grammatical features, and can use Fluent builtins.
    See the documentation of the Fluent syntax for more information.
    """

    def __init__(self,
                 locales: List[str],
                 functions: Union[Dict[str, Callable[[Any], 'FluentType']], None] = None,
                 use_isolating: bool = True):
        self.locales = locales
        self._functions = {**BUILTINS, **(functions or {})}
        self.use_isolating = use_isolating
        self._messages: Dict[str, Union[FTL.Message, FTL.Term]] = {}
        self._terms: Dict[str, Union[FTL.Message, FTL.Term]] = {}
        self._compiled: Dict[str, Message] = {}
        # The compiler is not typed, and this cast is only valid for the public API
        self._compiler = cast(Callable[[Union[FTL.Message, FTL.Term]], Message], Compiler())
        self._babel_locale = self._get_babel_locale()
        self._plural_form = cast(Callable[[Any], Callable[[Union[int, float]], PluralCategory]],
                                 babel.plural.to_python)(self._babel_locale.plural_form)

    def add_resource(self, resource: FTL.Resource, allow_overrides: bool = False) -> None:
        # TODO - warn/error about duplicates
        for item in resource.body:
            if not isinstance(item, (FTL.Message, FTL.Term)):
                continue
            map_ = self._messages if isinstance(item, FTL.Message) else self._terms
            full_id = item.id.name
            if full_id not in map_ or allow_overrides:
                map_[full_id] = item

    def has_message(self, message_id: str) -> bool:
        return message_id in self._messages

    def get_message(self, message_id: str) -> Message:
        return self._lookup(message_id)

    def _lookup(self, entry_id: str, term: bool = False) -> Message:
        if term:
            compiled_id = '-' + entry_id
        else:
            compiled_id = entry_id
        try:
            return self._compiled[compiled_id]
        except LookupError:
            pass
        entry = self._terms[entry_id] if term else self._messages[entry_id]
        self._compiled[compiled_id] = self._compiler(entry)
        return self._compiled[compiled_id]

    def format_pattern(self,
                       pattern: Pattern,
                       args: Union[Dict[str, Any], None] = None
                       ) -> Tuple[Union[str, 'FluentNone'], List[Exception]]:
        if args is not None:
            fluent_args = {
                argname: native_to_fluent(argvalue)
                for argname, argvalue in args.items()
            }
        else:
            fluent_args = {}

        errors: List[Exception] = []
        env = ResolverEnvironment(context=self,
                                  current=CurrentEnvironment(args=fluent_args),
                                  errors=errors)
        try:
            result = pattern(env)
        except ValueError as e:
            errors.append(e)
            result = '{???}'
        return (result, errors)

    def _get_babel_locale(self) -> babel.Locale:
        for lc in self.locales:
            try:
                return babel.Locale.parse(lc.replace('-', '_'))
            except babel.UnknownLocaleError:
                continue
        # TODO - log error
        return babel.Locale.default()
