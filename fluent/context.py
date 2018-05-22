from __future__ import absolute_import, unicode_literals

import babel
import babel.numbers
import babel.plural
import six

from .builtins import BUILTINS
from .resolver import resolve
from .syntax import FluentParser
from .syntax.ast import Message, Term
from .utils import cachedproperty


class MessageContext(object):
    """
    Message contexts are single-language stores of translations.  They are
    responsible for parsing translation resources in the Fluent syntax and can
    format translation units (entities) to strings.

    Always use `MessageContext.format` to retrieve translation units from
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
        self.functions = _functions
        self._use_isolating = use_isolating
        self._messages = {}
        self._terms = {}

    def add_messages(self, source):
        parser = FluentParser()
        resource = parser.parse(source)
        # TODO - warn if items get overwritten
        for item in resource.body:
            if isinstance(item, Message):
                self._messages[item.id.name] = item
            elif isinstance(item, Term):
                self._terms[item.id.name] = item

    def has_message(self, message_id):
        try:
            self._get_message(message_id)
            return True
        except LookupError:
            return False

    def message_ids(self):
        """
        Returns iterable of the message ids of the messages in this context
        """
        return six.iterkeys(self._messages)

    def format(self, message_id, args=None):
        message = self._get_message(message_id)
        if args is None:
            args = {}
        errors = []
        resolved = resolve(self, message, args, errors=errors)
        return resolved, errors

    def _get_message(self, message_id):
        if '.' in message_id:
            name, attr_name = message_id.split('.', 1)
            msg = self._messages[name]
            for attribute in msg.attributes:
                if attribute.id.name == attr_name:
                    return attribute.value
            raise LookupError(message_id)
        else:
            return self._messages[message_id]

    @cachedproperty
    def plural_form_for_number(self):
        """
        Get the CLDR category for a given number.

        >>> ctx = MessageContext(['en-US'])
        >>> ctx.plural_form_for_number(1)
        'one'
        """
        return babel.plural.to_python(self._babel_locale.plural_form)

    @cachedproperty
    def _babel_locale(self):
        for l in self.locales:
            try:
                return babel.Locale.parse(l.replace('-', '_'))
            except babel.UnknownLocaleError:
                continue
        # TODO - log error
        return babel.Locale.default()
