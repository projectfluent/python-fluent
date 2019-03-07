from __future__ import absolute_import, unicode_literals

import six

from . import codegen
from .utils import SimpleNamespace


def identity(value):
    """
    Identity function.
    The function is also used as a sentinel value by the
    compiler for it to detect a no-op
    """
    return value


# Default string join function and sentinel value
default_join = ''.join


def select_always(message_id=None, **kwargs):
    return True


null_escaper = SimpleNamespace(
    select=select_always,
    output_type=six.text_type,
    escape=identity,
    mark_escaped=identity,
    join=default_join,
    use_isolating=None,
    name='null_escaper',
)


def escapers_compatible(outer_escaper, inner_escaper):
    # Messages with no escaper defined can always be used from other messages,
    # because the outer message will do the escaping, and the inner message will
    # always return a simple string which must be handle by all escapers.
    if inner_escaper.name == null_escaper.name:
        return True

    # Otherwise, however, since escapers could potentially build completely
    # different types of objects, we disallow any other mismatch.
    return outer_escaper.name == inner_escaper.name


def escaper_for_message(escapers, message_id):
    if escapers is not None:
        for escaper in escapers:
            if escaper.select(message_id=message_id):
                return escaper

    return null_escaper


class RegisteredEscaper(object):
    """
    Escaper wrapper that encapsulates logic like knowing what the escaper
    functions are called in the compiler environment.
    """
    def __init__(self, escaper, compiler_env):
        self._escaper = escaper
        self._compiler_env = compiler_env

    def __repr__(self):
        return '<RegisteredEscaper {0}>'.format(self.name)

    @property
    def select(self):
        return self._escaper.select

    @property
    def output_type(self):
        return self._escaper.output_type

    @property
    def escape(self):
        return self._escaper.escape

    @property
    def mark_escaped(self):
        return self._escaper.mark_escaped

    @property
    def join(self):
        return self._escaper.join

    @property
    def use_isolating(self):
        return self._escaper.use_isolating

    @property
    def name(self):
        return self._escaper.name

    def get_reserved_names_with_properties(self):
        # escaper.output_type, escaper.mark_escaped, escaper.escape, escaper.join
        return [
            (self.output_type_name(),
             self._escaper.output_type,
             {}),
            (self.escape_name(),
             self._escaper.escape,
             {codegen.PROPERTY_RETURN_TYPE: self._escaper.output_type}),
            (self.mark_escaped_name(),
             self._escaper.mark_escaped,
             {codegen.PROPERTY_RETURN_TYPE: self._escaper.output_type}),
            (self.join_name(),
             self._escaper.join,
             {codegen.PROPERTY_RETURN_TYPE: self._escaper.output_type}),
        ]

    def _prefix(self):
        idx = self._compiler_env.escapers.index(self)
        return "escaper_{0}_".format(idx)

    def output_type_name(self):
        return "{0}_output_type".format(self._prefix())

    def mark_escaped_name(self):
        return "{0}_mark_escaped".format(self._prefix())

    def escape_name(self):
        return "{0}_escape".format(self._prefix())

    def join_name(self):
        return "{0}_join".format(self._prefix())


class EscaperJoin(codegen.StringJoin):
    def __init__(self, parts, escaper, scope):
        super(EscaperJoin, self).__init__(parts)
        self.type = escaper.output_type
        self.escaper = escaper
        self.scope = scope

    def as_ast(self):
        if self.escaper.join is default_join:
            return super(EscaperJoin, self).as_ast()
        else:
            return codegen.FunctionCall(
                self.escaper.join_name(),
                [codegen.List(self.parts)],
                {},
                self.scope,
                expr_type=self.type).as_ast()

    def simplify(self, changes, simplifier):
        new_parts = []
        for part in self.parts:
            handled = False
            if len(new_parts) > 0:
                last_part = new_parts[-1]
                # Merge string literals wrapped in mark_escaped calls
                if (self.escaper.name != null_escaper.name and
                    all((isinstance(p, codegen.FunctionCall) and
                         p.function_name == self.escaper.mark_escaped_name() and
                         isinstance(p.args[0], codegen.String))
                        for p in [last_part, part])):
                    new_parts[-1] = codegen.FunctionCall(last_part.function_name,
                                                         [codegen.String(last_part.args[0].string_value +
                                                                         part.args[0].string_value)],
                                                         {},
                                                         self.scope)
                    handled = True

            if not handled:
                new_parts.append(part)
        if len(new_parts) < len(self.parts):
            changes.append(True)
        self.parts = new_parts

        return simplifier(super(EscaperJoin, self).simplify(changes, simplifier), changes)
