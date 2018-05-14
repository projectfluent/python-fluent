from __future__ import absolute_import, unicode_literals

import six

from .resolver import resolve
from .syntax import FluentParser
from .syntax.ast import Message, Term


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
        self.functions = functions or {}
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

    def format(self, message_id, args):
        message = self._get_message(message_id)
        errors = []
        resolved = resolve(self, args, message, errors=errors)
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
