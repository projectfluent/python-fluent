from __future__ import absolute_import, unicode_literals

import unittest

from fluent.exceptions import FluentReferenceError
from fluent.types import FluentNone, fluent_number

from .. import all_message_context_implementations
from ..syntax import dedent_ftl


@all_message_context_implementations
class TestFunctionCalls(unittest.TestCase):

    def setUp(self):
        self.ctx = self.message_context_cls(['en-US'], use_isolating=False,
                                            functions={'IDENTITY': lambda x: x})
        self.ctx.add_messages(dedent_ftl("""
            foo = Foo
                .attr = Attribute
            pass-nothing       = { IDENTITY() }
            pass-string        = { IDENTITY("a") }
            pass-number        = { IDENTITY(1) }
            pass-message       = { IDENTITY(foo) }
            pass-attr          = { IDENTITY(foo.attr) }
            pass-external      = { IDENTITY($ext) }
            pass-function-call = { IDENTITY(IDENTITY(1)) }
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

    def test_wrong_arity(self):
        val, errs = self.ctx.format('pass-nothing', {})
        self.assertEqual(val, "IDENTITY()")
        self.assertEqual(len(errs), 1)
        self.assertEqual(type(errs[0]), TypeError)


@all_message_context_implementations
class TestMissing(unittest.TestCase):

    def setUp(self):
        self.ctx = self.message_context_cls(['en-US'], use_isolating=False)
        self.ctx.add_messages(dedent_ftl("""
            missing = { MISSING(1) }
        """))

    def test_falls_back_to_name_of_function(self):
        val, errs = self.ctx.format("missing", {})
        self.assertEqual(val, "MISSING()")
        self.assertEqual(errs,
                         [FluentReferenceError("Unknown function: MISSING")])


@all_message_context_implementations
class TestResolving(unittest.TestCase):

    def setUp(self):
        self.args_passed = []

        def number_processor(number):
            self.args_passed.append(number)
            return number

        self.ctx = self.message_context_cls(['en-US'], use_isolating=False,
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


@all_message_context_implementations
class TestKeywordArgs(unittest.TestCase):

    def setUp(self):
        self.args_passed = []

        def my_function(arg, kwarg1=None, kwarg2="default"):
            self.args_passed.append((arg, kwarg1, kwarg2))
            return arg

        self.ctx = self.message_context_cls(['en-US'], use_isolating=False,
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
