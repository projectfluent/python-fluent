from __future__ import absolute_import, unicode_literals

import unittest

from fluent.runtime.utils import inspect_function_args, Any
from fluent.runtime.errors import FluentFormatError


class TestInspectFunctionArgs(unittest.TestCase):

    def test_inspect_function_args_positional(self):
        self.assertEqual(inspect_function_args(lambda: None, 'name', []),
                         (0, []))
        self.assertEqual(inspect_function_args(lambda x: None, 'name', []),
                         (1, []))
        self.assertEqual(inspect_function_args(lambda x, y: None, 'name', []),
                         (2, []))

    def test_inspect_function_args_var_positional(self):
        self.assertEqual(inspect_function_args(lambda *args: None, 'name', []),
                         (Any, []))

    def test_inspect_function_args_keywords(self):
        self.assertEqual(inspect_function_args(lambda x, y=1, z=2: None, 'name', []),
                         (1, ['y', 'z']))

    def test_inspect_function_args_var_keywords(self):
        self.assertEqual(inspect_function_args(lambda x, **kwargs: None, 'name', []),
                         (1, Any))

    def test_inspect_function_args_var_positional_plus_keywords(self):
        self.assertEqual(inspect_function_args(lambda x, y=1, *args: None, 'name', []),
                         (Any, ['y']))

    def test_inspect_function_args_bad_keyword_args(self):
        def foo():
            pass
        foo.ftl_arg_spec = (0, ['bad-kwarg', 'good'])
        errors = []
        self.assertEqual(inspect_function_args(foo, 'FOO', errors),
                         (0, ['good']))
        self.assertEqual(errors,
                         [FluentFormatError("FOO() has invalid keyword argument name 'bad-kwarg'")])
