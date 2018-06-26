from __future__ import absolute_import, unicode_literals

import unittest

import babel

from fluent.compiler import messages_to_module
from fluent.syntax import FluentParser
from fluent.syntax.ast import Message, Term

from .syntax import dedent_ftl

from .test_codegen import normalize_python


# Some TDD tests to help develop CompilingMessageContext. It should be possible to delete
# the tests here and still have complete test coverage of the compiler.py module, via
# the other MessageContext.format tests.

def parse_ftl(source):
    resource = FluentParser().parse(source)
    messages = {}
    for item in resource.body:
        if isinstance(item, Message):
            messages[item.id.name] = item
        elif isinstance(item, Term):
            messages[item.id.name] = item
    return messages


def compile_messages_to_python(source, locale, use_isolating=True, strict=True):
    messages = parse_ftl(source)
    module, message_mapping = messages_to_module(messages, locale, use_isolating=use_isolating, strict=strict)
    return module.as_source_code()


class TestCompiler(unittest.TestCase):
    locale = babel.Locale.parse('en_US')

    def assertCodeEqual(self, code1, code2):
        self.assertEqual(normalize_python(code1),
                         normalize_python(code2))

    def test_single_string_literal(self):
        code = compile_messages_to_python(dedent_ftl("""
            foo = Foo
        """), self.locale)
        self.assertCodeEqual(code, """
        def foo(message_args, errors):
            return ('Foo', errors)
        """)
