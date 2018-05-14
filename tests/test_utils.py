from __future__ import absolute_import, unicode_literals

import unittest

from fluent.utils import cachedproperty


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
