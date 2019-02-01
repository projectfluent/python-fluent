from __future__ import absolute_import, unicode_literals

import unittest

import six

from fluent.runtime.errors import FluentReferenceError
from fluent.runtime.types import FluentNone, fluent_number

from .. import all_fluent_bundle_implementations
from ..utils import dedent_ftl


@all_fluent_bundle_implementations
class TestFunctionCalls(unittest.TestCase):

    def setUp(self):
        def IDENTITY(x):
            return x

        def WITH_KEYWORD(x, y=0):
            return six.text_type(x + y)

        def RUNTIME_ERROR(x):
            return 1/0

        def RUNTIME_TYPE_ERROR(arg):
            return arg + 1

        def ANY_ARGS(*args, **kwargs):
            return (' '.join(map(six.text_type, args)) + " " +
                    ' '.join("{0}={1}".format(k, v) for k, v in sorted(kwargs.items())))

        def RESTRICTED(allowed=None, notAllowed=None):
            return allowed if allowed is not None else 'nothing passed'

        def BAD_OUTPUT():
            class Unsupported(object):
                pass
            return Unsupported()

        RESTRICTED.ftl_arg_spec = (0, ['allowed'])

        self.ctx = self.fluent_bundle_cls(
            ['en-US'], use_isolating=False,
            functions={'IDENTITY': IDENTITY,
                       'WITH_KEYWORD': WITH_KEYWORD,
                       'RUNTIME_ERROR': RUNTIME_ERROR,
                       'RUNTIME_TYPE_ERROR': RUNTIME_TYPE_ERROR,
                       'ANY_ARGS': ANY_ARGS,
                       'RESTRICTED': RESTRICTED,
                       'BAD_OUTPUT': BAD_OUTPUT,
                       })
        self.ctx.add_messages(dedent_ftl("""
            foo = Foo
                .attr = Attribute
            pass-string        = { IDENTITY("a") }
            pass-number        = { IDENTITY(1) }
            pass-message       = { IDENTITY(foo) }
            pass-attr          = { IDENTITY(foo.attr) }
            pass-external      = { IDENTITY($ext) }
            pass-function-call = { IDENTITY(IDENTITY(1)) }
            too-few-pos-args   = { IDENTITY() }
            too-many-pos-args  = { IDENTITY(2, 3, 4) }
            use-good-kwarg     = { WITH_KEYWORD(1, y: 1) }
            use-bad-kwarg      = { WITH_KEYWORD(1, bad: 1) }
            runtime-error      = { RUNTIME_ERROR(1) }
            runtime-type-error = { RUNTIME_TYPE_ERROR("hello") }
            use-any-args       = { ANY_ARGS(1, 2, 3, x:1) }
            use-restricted-ok  = { RESTRICTED(allowed: 1) }
            use-restricted-bad = { RESTRICTED(notAllowed: 1) }
            bad-output         = { BAD_OUTPUT() }
            non-identfier-arg  = { ANY_ARGS(1, foo: 2, non-identifier: 3) }
        """))

    def test_accepts_strings(self):
        val, errs = self.ctx.format('pass-string', {})
        self.assertEqual(val, "a")
        self.assertEqual(len(errs), 0)

    def test_accepts_numbers(self):
        val, errs = self.ctx.format('pass-number', {})
        self.assertEqual(val, "1")
        self.assertEqual(len(errs), 0)

    def test_accepts_entities(self):
        val, errs = self.ctx.format('pass-message', {})
        self.assertEqual(val, "Foo")
        self.assertEqual(len(errs), 0)

    def test_accepts_attributes(self):
        val, errs = self.ctx.format('pass-attr', {})
        self.assertEqual(val, "Attribute")
        self.assertEqual(len(errs), 0)

    def test_accepts_externals(self):
        val, errs = self.ctx.format('pass-external', {'ext': 'Ext'})
        self.assertEqual(val, "Ext")
        self.assertEqual(len(errs), 0)

    def test_accepts_function_calls(self):
        val, errs = self.ctx.format('pass-function-call', {})
        self.assertEqual(val, "1")
        self.assertEqual(len(errs), 0)

    def test_too_few_pos_args(self):
        val, errs = self.ctx.format('too-few-pos-args', {})
        self.assertEqual(val, "IDENTITY()")
        self.assertEqual(len(errs), 1)
        self.assertEqual(type(errs[0]), TypeError)

    def test_too_many_pos_args(self):
        val, errs = self.ctx.format('too-many-pos-args', {})
        self.assertEqual(val, "2")
        self.assertEqual(len(errs), 1)
        self.assertEqual(type(errs[0]), TypeError)

    def test_good_kwarg(self):
        val, errs = self.ctx.format('use-good-kwarg')
        self.assertEqual(val, "2")
        self.assertEqual(len(errs), 0)

    def test_bad_kwarg(self):
        val, errs = self.ctx.format('use-bad-kwarg')
        self.assertEqual(val, "1")
        self.assertEqual(len(errs), 1)
        self.assertEqual(type(errs[0]), TypeError)

    def test_runtime_error(self):
        self.assertRaises(ZeroDivisionError,
                          self.ctx.format,
                          'runtime-error')

    def test_runtime_type_error(self):
        self.assertRaises(TypeError,
                          self.ctx.format,
                          'runtime-type-error')

    def test_use_any_args(self):
        val, errs = self.ctx.format('use-any-args')
        self.assertEqual(val, "1 2 3 x=1")
        self.assertEqual(len(errs), 0)

    def test_restricted_ok(self):
        val, errs = self.ctx.format('use-restricted-ok')
        self.assertEqual(val, "1")
        self.assertEqual(len(errs), 0)

    def test_restricted_bad(self):
        val, errs = self.ctx.format('use-restricted-bad')
        self.assertEqual(val, "nothing passed")
        self.assertEqual(len(errs), 1)
        self.assertEqual(type(errs[0]), TypeError)

    def test_bad_output(self):
        # This is a developer error, so should raise an exception
        with self.assertRaises(TypeError) as cm:
            self.ctx.format('bad-output')
        self.assertIn("Unsupported", cm.exception.args[0])

    def test_non_identifier_python_keyword_args(self):
        val, errs = self.ctx.format('non-identfier-arg')
        self.assertEqual(val, '1 foo=2 non-identifier=3')
        self.assertEqual(len(errs), 0)


