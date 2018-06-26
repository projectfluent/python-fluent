from __future__ import absolute_import, unicode_literals

import textwrap
import unittest

from fluent import codegen


def normalize_python(text):
    return textwrap.dedent(text.rstrip()).strip()


class TestCodeGen(unittest.TestCase):

    def assertCodeEqual(self, code1, code2):
        self.assertEqual(normalize_python(code1),
                         normalize_python(code2))

    def test_reserve_name(self):
        scope = codegen.Scope()
        name1 = scope.reserve_name('name')
        name2 = scope.reserve_name('name')
        self.assertEqual(name1, 'name')
        self.assertNotEqual(name1, name2)
        self.assertEqual(name2, 'name2')

    def test_reserve_name_nested(self):
        parent = codegen.Scope()
        parent_name = parent.reserve_name('name')
        self.assertEqual(parent_name, 'name')

        child1 = codegen.Scope(parent_scope=parent)
        child2 = codegen.Scope(parent_scope=parent)

        child1_name = child1.reserve_name('name')
        self.assertNotEqual(child1_name, parent_name)

        child2_name = child2.reserve_name('name')
        self.assertNotEqual(child2_name, parent_name)

        # But children can have same names, they don't shadow each other.
        # To be deterministic, we expect the same name
        self.assertEqual(child1_name, child2_name)

    def test_function(self):
        module = codegen.Module()
        func = codegen.Function('myfunc', ['myarg1', 'myarg2'],
                                parent_scope=module)
        self.assertCodeEqual(func.as_source_code(),
                             """
                             def myfunc(myarg1, myarg2):
                                 pass
                             """)

    def test_function_return(self):
        module = codegen.Module()
        func = codegen.Function('myfunc', [],
                                parent_scope=module)
        func.add_return(codegen.String("Hello"))
        self.assertCodeEqual(func.as_source_code(),
                             """
                             def myfunc():
                                 return 'Hello'
                             """)

    def test_add_function(self):
        module = codegen.Module()
        func_name = module.reserve_name('myfunc')
        func = codegen.Function(func_name, [],
                                parent_scope=module)
        module.add_function(func_name, func)
        self.assertCodeEqual(module.as_source_code(),
                             """
                             def myfunc():
                                 pass
                             """)
