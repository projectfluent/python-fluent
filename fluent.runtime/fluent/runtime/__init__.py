from __future__ import absolute_import, unicode_literals

import babel
import babel.numbers
import babel.plural

from fluent.syntax import FluentParser
from fluent.syntax.ast import Message, Term

from .builtins import BUILTINS
from .prepare import Compiler
from .resolver import ResolverEnvironment, CurrentEnvironment
from .utils import native_to_fluent
from .fallback import FluentLocalization, AbstractResourceLoader, FluentResourceLoader


__all__ = [
    'FluentLocalization',
    'AbstractResourceLoader',
    'FluentResourceLoader',
    'FluentResource',
    'FluentBundle',
]


def FluentResource(source):
    parser = FluentParser()
    return parser.parse(source)


class FluentBundle(object):
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

    def __init__(self, locales, functions=None, use_isolating=True):
        self.locales = locales
        _functions = BUILTINS.copy()
        if functions:
            _functions.update(functions)
        self._functions = _functions
        self.use_isolating = use_isolating
        self._messages = {}
        self._terms = {}
        self._compiled = {}
        self._compiler = Compiler()
        self._babel_locale = self._get_babel_locale()
        self._plural_form = babel.plural.to_python(self._babel_locale.plural_form)

    def add_resource(self, resource, allow_overrides=False):
        # TODO - warn/error about duplicates
        for item in resource.body:
            if not isinstance(item, (Message, Term)):
                continue
            map_ = self._messages if isinstance(item, Message) else self._terms
            full_id = item.id.name
            if full_id not in map_ or allow_overrides:
                map_[full_id] = item

    def has_message(self, message_id):
        return message_id in self._messages

    def get_message(self, message_id):
        return self._lookup(message_id)

    def _lookup(self, entry_id, term=False):
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

    def format_pattern(self, pattern, args=None):
        if args is not None:
            fluent_args = {
                argname: native_to_fluent(argvalue)
                for argname, argvalue in args.items()
            }
        else:
            fluent_args = {}

        errors = []
        env = ResolverEnvironment(context=self,
                                  current=CurrentEnvironment(args=fluent_args),
                                  errors=errors)
        try:
            result = pattern(env)
        except ValueError as e:
            errors.append(e)
            result = '{???}'
        return [result, errors]

    def _get_babel_locale(self):
        for l in self.locales:
            try:
                return babel.Locale.parse(l.replace('-', '_'))
            except babel.UnknownLocaleError:
                continue
        # TODO - log error
        return babel.Locale.default()
