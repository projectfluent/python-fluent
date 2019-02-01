# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import ast
import sys
import textwrap
import unittest

from ast_decompiler import decompiler
from hypothesis import given
from hypothesis.strategies import text

from fluent.runtime import codegen
from fluent.runtime.utils import allowable_name


def normalize_python(txt):
    return textwrap.dedent(txt.rstrip()).strip()


class TestDecompiler(decompiler.Decompiler):
    if sys.version_info < (3, 0):
        # We override one bit of behaviour to make Python 2 testing simpler.

        # We don't need 'u' prefixes on strings because we are using from
        # __future__ import unicode_literals. Therefore we omit them in the
        # decompiled output. This function is copy-pasted from Decompiler.
        # with just the unicode branch changed.

        def visit_Str(self, node):
            if sys.version_info < (3, 0):
                if self.has_unicode_literals and isinstance(node.s, str):
                    self.write('b')
                # REMOVED
                # elif isinstance(node.s, unicode):
                #     self.write('u')
            if sys.version_info >= (3, 6) and self.has_parent_of_type(ast.FormattedValue):
                delimiter = '"'
            else:
                delimiter = "'"
            self.write(delimiter)
            s = node.s.encode('unicode-escape').decode('ascii')
            self.write(s.replace(delimiter, '\\' + delimiter))
            self.write(delimiter)


def decompile(ast, indentation=4, line_length=100, starting_indentation=0):
    """Decompiles an AST into Python code.
    """
    decompiler = TestDecompiler(
        indentation=indentation,
        line_length=line_length,
        starting_indentation=starting_indentation,
    )
    return decompiler.run(ast)


def decompile_ast_list(ast_list):
    return decompile(ast.Module(body=ast_list,
                                **codegen.DEFAULT_AST_ARGS))


