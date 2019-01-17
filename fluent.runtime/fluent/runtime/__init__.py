from __future__ import absolute_import, unicode_literals

import babel
import babel.numbers
import babel.plural

from fluent.syntax import FluentParser
from fluent.syntax.ast import Message, Term

from .builtins import BUILTINS
from .resolver import resolve


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
        self._babel_locale = self._get_babel_locale()
        self._plural_form = babel.plural.to_python(self._babel_locale.plural_form)

    def add_messages(self, source):
        parser = FluentParser()
        resource = parser.parse(source)
        # TODO - warn/error about duplicates
        for item in resource.body:
            if isinstance(item, (Message, Term)):
                if item.id.name not in self._messages_and_terms:
                    self._messages_and_terms[item.id.name] = item

    def has_message(self, message_id):
        if message_id.startswith('-'):
            return False
        return message_id in self._messages_and_terms

    def format(self, message_id, args=None):
        message = self._get_message(message_id)
        if args is None:
            args = {}
        return resolve(self, message, args)

    def _get_message(self, message_id):
        if message_id.startswith('-'):
            raise LookupError(message_id)
        if '.' in message_id:
            name, attr_name = message_id.split('.', 1)
            msg = self._messages_and_terms[name]
            for attribute in msg.attributes:
                if attribute.id.name == attr_name:
                    return attribute.value
            raise LookupError(message_id)
        else:
            return self._messages_and_terms[message_id]

    def _get_babel_locale(self):
        for l in self.locales:
            try:
                return babel.Locale.parse(l.replace('-', '_'))
            except babel.UnknownLocaleError:
                continue
        # TODO - log error
        return babel.Locale.default()
