from __future__ import absolute_import, unicode_literals

import unittest

from fluent.utils import cachedproperty, inspect_function_args, Any


class TestCachedProperty(unittest.TestCase):
    def test_cachedproperty(self):

        class Foo(object):
            def __init__(self):
                self.my_property_call_count = 0

            @cachedproperty
            def my_property(self):
                self.my_property_call_count += 1
                return "Expensive result"

        foo = Foo()
        self.assertEqual(foo.my_property_call_count, 0)
        self.assertEqual(foo.my_property, "Expensive result")
        self.assertEqual(foo.my_property_call_count, 1)

        # Asking again uses cached value:
        self.assertEqual(foo.my_property, "Expensive result")
        self.assertEqual(foo.my_property_call_count, 1)

        # But we can delete and run it again.
        del foo.my_property
        self.assertEqual(foo.my_property, "Expensive result")
        self.assertEqual(foo.my_property_call_count, 2)

    def test_inspect_function_args_positional(self):
        self.assertEqual(inspect_function_args(lambda: None),
                         (0, []))
        self.assertEqual(inspect_function_args(lambda x: None),
                         (1, []))
        self.assertEqual(inspect_function_args(lambda x, y: None),
                         (2, []))

    def test_inspect_function_args_var_positional(self):
        self.assertEqual(inspect_function_args(lambda *args: None),
                         (Any, []))

    def test_inspect_function_args_keywords(self):
        self.assertEqual(inspect_function_args(lambda x, y=1, z=2: None),
                         (1, ['y', 'z']))

    def test_inspect_function_args_var_keywords(self):
        self.assertEqual(inspect_function_args(lambda x, **kwargs: None),
                         (1, Any))

    def test_inspect_function_args_var_positional_plus_keywords(self):
        self.assertEqual(inspect_function_args(lambda x, y=1, *args: None),
                         (Any, ['y']))