def as_source_code(codegen_ast):
    if not hasattr(codegen_ast, 'as_ast'):
        ast_list = codegen_ast.as_ast_list()
    else:
        ast_list = [codegen_ast.as_ast()]
    return decompile_ast_list(ast_list)


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
                                parent_scope=module.scope)
        self.assertCodeEqual(as_source_code(func), """
            def myfunc(myarg1, myarg2):
                pass
        """)

    def test_function_return(self):
        module = codegen.Module()
        func = codegen.Function('myfunc',
                                parent_scope=module)
        func.add_return(codegen.String("Hello"))
        self.assertCodeEqual(as_source_code(func), """
            def myfunc():
                return 'Hello'
        """)

    def test_function_bad_name(self):
        module = codegen.Module()
        func = codegen.Function('my func', args=[],
                                parent_scope=module)
        self.assertRaises(AssertionError, as_source_code, func)

    def test_function_bad_arg(self):
        module = codegen.Module()
        func = codegen.Function('myfunc', args=['my arg'],
                                parent_scope=module.scope)
        self.assertRaises(AssertionError, as_source_code, func)

    def test_add_function(self):
        module = codegen.Module()
        func_name = module.scope.reserve_name('myfunc')
        func = codegen.Function(func_name,
                                parent_scope=module)
        module.add_function(func_name, func)
        self.assertCodeEqual(as_source_code(module), """
            def myfunc():
                pass
        """)

    def test_variable_reference(self):
        scope = codegen.Scope()
        name = scope.reserve_name('name')
        ref = codegen.VariableReference(name, scope)
        self.assertEqual(as_source_code(ref), 'name')

    def test_variable_reference_check(self):
        scope = codegen.Scope()
        self.assertRaises(AssertionError,
                          codegen.VariableReference,
                          'name',
                          scope)

    def test_variable_reference_function_arg_check(self):
        scope = codegen.Scope()
        func_name = scope.reserve_name('myfunc')
        func = codegen.Function(func_name, args=['my_arg'],
                                parent_scope=scope)
        # Can't use undefined 'some_name'
        self.assertRaises(AssertionError,
                          codegen.VariableReference,
                          'some_name',
                          func)
        # But can use function argument 'my_arg'
        ref = codegen.VariableReference('my_arg', func)
        self.assertCodeEqual(as_source_code(ref), 'my_arg')

    def test_variable_reference_bad(self):
        module = codegen.Module()
        name = module.scope.reserve_name('name')
        ref = codegen.VariableReference(name, module.scope)
        ref.name = 'bad name'
        self.assertRaises(AssertionError, as_source_code, ref)

    def test_scope_variable_helper(self):
        # Scope.variable is more convenient than using VariableReference
        # manually, we use that from now on.
        scope = codegen.Scope()
        name = scope.reserve_name('name')
        ref1 = codegen.VariableReference(name, scope)
        ref2 = scope.variable(name)
        self.assertEqual(ref1, ref2)

    def test_function_args_name_check(self):
        module = codegen.Module()
        module.scope.reserve_name('my_arg')
        func_name = module.scope.reserve_name('myfunc')
        self.assertRaises(AssertionError,
                          codegen.Function,
                          func_name, args=['my_arg'],
                          parent_scope=module.scope)

    def test_function_args_name_reserved_check(self):
        module = codegen.Module()
        module.scope.reserve_function_arg_name('my_arg')
        func_name = module.scope.reserve_name('myfunc')
        func = codegen.Function(func_name, args=['my_arg'],
                                parent_scope=module.scope)
        func.add_return(func.variable('my_arg'))
        self.assertCodeEqual(as_source_code(func), """
            def myfunc(my_arg):
                return my_arg
        """)

    def test_add_assignment_unreserved(self):
        scope = codegen.Module()
        self.assertRaises(AssertionError,
                          scope.add_assignment,
                          'x',
                          codegen.String('a string'))

    def test_add_assignment_reserved(self):
        module = codegen.Module()
        name = module.scope.reserve_name('x')
        module.add_assignment(name, codegen.String('a string'))
        self.assertCodeEqual(as_source_code(module), """
            x = 'a string'
        """)

    def test_add_assignment_bad(self):
        module = codegen.Module()
        name = module.scope.reserve_name('x')
        module.add_assignment(name, codegen.String('a string'))
        # We have to modify internals to force the error path, because
        # add_assignment already does checking
        module.statements[0].name = 'something with a space'
        self.assertRaises(AssertionError,
                          as_source_code, module)

    def test_multiple_add_assignment(self):
        # To make our code generation easier to reason about, we disallow
        # assigning to same name twice. We can add trimming of unneeded
        # temporaries as a later pass.
        module = codegen.Module()
        name = module.scope.reserve_name('x')
        module.add_assignment(name, codegen.String('a string'))
        self.assertRaises(AssertionError,
                          module.add_assignment,
                          name, codegen.String('another string'))

    def test_multiple_add_assignment_in_inherited_scope(self):
        # try/if etc inherit their scope from function
        scope = codegen.Scope()
        scope.reserve_name('myfunc')
        func = codegen.Function('myfunc',
                                args=[],
                                parent_scope=scope)
        try_ = codegen.Try([], func)
        name = func.reserve_name('name')

        # We'd really like to ensure no multiple assignments ever,
        # but the way that if/try etc. work make that hard.
        # Instead, we add a keyword argument to allow the second assignment.
        try_.try_block.add_assignment(name, codegen.Number(1))
        self.assertRaises(AssertionError,
                          try_.try_block.add_assignment,
                          name, codegen.Number(2))
        self.assertRaises(AssertionError,
                          try_.except_block.add_assignment,
                          name, codegen.Number(2))
        try_.except_block.add_assignment(name, codegen.Number(2),
                                         allow_multiple=True)

    def test_function_call_unknown(self):
        scope = codegen.Scope()
        self.assertRaises(AssertionError,
                          codegen.FunctionCall,
                          'a_function',
                          [],
                          {},
                          scope)

    def test_function_call_known(self):
        module = codegen.Module()
        module.scope.reserve_name('a_function')
        func_call = codegen.FunctionCall('a_function', [], {}, module.scope)
        self.assertCodeEqual(as_source_code(func_call), "a_function()")

    def test_function_call_args_and_kwargs(self):
        module = codegen.Module()
        module.scope.reserve_name('a_function')
        func_call = codegen.FunctionCall('a_function', [codegen.Number(123)], {'x': codegen.String("hello")},
                                         module.scope)
        self.assertCodeEqual(as_source_code(func_call), "a_function(123, x='hello')")

    def test_function_call_bad_name(self):
        module = codegen.Module()
        module.scope.reserve_name('a_function')
        func_call = codegen.FunctionCall('a_function', [], {}, module.scope)
        func_call.function_name = 'bad function name'
        self.assertRaises(AssertionError, as_source_code, func_call)

    def test_function_call_bad_kwarg_names(self):
        module = codegen.Module()
        module.scope.reserve_name('a_function')
        allowed_args = [
            # (name, allowed) pairs.
            # We allow reserved names etc. because we can
            # call these using **{} syntax
            ('hyphen-ated', True),
            ('class', True),
            ('True', True),
            (' pre_space', False),
            ('post_space ', False),
            ('mid space', False),
            ('valid_arg', True),
        ]
        for arg_name, allowed in allowed_args:
            func_call = codegen.FunctionCall('a_function', [],
                                             {arg_name: codegen.String("a")},
                                             module.scope)
            if allowed:
                output = as_source_code(func_call)
                self.assertNotEqual(output, '')
                if not allowable_name(arg_name):
                    self.assertIn('**{', output)
            else:
                self.assertRaises(AssertionError, as_source_code, func_call)

    def test_function_call_sensitive(self):
        module = codegen.Module()
        module.scope.reserve_name('a_function')
        func_call = codegen.FunctionCall('a_function', [], {}, module.scope)
        # codegen should refuse to create a call to 'exec', there is no reason
        # for us to generate code like that.
        func_call.function_name = 'exec'
        self.assertRaises(AssertionError, as_source_code, func_call)

    def test_method_call_bad_name(self):
        scope = codegen.Module()
        s = codegen.String("x")
        method_call = codegen.MethodCall(s, 'bad method name', [], scope)
        self.assertRaises(AssertionError, as_source_code, method_call)

    def test_try_catch(self):
        scope = codegen.Scope()
        scope.reserve_name('MyError')
        try_ = codegen.Try([scope.variable('MyError')], scope)
        self.assertCodeEqual(as_source_code(try_), """
            try:
                pass
            except MyError:
                pass
        """)
        scope.reserve_name('x')
        scope.reserve_name('y')
        scope.reserve_name('z')
        try_.try_block.add_assignment('x', codegen.String("x"))
        try_.except_block.add_assignment('y', codegen.String("y"))
        try_.else_block.add_assignment('z', codegen.String("z"))
        self.assertCodeEqual(as_source_code(try_), """
            try:
                x = 'x'
            except MyError:
                y = 'y'
            else:
                z = 'z'
        """)

    def test_try_catch_multiple_exceptions(self):
        scope = codegen.Scope()
        scope.reserve_name('MyError')
        scope.reserve_name('OtherError')
        try_ = codegen.Try([scope.variable('MyError'),
                            scope.variable('OtherError')], scope)
        self.assertCodeEqual(as_source_code(try_), """
            try:
                pass
            except (MyError, OtherError):
                pass
        """)

    def test_if_empty(self):
        scope = codegen.Module()
        if_statement = codegen.If(scope)
        self.assertCodeEqual(as_source_code(if_statement), "")

    def test_if_one_if(self):
        scope = codegen.Module()
        if_statement = codegen.If(scope)
        first_block = if_statement.add_if(codegen.Number(1))
        first_block.add_return(codegen.Number(2))
        self.assertCodeEqual(as_source_code(if_statement), """
            if 1:
                return 2
        """)

    def test_if_two_ifs(self):
        scope = codegen.Module()
        if_statement = codegen.If(scope)
        first_block = if_statement.add_if(codegen.Number(1))
        first_block.add_return(codegen.Number(2))
        second_block = if_statement.add_if(codegen.Number(3))
        second_block.add_return(codegen.Number(4))
        self.assertCodeEqual(as_source_code(if_statement), """
            if 1:
                return 2
            elif 3:
                return 4
        """)

    def test_if_with_else(self):
        scope = codegen.Module()
        if_statement = codegen.If(scope)
        first_block = if_statement.add_if(codegen.Number(1))
        first_block.add_return(codegen.Number(2))
        if_statement.else_block.add_return(codegen.Number(3))
        self.assertCodeEqual(as_source_code(if_statement), """
            if 1:
                return 2
            else:
                return 3
        """)

    def test_if_no_ifs(self):
        scope = codegen.Module()
        if_statement = codegen.If(scope)
        if_statement.else_block.add_return(codegen.Number(3))
        if_statement = codegen.simplify(if_statement)
        self.assertCodeEqual(as_source_code(if_statement), """
            return 3
        """)

    @given(text())
    def test_string(self, t):
        self.assertEqual(t, eval(as_source_code(codegen.String(t))), " for t = {!r}".format(t))

    def test_string_join_empty(self):
        join = codegen.StringJoin([])
        join = codegen.simplify(join)
        self.assertCodeEqual(as_source_code(join), "''")

    def test_string_join_one(self):
        join = codegen.StringJoin([codegen.String('hello')])
        join = codegen.simplify(join)
        self.assertCodeEqual(as_source_code(join), "'hello'")

    def test_string_join_two(self):
        module = codegen.Module()
        module.scope.reserve_name('tmp')
        var = module.scope.variable('tmp')
        join = codegen.StringJoin([codegen.String('hello '), var])
        self.assertCodeEqual(as_source_code(join), "''.join(['hello ', tmp])")

    def test_string_join_collapse_strings(self):
        scope = codegen.Scope()
        scope.reserve_name('tmp')
        var = scope.variable('tmp')
        join1 = codegen.StringJoin([codegen.String('hello '),
                                    codegen.String('there '),
                                    var,
                                    codegen.String(' how'),
                                    codegen.String(' are you?'),
                                    ])
        join1 = codegen.simplify(join1)
        self.assertCodeEqual(as_source_code(join1), "''.join(['hello there ', tmp, ' how are you?'])")

    def test_cleanup_name(self):
        for n, c in [('abc-def()[]ghi,.<>¡!?¿', 'abcdefghi'),  # illegal chars
                     ('1abc', 'n1abc'),  # leading digit
                     ('_allowed', '_allowed'),  # leading _ (which is allowed)
                     ('-', 'n')  # empty after removing illegals
                     ]:
            self.assertEqual(codegen.cleanup_name(n), c)

    @given(text())
    def test_cleanup_name_not_empty(self, t):
        self.assertTrue(len(codegen.cleanup_name(t)) > 0, " for t = {!r}".format(t))

    @given(text())
    def test_cleanup_name_allowed_identifier(self, t):
        self.assertTrue(allowable_name(codegen.cleanup_name(t)), " for t = {!r}".format(t))

    def test_dict_lookup(self):
        scope = codegen.Scope()
        scope.reserve_name('tmp')
        var = scope.variable('tmp')
        lookup = codegen.DictLookup(var, codegen.String('x'))
        self.assertCodeEqual(as_source_code(lookup), "tmp['x']")

    def test_equals(self):
        eq = codegen.Equals(codegen.String('x'), codegen.String('y'))
        self.assertCodeEqual(as_source_code(eq), "'x' == 'y'")

    def test_or(self):
        or_ = codegen.Or(codegen.String('x'), codegen.String('y'))
        self.assertCodeEqual(as_source_code(or_), "'x' or 'y'")
