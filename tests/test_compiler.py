from __future__ import absolute_import, unicode_literals

import unittest
from collections import OrderedDict

import babel

from fluent.builtins import BUILTINS
from fluent.compiler import messages_to_module
from fluent.exceptions import FluentCyclicReferenceError, FluentReferenceError
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


def compile_messages_to_python(source, locale, use_isolating=False, functions=None):
    if functions is None:
        functions = {}
    _functions = BUILTINS.copy()
    _functions.update(functions)
    messages = parse_ftl(dedent_ftl(source))
    module, message_mapping, module_globals, errors = messages_to_module(
        messages, locale,
        use_isolating=use_isolating,
        functions=_functions)
    return module.as_source_code(), errors


class TestCompiler(unittest.TestCase):
    locale = babel.Locale.parse('en_US')

    maxDiff = None

    def assertCodeEqual(self, code1, code2):
        self.assertEqual(normalize_python(code1),
                         normalize_python(code2))

    def test_single_string_literal(self):
        code, errs = compile_messages_to_python("""
            foo = Foo
        """, self.locale)
        self.assertCodeEqual(code, """
            def foo(message_args, errors):
                return ('Foo', errors)
        """)
        self.assertEqual(errs, [])

    def test_string_literal_in_placeable(self):
        code, errs = compile_messages_to_python("""
            foo = { "Foo" }
        """, self.locale)
        self.assertCodeEqual(code, """
            def foo(message_args, errors):
                return ('Foo', errors)
        """)
        self.assertEqual(errs, [])

    def test_number_literal(self):
        code, errs = compile_messages_to_python("""
            foo = { 123 }
        """, self.locale)
        self.assertCodeEqual(code, """
            def foo(message_args, errors):
                return (NUMBER(123).format(locale), errors)
        """)
        self.assertEqual(errs, [])

    def test_interpolated_number(self):
        code, errs = compile_messages_to_python("""
            foo = x { 123 } y
        """, self.locale)
        self.assertCodeEqual(code, """
            def foo(message_args, errors):
                return (''.join(['x ', NUMBER(123).format(locale), ' y']), errors)
        """)
        self.assertEqual(errs, [])

    def test_message_reference_plus_string_literal(self):
        code, errs = compile_messages_to_python("""
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
        self.assertEqual(errs, [])

    def test_single_message_reference(self):
        code, errs = compile_messages_to_python("""
            foo = Foo
            bar = { foo }
        """, self.locale)
        self.assertCodeEqual(code, """
            def foo(message_args, errors):
                return ('Foo', errors)

            def bar(message_args, errors):
                return foo(message_args, errors)
        """)
        self.assertEqual(errs, [])

    def test_message_attr_reference(self):
        code, errs = compile_messages_to_python("""
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
        self.assertEqual(errs, [])

    def test_single_message_reference_reversed_order(self):
        # We should cope with forward references
        code, errs = compile_messages_to_python("""
            bar = { foo }
            foo = Foo
        """, self.locale)
        self.assertCodeEqual(code, """
            def bar(message_args, errors):
                return foo(message_args, errors)

            def foo(message_args, errors):
                return ('Foo', errors)
        """)
        self.assertEqual(errs, [])

    def test_single_message_bad_reference(self):
        code, errs = compile_messages_to_python("""
            bar = { foo }
        """, self.locale)
        # We already know that foo does not exist, so we can hard code the error
        # into the function for the runtime error.
        self.assertCodeEqual(code, """
            def bar(message_args, errors):
                errors.append(FluentReferenceError('Unknown message: foo'))
                return (FluentNone('foo').format(locale), errors)
        """)
        # And we should get a compile time error:
        self.assertEqual(errs, [('bar', FluentReferenceError("Unknown message: foo"))])

    def test_name_collision_function_args(self):
        code, errs = compile_messages_to_python("""
            errors = Errors
        """, self.locale)
        self.assertCodeEqual(code, """
            def errors2(message_args, errors):
                return ('Errors', errors)
        """)
        self.assertEqual(errs, [])

    def test_name_collision_builtins(self):
        code, errs = compile_messages_to_python("""
            zip = Zip
        """, self.locale)
        self.assertCodeEqual(code, """
            def zip2(message_args, errors):
                return ('Zip', errors)
        """)
        self.assertEqual(errs, [])

    def test_name_collision_keyword(self):
        code, errs = compile_messages_to_python("""
            class = Class
        """, self.locale)
        self.assertCodeEqual(code, """
            def class2(message_args, errors):
                return ('Class', errors)
        """)
        self.assertEqual(errs, [])

    def test_message_mapping_used(self):
        # Checking that we actually use message_mapping when looking up the name
        # of the message function to call.
        code, errs = compile_messages_to_python("""
            zip = Foo
            str = { zip }
        """, self.locale)
        self.assertCodeEqual(code, """
            def zip2(message_args, errors):
                return ('Foo', errors)

            def str2(message_args, errors):
                return zip2(message_args, errors)
        """)
        self.assertEqual(errs, [])

    def test_external_argument(self):
        code, errs = compile_messages_to_python("""
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
        self.assertEqual(errs, [])

    def test_function_call(self):
        code, errs = compile_messages_to_python("""
            foo = { NUMBER(12345) }
        """, self.locale)
        self.assertCodeEqual(code, """
            def foo(message_args, errors):
                return (NUMBER(12345).format(locale), errors)
        """)
        self.assertEqual(errs, [])

    def test_function_call_external_arg(self):
        code, errs = compile_messages_to_python("""
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
        self.assertEqual(errs, [])

    def test_function_call_kwargs(self):
        code, errs = compile_messages_to_python("""
            foo = { NUMBER(12345, useGrouping: 0) }
        """, self.locale)
        self.assertCodeEqual(code, """
            def foo(message_args, errors):
                return (NUMBER(12345, useGrouping=0).format(locale), errors)
        """)
        self.assertEqual(errs, [])

    def test_missing_function_call(self):
        code, errs = compile_messages_to_python("""
            foo = { MISSING(123) }
        """, self.locale)
        self.assertCodeEqual(code, """
            def foo(message_args, errors):
                errors.append(FluentReferenceError('Unknown function: MISSING'))
                return (FluentNone('MISSING()').format(locale), errors)
        """),
        self.assertEqual(errs, [('foo', FluentReferenceError('Unknown function: MISSING'))])

    def test_function_call_with_bad_keyword_arg(self):
        def MYFUNC(arg, kw1=None, kw2=None):
            return arg
        # Disallow 'kw2' arg
        MYFUNC.ftl_arg_spec = [1, 'kw1']
        code, errs = compile_messages_to_python("""
            foo = { MYFUNC(123, kw2: 1) }
        """, self.locale, functions={'MYFUNC': MYFUNC})
        self.assertCodeEqual(code, """
            def foo(message_args, errors):
                errors.append(TypeError("MYFUNC() got an unexpected keyword argument 'kw2'"))
                return (FluentNone('MYFUNC()').format(locale), errors)
        """),
        self.assertEqual(len(errs), 1)
        self.assertEqual(errs[0][0], 'foo')
        self.assertEqual(type(errs[0][1]), TypeError)

    def test_function_call_with_bad_positional_arg(self):
        def MYFUNC():
            return ''
        code, errs = compile_messages_to_python("""
            foo = { MYFUNC(123) }
        """, self.locale, functions={'MYFUNC': MYFUNC})
        self.assertCodeEqual(code, """
            def foo(message_args, errors):
                errors.append(TypeError('MYFUNC() takes 0 positional arguments but 1 was given'))
                return (FluentNone('MYFUNC()').format(locale), errors)
        """),
        self.assertEqual(len(errs), 1)
        self.assertEqual(errs[0][0], 'foo')
        self.assertEqual(type(errs[0][1]), TypeError)

    def test_message_with_attrs(self):
        code, errs = compile_messages_to_python("""
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
        self.assertEqual(errs, [])

    def test_variant(self):
        code, errs = compile_messages_to_python("""
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
        self.assertEqual(errs, [])

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
        term_code, term_errs = compile_messages_to_python(term_ftl,
                                                          self.locale)
        combined_code, combined_errs = compile_messages_to_python(term_ftl + calling_ftl,
                                                                  self.locale)
        self.assertCodeEqual(combined_code, term_code + """
def foo(message_args, errors):
    return _my_term(message_args, errors, variant='a')
        """.strip())
        self.assertEqual(term_errs, [])
        self.assertEqual(combined_errs, [])

    def test_select_string(self):
        code, errs = compile_messages_to_python("""
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
        self.assertEqual(errs, [])

    def test_select_number(self):
        code, errs = compile_messages_to_python("""
           foo = { 1 ->
                [1] One
               *[2] { 2 }
             }
        """, self.locale)
        # We should not get 'NUMBER' calls in the select expression or
        # or the key comparisons, but we should get them for the select value
        # for { 2 }.
        self.assertCodeEqual(code, """
            def foo(message_args, errors):
                _key = 1
                if _key == 1:
                    _ret = 'One'
                else:
                    _ret = NUMBER(2).format(locale)

                return (_ret, errors)
        """)
        self.assertEqual(errs, [])

    def test_select_plural_category_with_literal(self):
        code, errs = compile_messages_to_python("""
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
        self.assertEqual(errs, [])

    def test_select_plural_category_with_arg(self):
        code, errs = compile_messages_to_python("""
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
        self.assertEqual(errs, [])

    def test_combine_strings(self):
        code, errs = compile_messages_to_python("""
            foo = Start { "Middle" } End
        """, self.locale)
        self.assertCodeEqual(code, """
            def foo(message_args, errors):
                return ('Start Middle End', errors)
        """)
        self.assertEqual(errs, [])

    def test_single_string_literal_isolating(self):
        code, errs = compile_messages_to_python("""
            foo = Foo
        """, self.locale, use_isolating=True)
        # No isolating chars, because we have no placeables.
        self.assertCodeEqual(code, """
            def foo(message_args, errors):
                return ('Foo', errors)
        """)
        self.assertEqual(errs, [])

    def test_interpolation_isolating(self):
        code, errs = compile_messages_to_python("""
            foo = Foo { $arg } Bar
        """, self.locale, use_isolating=True)
        self.assertCodeEqual(code, """
            def foo(message_args, errors):
                try:
                    _tmp = message_args['arg']
                except LookupError:
                    errors.append(FluentReferenceError('Unknown external: arg'))
                    _tmp = FluentNone('arg')
                else:
                    _tmp = handle_argument(_tmp, 'arg', locale, errors)

                return (''.join(['Foo \\u2068', handle_output(_tmp, locale, errors), '\\u2069 Bar']), errors)
        """)
        self.assertEqual(errs, [])

    def test_cycle_detection(self):
        code, errs = compile_messages_to_python("""
            foo = { foo }
        """, self.locale)
        self.assertCodeEqual(code, """
            def foo(message_args, errors):
                errors.append(FluentCyclicReferenceError('Cyclic reference in foo'))
                return (FluentNone().format(locale), errors)
        """)
        self.assertEqual(errs, [('foo', FluentCyclicReferenceError("Cyclic reference in foo"))])

    def test_cycle_detection_with_attrs(self):
        code, errs = compile_messages_to_python("""
            foo
               .attr1 = { bar.attr2 }

            bar
               .attr2 = { foo.attr1 }
        """, self.locale)
        self.assertCodeEqual(code, """
            def foo__attr1(message_args, errors):
                errors.append(FluentCyclicReferenceError('Cyclic reference in foo.attr1'))
                return (FluentNone().format(locale), errors)

            def bar__attr2(message_args, errors):
                errors.append(FluentCyclicReferenceError('Cyclic reference in bar.attr2'))
                return (FluentNone().format(locale), errors)
        """)
        self.assertEqual(errs, [('foo.attr1', FluentCyclicReferenceError("Cyclic reference in foo.attr1")),
                                ('bar.attr2', FluentCyclicReferenceError("Cyclic reference in bar.attr2")),
                                ])

    def test_cycle_detection_with_unknown_attr(self):
        # unknown attributes fall back to main message, which brings
        # another option for a cycle.
        code, errs = compile_messages_to_python("""
            foo = { bar.bad-attr }

            bar = { foo }
        """, self.locale)
        self.assertCodeEqual(code, """
            def foo(message_args, errors):
                errors.append(FluentCyclicReferenceError('Cyclic reference in foo'))
                return (FluentNone().format(locale), errors)

            def bar(message_args, errors):
                errors.append(FluentCyclicReferenceError('Cyclic reference in bar'))
                return (FluentNone().format(locale), errors)
        """)
        self.assertEqual(errs, [('foo', FluentCyclicReferenceError("Cyclic reference in foo")),
                                ('bar', FluentCyclicReferenceError("Cyclic reference in bar")),
                                ])
