from __future__ import absolute_import, unicode_literals

import unittest
from collections import OrderedDict

import babel

from fluent.builtins import BUILTINS
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
    messages = parse_ftl(dedent_ftl(source))
    module, message_mapping, module_globals = messages_to_module(messages, locale,
                                                                 use_isolating=use_isolating,
                                                                 functions=BUILTINS,
                                                                 strict=strict)
    return module.as_source_code()


class TestCompiler(unittest.TestCase):
    locale = babel.Locale.parse('en_US')

    maxDiff = None

    def assertCodeEqual(self, code1, code2):
        self.assertEqual(normalize_python(code1),
                         normalize_python(code2))

    def test_single_string_literal(self):
        code = compile_messages_to_python("""
            foo = Foo
        """, self.locale)
        self.assertCodeEqual(code, """
            def foo(message_args, errors):
                return ('Foo', errors)
        """)

    def test_string_literal_in_placeable(self):
        code = compile_messages_to_python("""
            foo = { "Foo" }
        """, self.locale)
        self.assertCodeEqual(code, """
            def foo(message_args, errors):
                return ('Foo', errors)
        """)

    def test_number_literal(self):
        code = compile_messages_to_python("""
            foo = { 123 }
        """, self.locale)
        self.assertCodeEqual(code, """
            def foo(message_args, errors):
                return (NUMBER(123).format(locale), errors)
        """)

    def test_interpolated_number(self):
        code = compile_messages_to_python("""
            foo = x { 123 } y
        """, self.locale)
        self.assertCodeEqual(code, """
            def foo(message_args, errors):
                return (''.join(['x ', NUMBER(123).format(locale), ' y']), errors)
        """)

    def test_message_reference_plus_string_literal(self):
        code = compile_messages_to_python("""
            foo = Foo
            bar = X { foo }
        """, self.locale)
        self.assertCodeEqual(code, """
            def foo(message_args, errors):
                return ('Foo', errors)

            def bar(message_args, errors):
                _tmp, errors = foo(message_args, errors)
                return (''.join(['X ', _tmp]), errors)
        """)

    def test_single_message_reference(self):
        code = compile_messages_to_python("""
            foo = Foo
            bar = { foo }
        """, self.locale)
        self.assertCodeEqual(code, """
            def foo(message_args, errors):
                return ('Foo', errors)

            def bar(message_args, errors):
                return foo(message_args, errors)
        """)

    def test_message_attr_reference(self):
        code = compile_messages_to_python("""
            foo
               .attr = Foo Attr
            bar = { foo.attr }
        """, self.locale)
        self.assertCodeEqual(code, """
            def foo__attr(message_args, errors):
                return ('Foo Attr', errors)

            def bar(message_args, errors):
                return foo__attr(message_args, errors)
        """)

    def test_single_message_reference_reversed_order(self):
        # We should cope with forward references
        code = compile_messages_to_python("""
            bar = { foo }
            foo = Foo
        """, self.locale)
        self.assertCodeEqual(code, """
            def bar(message_args, errors):
                return foo(message_args, errors)

            def foo(message_args, errors):
                return ('Foo', errors)
        """)

    def test_single_message_bad_reference(self):
        code = compile_messages_to_python("""
            bar = { foo }
        """, self.locale)
        # We already know that foo does not exist, so we can hard code the error
        # into the function.
        self.assertCodeEqual(code, """
            def bar(message_args, errors):
                errors.append(FluentReferenceError('Unknown message: foo'))
                return (FluentNone('foo').format(locale), errors)
        """)

    def test_name_collision_function_args(self):
        code = compile_messages_to_python("""
            errors = Errors
        """, self.locale)
        self.assertCodeEqual(code, """
            def errors2(message_args, errors):
                return ('Errors', errors)
        """)

    def test_name_collision_builtins(self):
        code = compile_messages_to_python("""
            zip = Zip
        """, self.locale)
        self.assertCodeEqual(code, """
            def zip2(message_args, errors):
                return ('Zip', errors)
        """)

    def test_message_mapping_used(self):
        # Checking that we actually use message_mapping when looking up the name
        # of the message function to call.
        code = compile_messages_to_python("""
            zip = Foo
            str = { zip }
        """, self.locale)
        self.assertCodeEqual(code, """
            def zip2(message_args, errors):
                return ('Foo', errors)

            def str2(message_args, errors):
                return zip2(message_args, errors)
        """)

    def test_external_argument(self):
        code = compile_messages_to_python("""
            with-arg = { $arg }
        """, self.locale)
        self.assertCodeEqual(code, """
            def with_arg(message_args, errors):
                try:
                    _tmp = message_args['arg']
                except LookupError:
                    errors.append(FluentReferenceError('Unknown external: arg'))
                    _tmp = FluentNone('arg')
                else:
                    _tmp = handle_argument(_tmp, 'arg', locale, errors)

                return (handle_output(_tmp, locale, errors), errors)
        """)

    def test_function_call(self):
        code = compile_messages_to_python("""
            foo = { NUMBER(12345) }
        """, self.locale)
        self.assertCodeEqual(code, """
            def foo(message_args, errors):
                return (NUMBER(12345).format(locale), errors)
        """)

    def test_function_call_external_arg(self):
        code = compile_messages_to_python("""
            foo = { NUMBER($arg) }
        """, self.locale)
        self.assertCodeEqual(code, """
            def foo(message_args, errors):
                try:
                    _tmp = message_args['arg']
                except LookupError:
                    errors.append(FluentReferenceError('Unknown external: arg'))
                    _tmp = FluentNone('arg')
                else:
                    _tmp = handle_argument(_tmp, 'arg', locale, errors)

                return (NUMBER(_tmp).format(locale), errors)
        """)

    def test_function_call_kwargs(self):
        code = compile_messages_to_python("""
            foo = { NUMBER(12345, useGrouping: 0) }
        """, self.locale)
        self.assertCodeEqual(code, """
            def foo(message_args, errors):
                return (NUMBER(12345, useGrouping=0).format(locale), errors)
        """)

    def test_message_with_attrs(self):
        code = compile_messages_to_python("""
            foo = Foo
               .attr-1 = Attr 1
               .attr-2 = Attr 2
        """, self.locale)
        self.assertCodeEqual(code, """
            def foo(message_args, errors):
                return ('Foo', errors)

            def foo__attr_1(message_args, errors):
                return ('Attr 1', errors)

            def foo__attr_2(message_args, errors):
                return ('Attr 2', errors)
        """)

    def test_variant(self):
        code = compile_messages_to_python("""
            -my-term = {
                [a] A
               *[b] B
                [c] C
              }
        """, self.locale)
        self.assertCodeEqual(code, """
            def _my_term(message_args, errors, variant=None):
                if variant == 'a':
                    _ret = 'A'
                elif variant == 'c':
                    _ret = 'C'
                else:
                    if variant is not None and variant != 'b':
                        errors.append(FluentReferenceError('Unknown variant: {0}'.format(variant)))

                    _ret = 'B'

                return (_ret, errors)
        """)

    def test_variant_select(self):
        term_ftl = """
            -my-term = {
                [a] A
               *[b] B
              }
        """
        calling_ftl = """
            foo = { -my-term[a] }
        """
        term_code = compile_messages_to_python(term_ftl,
                                               self.locale)
        combined_code = compile_messages_to_python(term_ftl + calling_ftl,
                                                   self.locale)
        self.assertCodeEqual(combined_code, term_code + """
def foo(message_args, errors):
    return _my_term(message_args, errors, variant='a')
        """.strip())

    def test_select_string(self):
        code = compile_messages_to_python("""
           foo = { "a" ->
                [a] A
               *[b] B
             }
        """, self.locale)
        self.assertCodeEqual(code, """
            def foo(message_args, errors):
                _key = 'a'
                if _key == 'a':
                    _ret = 'A'
                else:
                    _ret = 'B'

                return (_ret, errors)
        """)

    def test_select_number(self):
        code = compile_messages_to_python("""
           foo = { 1 ->
                [1] One
               *[2] { 2 }
             }
        """, self.locale)
        self.assertCodeEqual(code, """
            def foo(message_args, errors):
                _key = 1
                if _key == 1:
                    _ret = 'One'
                else:
                    _ret = NUMBER(2).format(locale)

                return (_ret, errors)
        """)

    def test_select_plural_category_with_literal(self):
        code = compile_messages_to_python("""
           foo = { 1 ->
                [one] One
               *[other] Other
             }
        """, self.locale)
        self.assertCodeEqual(code, """
            def foo(message_args, errors):
                _key = 1
                _plural_form = plural_form_for_number(_key)
                if _key == 'one' or _plural_form == 'one':
                    _ret = 'One'
                else:
                    _ret = 'Other'

                return (_ret, errors)
        """)

    def test_select_plural_category_with_arg(self):
        code = compile_messages_to_python("""
           foo = { $count ->
                [0] You have nothing
                [one] You have one thing
               *[other] You have some things
             }
        """, self.locale)
        self.assertCodeEqual(code, """
            def foo(message_args, errors):
                try:
                    _tmp = message_args['count']
                except LookupError:
                    errors.append(FluentReferenceError('Unknown external: count'))
                    _tmp = FluentNone('count')
                else:
                    _tmp = handle_argument(_tmp, 'count', locale, errors)

                _key = _tmp
                _plural_form = plural_form_for_number(_key)
                if _key == 0:
                    _ret = 'You have nothing'
                elif _key == 'one' or _plural_form == 'one':
                    _ret = 'You have one thing'
                else:
                    _ret = 'You have some things'

                return (_ret, errors)
        """)
