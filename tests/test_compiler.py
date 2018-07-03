from __future__ import absolute_import, unicode_literals

import unittest
from collections import OrderedDict

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
    messages = OrderedDict()
    for item in resource.body:
        if isinstance(item, Message):
            messages[item.id.name] = item
        elif isinstance(item, Term):
            messages[item.id.name] = item
    return messages


def compile_messages_to_python(source, locale, use_isolating=True, strict=True):
    messages = parse_ftl(source)
    module, message_mapping, module_globals = messages_to_module(messages, locale,
                                                                 use_isolating=use_isolating,
                                                                 strict=strict)
    return module.as_source_code()


class TestCompiler(unittest.TestCase):
    locale = babel.Locale.parse('en_US')

    maxDiff = None

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

    def test_string_literal_in_placeable(self):
        code = compile_messages_to_python(dedent_ftl("""
            foo = { "Foo" }
        """), self.locale)
        self.assertCodeEqual(code, """
        def foo(message_args, errors):
            return ('Foo', errors)
        """)

    def test_message_reference_plus_string_literal(self):
        code = compile_messages_to_python(dedent_ftl("""
            foo = Foo
            bar = X { foo }
        """), self.locale)
        self.assertCodeEqual(code, """
            def foo(message_args, errors):
                return ('Foo', errors)

            def bar(message_args, errors):
                _tmp, errors = foo(message_args, errors)
                return (''.join(['X ', _tmp]), errors)
        """)

    def test_single_message_reference(self):
        code = compile_messages_to_python(dedent_ftl("""
            foo = Foo
            bar = { foo }
        """), self.locale)
        self.assertCodeEqual(code, """
            def foo(message_args, errors):
                return ('Foo', errors)

            def bar(message_args, errors):
                return foo(message_args, errors)
        """)

    def test_single_message_reference_reversed_order(self):
        # We should cope with forward references
        code = compile_messages_to_python(dedent_ftl("""
            bar = { foo }
            foo = Foo
        """), self.locale)
        self.assertCodeEqual(code, """
            def bar(message_args, errors):
                return foo(message_args, errors)

            def foo(message_args, errors):
                return ('Foo', errors)
        """)

    def test_single_message_bad_reference(self):
        code = compile_messages_to_python(dedent_ftl("""
            bar = { foo }
        """), self.locale)
        # We already know that foo does not exist, so we can hard code the error
        # into the function.
        self.assertCodeEqual(code, """
            def bar(message_args, errors):
                errors.append(FluentReferenceError('Unknown message: foo'))
                return ('foo', errors)
        """)

    def test_name_collision_function_args(self):
        code = compile_messages_to_python(dedent_ftl("""
            errors = Errors
        """), self.locale)
        self.assertCodeEqual(code, """
            def errors2(message_args, errors):
                return ('Errors', errors)
        """)

    def test_name_collision_builtins(self):
        code = compile_messages_to_python(dedent_ftl("""
            zip = Zip
        """), self.locale)
        self.assertCodeEqual(code, """
            def zip2(message_args, errors):
                return ('Zip', errors)
        """)

    def test_message_mapping_used(self):
        # Checking that we actually use message_mapping when looking up the name
        # of the message function to call.
        code = compile_messages_to_python(dedent_ftl("""
            zip = Foo
            str = { zip }
        """), self.locale)
        self.assertCodeEqual(code, """
            def zip2(message_args, errors):
                return ('Foo', errors)

            def str2(message_args, errors):
                return zip2(message_args, errors)
        """)

    def test_external_argument(self):
        code = compile_messages_to_python(dedent_ftl("""
            with-arg = { $arg }
        """), self.locale)
        self.assertCodeEqual(code, """
            def with_arg(message_args, errors):
                try:
                    _tmp = message_args['arg']
                except LookupError:
                    errors.append(FluentReferenceError('Unknown external: arg'))
                    _tmp = '???'
                else:
                    _tmp = handle_argument(_tmp, 'arg', errors)

                return (_tmp, errors)
        """)
