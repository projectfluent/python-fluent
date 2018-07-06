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

    def test_reserve_name_function_arg_disallowed(self):
        scope = codegen.Scope()
        scope.reserve_name('name')
        self.assertRaises(AssertionError,
                          scope.reserve_name,
                          'name',
                          function_arg=True)

    def test_reserve_name_function_arg(self):
        scope = codegen.Scope()
        scope.reserve_function_arg_name('arg_name')
        scope.reserve_name('myfunc')
        func = codegen.Function('myfunc',
                                args=['arg_name'],
                                parent_scope=scope)
        self.assertNotIn('arg_name2', func.all_reserved_names())

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

    def test_reserve_name_after_reserve_function_arg(self):
        scope = codegen.Scope()
        scope.reserve_function_arg_name('my_arg')
        name = scope.reserve_name('my_arg')
        self.assertEqual(name, 'my_arg2')

    def test_reserve_function_arg_after_reserve_name(self):
        scope = codegen.Scope()
        scope.reserve_name('my_arg')
        self.assertRaises(AssertionError,
                          scope.reserve_function_arg_name,
                          'my_arg')

    def test_name_properties(self):
        scope = codegen.Scope()
        scope.reserve_name('name', properties={'FOO': True})
        self.assertEqual(scope.get_name_properties('name'),
                         {'FOO': True})

    def test_function(self):
        module = codegen.Module()
        func = codegen.Function('myfunc', args=['myarg1', 'myarg2'],
                                parent_scope=module)
        self.assertCodeEqual(func.as_source_code(), """
            def myfunc(myarg1, myarg2):
                pass
        """)

    def test_function_kwargs(self):
        module = codegen.Module()
        func = codegen.Function('myfunc', args=['myarg1'], kwargs={'myarg2': codegen.NoneExpr()},
                                parent_scope=module)
        self.assertCodeEqual(func.as_source_code(), """
            def myfunc(myarg1, myarg2=None):
                pass
        """)

    def test_function_return(self):
        module = codegen.Module()
        func = codegen.Function('myfunc',
                                parent_scope=module)
        func.add_return(codegen.String("Hello"))
        self.assertCodeEqual(func.as_source_code(), """
            def myfunc():
                return 'Hello'
        """)

    def test_add_function(self):
        module = codegen.Module()
        func_name = module.reserve_name('myfunc')
        func = codegen.Function(func_name,
                                parent_scope=module)
        module.add_function(func_name, func)
        self.assertCodeEqual(module.as_source_code(), """
            def myfunc():
                pass
        """)

    def test_variable_reference(self):
        module = codegen.Module()
        name = module.reserve_name('name')
        ref = codegen.VariableReference(name, module)
        self.assertEqual(ref.as_source_code(), 'name')

    def test_variable_reference_check(self):
        module = codegen.Module()
        self.assertRaises(AssertionError,
                          codegen.VariableReference,
                          'name',
                          module)

    def test_variable_reference_function_arg_check(self):
        module = codegen.Module()
        func_name = module.reserve_name('myfunc')
        func = codegen.Function(func_name, args=['my_arg'],
                                parent_scope=module)
        # Can't use undefined 'some_name'
        self.assertRaises(AssertionError,
                          codegen.VariableReference,
                          'some_name',
                          func)
        # But can use function argument 'my_arg'
        ref = codegen.VariableReference('my_arg', func)
        self.assertCodeEqual(ref.as_source_code(), 'my_arg')

    def test_function_args_name_check(self):
        module = codegen.Module()
        module.reserve_name('my_arg')
        func_name = module.reserve_name('myfunc')
        self.assertRaises(AssertionError,
                          codegen.Function,
                          func_name, args=['my_arg'],
                          parent_scope=module)

    def test_function_args_name_reserved_check(self):
        module = codegen.Module()
        module.reserve_function_arg_name('my_arg')
        func_name = module.reserve_name('myfunc')
        func = codegen.Function(func_name, args=['my_arg'],
                                parent_scope=module)
        func.add_return(codegen.VariableReference('my_arg', func))
        self.assertCodeEqual(func.as_source_code(), """
            def myfunc(my_arg):
                return my_arg
        """)

    def test_add_assignment_unreserved(self):
        scope = codegen.Scope()
        self.assertRaises(AssertionError,
                          scope.add_assignment,
                          'x',
                          codegen.String('a string'))

    def test_add_assignment_reserved(self):
        scope = codegen.Scope()
        name = scope.reserve_name('x')
        scope.add_assignment(name, codegen.String('a string'))
        self.assertCodeEqual(scope.as_source_code(), """
            x = 'a string'
        """)

    def test_add_assignment_multi(self):
        scope = codegen.Scope()
        name1 = scope.reserve_name('x')
        name2 = scope.reserve_name('y')
        scope.add_assignment((name1, name2), codegen.Tuple(codegen.String('a string'), codegen.String('another')))
        self.assertCodeEqual(scope.as_source_code(), """
            x, y = ('a string', 'another')
        """)

    def test_function_call_unknown(self):
        scope = codegen.Scope()
        self.assertRaises(AssertionError,
                          codegen.FunctionCall,
                          'a_function',
                          [],
                          {},
                          scope)

    def test_function_call_known(self):
        scope = codegen.Scope()
        scope.reserve_name('a_function')
        func_call = codegen.FunctionCall('a_function', [], {}, scope)
        self.assertCodeEqual(func_call.as_source_code(), "a_function()")

    def test_function_call_args_and_kwargs(self):
        scope = codegen.Scope()
        scope.reserve_name('a_function')
        func_call = codegen.FunctionCall('a_function', [codegen.Number(123)], {'x': codegen.String("hello")}, scope)
        self.assertCodeEqual(func_call.as_source_code(), "a_function(123, x='hello')")

    def test_try_catch(self):
        scope = codegen.Scope()
        scope.reserve_name('MyError')
        t = codegen.TryCatch(codegen.VariableReference('MyError', scope), scope)
        self.assertCodeEqual(t.as_source_code(), """
            try:
                pass
            except MyError:
                pass
        """)
        scope.reserve_name('x')
        t.try_block.add_assignment('x', codegen.String("x"))
        t.except_block.add_assignment('x', codegen.String("y"))
        t.else_block.add_assignment('x', codegen.String("z"))
        self.assertCodeEqual(t.as_source_code(), """
            try:
                x = 'x'
            except MyError:
                x = 'y'
            else:
                x = 'z'
        """)

    def test_if_empty(self):
        scope = codegen.Scope()
        if_statement = codegen.If(scope)
        self.assertCodeEqual(if_statement.as_source_code(), "")

    def test_if_one_if(self):
        scope = codegen.Scope()
        if_statement = codegen.If(scope)
        first_block = if_statement.add_if(codegen.Number(1))
        first_block.statements.append(codegen.Return(codegen.Number(2)))
        self.assertCodeEqual(if_statement.as_source_code(), """
            if 1:
                return 2
        """)

    def test_if_two_ifs(self):
        scope = codegen.Scope()
        if_statement = codegen.If(scope)
        first_block = if_statement.add_if(codegen.Number(1))
        first_block.statements.append(codegen.Return(codegen.Number(2)))
        second_block = if_statement.add_if(codegen.Number(3))
        second_block.statements.append(codegen.Return(codegen.Number(4)))
        self.assertCodeEqual(if_statement.as_source_code(), """
            if 1:
                return 2
            elif 3:
                return 4
        """)

    def test_if_with_else(self):
        scope = codegen.Scope()
        if_statement = codegen.If(scope)
        first_block = if_statement.add_if(codegen.Number(1))
        first_block.statements.append(codegen.Return(codegen.Number(2)))
        if_statement.else_block.statements.append(codegen.Return(codegen.Number(3)))
        self.assertCodeEqual(if_statement.as_source_code(), """
            if 1:
                return 2
            else:
                return 3
        """)

    def test_if_no_ifs(self):
        scope = codegen.Scope()
        if_statement = codegen.If(scope)
        if_statement.else_block.statements.append(codegen.Return(codegen.Number(3)))
        self.assertCodeEqual(if_statement.as_source_code(), """
            return 3
        """)
