from __future__ import absolute_import, unicode_literals

from collections import OrderedDict

import babel
import babel.numbers
import babel.plural

from fluent.syntax import FluentParser
from fluent.syntax.ast import Junk, Message, Term

from .builtins import BUILTINS
from .compiler import compile_messages
from .errors import FluentDuplicateMessageId, FluentJunkFound
from .prepare import Compiler
from .resolver import CurrentEnvironment, ResolverEnvironment
from .utils import ATTRIBUTE_SEPARATOR, TERM_SIGIL, ast_to_id, native_to_fluent


class FluentBundleBase(object):
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
        self._messages_and_terms = OrderedDict()
        self._parsing_issues = []
        self._babel_locale = self._get_babel_locale()
        self._plural_form = babel.plural.to_python(self._babel_locale.plural_form)

    def add_messages(self, source):
        parser = FluentParser()
        resource = parser.parse(source)
        for item in resource.body:
            if isinstance(item, (Message, Term)):
                full_id = ast_to_id(item)
                if full_id in self._messages_and_terms:
                    self._parsing_issues.append((full_id, FluentDuplicateMessageId(
                        "Additional definition for '{0}' discarded.".format(full_id))))
                else:
                    self._messages_and_terms[full_id] = item
            elif isinstance(item, Junk):
                self._parsing_issues.append(
                    (None, FluentJunkFound("Junk found: " +
                                           '; '.join(a.message for a in item.annotations),
                                           item.annotations)))

    def has_message(self, message_id):
        if message_id.startswith(TERM_SIGIL) or ATTRIBUTE_SEPARATOR in message_id:
            return False
        return message_id in self._messages_and_terms

    def _get_babel_locale(self):
        for l in self.locales:
            try:
                return babel.Locale.parse(l.replace('-', '_'))
            except babel.UnknownLocaleError:
                continue
        # TODO - log error
        return babel.Locale.default()

    def format(self, message_id, args=None):
        raise NotImplementedError()

    def check_messages(self):
        """
        Check messages for errors and return as a list of two tuples:
           (message ID or None, exception object)
        """
        raise NotImplementedError()


class InterpretingFluentBundle(FluentBundleBase):

    def __init__(self, locales, functions=None, use_isolating=True):
        super(InterpretingFluentBundle, self).__init__(locales, functions=functions, use_isolating=use_isolating)
        self._compiled = {}
        self._compiler = Compiler(use_isolating=use_isolating)

    def lookup(self, full_id):
        if full_id not in self._compiled:
            entry_id = full_id.split(ATTRIBUTE_SEPARATOR, 1)[0]
            entry = self._messages_and_terms[entry_id]
            compiled = self._compiler(entry)
            if compiled.value is not None:
                self._compiled[entry_id] = compiled.value
            for attr in compiled.attributes:
                self._compiled[ATTRIBUTE_SEPARATOR.join([entry_id, attr.id.name])] = attr.value
        return self._compiled[full_id]

    def format(self, message_id, args=None):
        if message_id.startswith(TERM_SIGIL):
            raise LookupError(message_id)
        if args is not None:
            fluent_args = {
                argname: native_to_fluent(argvalue)
                for argname, argvalue in args.items()
            }
        else:
            fluent_args = {}

        errors = []
        resolve = self.lookup(message_id)
        env = ResolverEnvironment(context=self,
                                  current=CurrentEnvironment(args=fluent_args),
                                  errors=errors)
        return [resolve(env), errors]

    def check_messages(self):
        return self._parsing_issues[:]


class CompilingFluentBundle(FluentBundleBase):
    def __init__(self, *args, **kwargs):
        super(CompilingFluentBundle, self).__init__(*args, **kwargs)
        self._mark_dirty()

    def _mark_dirty(self):
        self._is_dirty = True
        # Clear out old compilation errors, they might not apply if we
        # re-compile:
        self._compilation_errors = []
        self.format = self._compile_and_format

    def _mark_clean(self):
        self._is_dirty = False
        self.format = self._format

    def add_messages(self, source):
        super(CompilingFluentBundle, self).add_messages(source)
        self._mark_dirty()

    def _compile(self):
        self._compiled_messages, self._compilation_errors = compile_messages(
            self._messages_and_terms,
            self._babel_locale,
            use_isolating=self._use_isolating,
            functions=self._functions)
        self._mark_clean()

    # 'format' is the hot path for many scenarios, so we try to optimize it. To
    # avoid having to check '_is_dirty' inside 'format', we switch 'format' from
    # '_compile_and_format' to '_format' when compilation is done. This gives us
    # about 10% improvement for the simplest (but most common) case of an
    # entirely static string.
    def _compile_and_format(self, message_id, args=None):
        self._compile()
        return self._format(message_id, args)

    def _format(self, message_id, args=None):
        errors = []
        return self._compiled_messages[message_id](args, errors), errors

    def check_messages(self):
        if self._is_dirty:
            self._compile()
        return self._parsing_issues + self._compilation_errors


FluentBundle = InterpretingFluentBundle
