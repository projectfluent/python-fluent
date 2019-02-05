from __future__ import absolute_import, unicode_literals

import babel
import babel.numbers
import babel.plural

from fluent.syntax import FluentParser
from fluent.syntax.ast import Message, Term

from .builtins import BUILTINS
from .prepare import Compiler
from .resolver import ResolverEnvironment, CurrentEnvironment
from .utils import ATTRIBUTE_SEPARATOR, TERM_SIGIL, add_message_and_attrs_to_store, ast_to_id


class FluentBundle(object):
    """
    Message contexts are single-language stores of translations.  They are
    responsible for parsing translation resources in the Fluent syntax and can
    format translation units (entities) to strings.

    Always use `FluentBundle.format` to retrieve translation units from
    a context.  Translations can contain references to other entities or
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
        self._use_isolating = use_isolating
        self._messages_and_terms = {}
        self._compiled = {}
        self._compiler = Compiler(use_isolating=use_isolating)
        self._babel_locale = self._get_babel_locale()
        self._plural_form = babel.plural.to_python(self._babel_locale.plural_form)

    def add_messages(self, source):
        parser = FluentParser()
        resource = parser.parse(source)
        # TODO - warn/error about duplicates
        for item in resource.body:
            if isinstance(item, (Message, Term)):
                full_id = ast_to_id(item)
                if full_id not in self._messages_and_terms:
                    # We add attributes to the store to enable faster looker
                    # later, and more direct code in some instances.
                    add_message_and_attrs_to_store(self._messages_and_terms, full_id, item)

    def has_message(self, message_id):
        if message_id.startswith(TERM_SIGIL) or ATTRIBUTE_SEPARATOR in message_id:
            return False
        return message_id in self._messages_and_terms

    def lookup(self, full_id):
        if full_id not in self._compiled:
            message = self._messages_and_terms[full_id]
            self._compiled[full_id] = self._compiler(message.value)
        return self._compiled[full_id]

    def format(self, message_id, args=None):
        if message_id.startswith(TERM_SIGIL):
            raise LookupError(message_id)
        if args is None:
            args = {}
        errors = []
        resolve = self.lookup(message_id)
        env = ResolverEnvironment(context=self,
                                  current=CurrentEnvironment(args=args),
                                  errors=errors)
        return [resolve(env), errors]

    def _get_babel_locale(self):
        for l in self.locales:
            try:
                return babel.Locale.parse(l.replace('-', '_'))
            except babel.UnknownLocaleError:
                continue
        # TODO - log error
        return babel.Locale.default()
