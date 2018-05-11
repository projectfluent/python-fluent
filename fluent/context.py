from __future__ import absolute_import, unicode_literals

import six

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
        self._functions = functions or {}
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
        return message_id in self._messages

    def messages(self):
        """
        Returns iterable of (id, message) for the messages in this context
        """
        return six.iteritems(self._messages)