@all_fluent_bundle_implementations
class TestMissing(unittest.TestCase):

    def setUp(self):
        self.ctx = self.fluent_bundle_cls(['en-US'], use_isolating=False)
        self.ctx.add_messages(dedent_ftl("""
            missing = { MISSING(1) }
        """))

    def test_falls_back_to_name_of_function(self):
        val, errs = self.ctx.format("missing", {})
        self.assertEqual(val, "MISSING()")
        self.assertEqual(errs,
                         [FluentReferenceError("Unknown function: MISSING")])


@all_fluent_bundle_implementations
class TestResolving(unittest.TestCase):

    def setUp(self):
        self.args_passed = []

        def number_processor(number):
            self.args_passed.append(number)
            return number

        self.ctx = self.fluent_bundle_cls(
            ['en-US'], use_isolating=False,
            functions={'NUMBER_PROCESSOR':
                       number_processor})

        self.ctx.add_messages(dedent_ftl("""
            pass-number = { NUMBER_PROCESSOR(1) }
            pass-arg = { NUMBER_PROCESSOR($arg) }
        """))

    def test_args_passed_as_numbers(self):
        val, errs = self.ctx.format('pass-arg', {'arg': 1})
        self.assertEqual(val, "1")
        self.assertEqual(len(errs), 0)
        self.assertEqual(self.args_passed, [1])
        self.assertEqual(self.args_passed, [fluent_number(1)])

    def test_literals_passed_as_numbers(self):
        val, errs = self.ctx.format('pass-number', {})
        self.assertEqual(val, "1")
        self.assertEqual(len(errs), 0)
        self.assertEqual(self.args_passed, [1])
        self.assertEqual(self.args_passed, [fluent_number(1)])


@all_fluent_bundle_implementations
class TestKeywordArgs(unittest.TestCase):

    def setUp(self):
        self.args_passed = []

        def my_function(arg, kwarg1=None, kwarg2="default"):
            self.args_passed.append((arg, kwarg1, kwarg2))
            return arg

        self.ctx = self.fluent_bundle_cls(
            ['en-US'], use_isolating=False,
            functions={'MYFUNC': my_function})
        self.ctx.add_messages(dedent_ftl("""
            pass-arg        = { MYFUNC("a") }
            pass-kwarg1     = { MYFUNC("a", kwarg1: 1) }
            pass-kwarg2     = { MYFUNC("a", kwarg2: "other") }
            pass-kwargs     = { MYFUNC("a", kwarg1: 1, kwarg2: "other") }
            pass-user-arg   = { MYFUNC($arg) }
        """))

    def test_defaults(self):
        val, errs = self.ctx.format('pass-arg', {})
        self.assertEqual(self.args_passed,
                         [("a", None, "default")])
        self.assertEqual(len(errs), 0)

    def test_pass_kwarg1(self):
        val, errs = self.ctx.format('pass-kwarg1', {})
        self.assertEqual(self.args_passed,
                         [("a", 1, "default")])
        self.assertEqual(len(errs), 0)

    def test_pass_kwarg2(self):
        val, errs = self.ctx.format('pass-kwarg2', {})
        self.assertEqual(self.args_passed,
                         [("a", None, "other")])
        self.assertEqual(len(errs), 0)

    def test_pass_kwargs(self):
        val, errs = self.ctx.format('pass-kwargs', {})
        self.assertEqual(self.args_passed,
                         [("a", 1, "other")])
        self.assertEqual(len(errs), 0)

    def test_missing_arg(self):
        val, errs = self.ctx.format('pass-user-arg', {})
        self.assertEqual(self.args_passed,
                         [(FluentNone('arg'), None, "default")])
        self.assertEqual(len(errs), 1)
