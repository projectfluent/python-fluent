"""
Utilities for doing Python code generation
"""
from __future__ import absolute_import, unicode_literals

import keyword
import re
import sys

from six import text_type

from . import ast_compat as ast
from .utils import allowable_keyword_arg_name, allowable_name

# This module provides simple utilities for building up Python source code. It
# implements only what is really needed by compiler.py, with a number of aims
# and constraints:
#
# 1. Performance.
#
#    The resulting Python code should do as little as possible, especially for
#    simple cases (which are by far the most common for .ftl files)
#
# 2. Correctness (obviously)
#
#    In particular, we should try to make it hard to generate code that is
#    syntactically correct and therefore compiles but doesn't work. We try to
#    make it hard to generate accidental name clashes, or use variables that are
#    not defined.
#
#    Correctness also has a security implication, since the result of this code
#    is 'exec'ed. To that end:
#     * We build up AST, rather than strings. This eliminates many
#       potential bugs caused by wrong escaping/interpolation.
#     * the `as_ast()` methods are paranoid about input, and do many asserts.
#       We do this even though other layers will usually have checked the
#       input, to allow us to reason locally when checking these methods. These
#       asserts must also have 100% code coverage.
#
# 3. Simplicity
#
#    The resulting Python code should be easy to read and understand.
#
# 4. Predictability
#
#    Since we want to test the resulting source code, we have made some design
#    decisions that aim to ensure things like function argument names are
#    consistent and so can be predicted easily.


PROPERTY_TYPE = 'PROPERTY_TYPE'
PROPERTY_RETURN_TYPE = 'PROPERTY_RETURN_TYPE'
UNKNOWN_TYPE = object
SENSITIVE_FUNCTIONS = [
    # builtin functions that we should never be calling from our code
    # generation. This is a defense-in-depth mechansim to stop our code
    # generation become a code exectution vulnerability, we also have
    # higher level code that ensures we are not generating calls
    # to arbitrary Python functions.

    # This is not a comprehensive list of functions we are not using, but
    # functions we definitly don't need and are most likely to be used to
    # execute remote code or to get around safety mechanisms.
    '__import__',
    '__build_class__',
    'apply',
    'compile',
    'eval',
    'exec',
    'execfile',
    'exit',
    'file',
    'globals',
    'locals',
    'open',
    'object',
    'reload',
    'type',
]


class PythonAst(object):
    """
    Base class representing a simplified Python AST (not the real one).
    Generates real `ast.*` nodes via `as_ast()` method.
    """
    def simplify(self, changes, simplifier):
        """
        Simplify the statement/expression, returning either a modified
        self, or a new object.

        This method should call .simplify(changes) on any contained subexpressions
        or statements.

        If changes were made, a True value must be appended to the passed in changes list.

        It should also run the callable simplifier on any returned values (this
        is an externally passed in function that may do additional higher level
        simplifications)

        """
        return self

    def as_ast(self):
        raise NotImplementedError("{!r}.as_ast()".format(self.__class__))


class PythonAstList(object):
    """
    Alternative base class to PythonAst when we have code that wants to return a
    list of AST objects.
    """
    def as_ast_list(self):
        raise NotImplementedError("{!r}.as_ast_list()".format(self.__class__))


# `compiler` needs these attributes on AST nodes.
# We don't have anything sensible we can put here so we put arbitrary values.
DEFAULT_AST_ARGS = dict(lineno=1, col_offset=1)


class Scope(object):
    def __init__(self, parent_scope=None):
        self.parent_scope = parent_scope
        self.names = set()
        self._function_arg_reserved_names = set()
        self._properties = {}
        self._assignments = {}

    def names_in_use(self):
        names = self.names
        if self.parent_scope is not None:
            names = names | self.parent_scope.names_in_use()
        return names

    def function_arg_reserved_names(self):
        names = self._function_arg_reserved_names
        if self.parent_scope is not None:
            names = names | self.parent_scope.function_arg_reserved_names()
        return names

    def all_reserved_names(self):
        return self.names_in_use() | self.function_arg_reserved_names()

    def reserve_name(self, requested, function_arg=False, is_builtin=False, properties=None):
        """
        Reserve a name as being in use in a scope.

        Pass function_arg=True if this is a function argument.
        'properties' is an optional dict of additional properties
        (e.g. the type associated with a name)
        """
        def _add(final):
            self.names.add(final)
            self._properties[final] = properties or {}
            return final

        if function_arg:
            if requested in self.function_arg_reserved_names():
                assert requested not in self.names_in_use()
                return _add(requested)
            if requested in self.all_reserved_names():
                raise AssertionError("Cannot use '{0}' as argument name as it is already in use"
                                     .format(requested))

        cleaned = cleanup_name(requested)

        attempt = cleaned
        count = 2  # instance without suffix is regarded as 1
        # To avoid shadowing of global names in local scope, we
        # take into account parent scope when assigning names.

        used = self.all_reserved_names()
        # We need to also protect against using keywords ('class', 'def' etc.)
        # However, some builtins are also keywords (e.g. 'None'), and so
        # if a builtin is being reserved, don't check against the keyword list
        if not is_builtin:
            used = used | set(keyword.kwlist)
        while attempt in used:
            attempt = cleaned + str(count)
            count += 1
        return _add(attempt)

    def reserve_function_arg_name(self, name):
        """
        Reserve a name for *later* use as a function argument. This does not result
        in that name being considered 'in use' in the current scope, but will
        avoid the name being assigned for any use other than as a function argument.
        """
        # To keep things simple, and the generated code predictable, we reserve
        # names for all function arguments in a separate scope, and insist on
        # the exact names
        if name in self.all_reserved_names():
            raise AssertionError("Can't reserve '{0}' as function arg name as it is already reserved"
                                 .format(name))
        self._function_arg_reserved_names.add(name)

    def get_name_properties(self, name):
        """
        Gets a dictionary of properties for the name.
        Raises exception if the name is not reserved in this scope or parent
        """
        if name in self._properties:
            return self._properties[name]
        return self.parent_scope.get_name_properties(name)

    def set_name_properties(self, name, props):
        """
        Sets a dictionary of properties for the name.
        Raises exception if the name is not reserved in this scope or parent.
        """
        scope = self
        while True:
            if name in scope._properties:
                scope._properties[name].update(props)
                break
            else:
                scope = scope.parent_scope

    def find_names_by_property(self, prop_name, prop_val):
        """
        Retrieve all names that match the supplied property name and value
        """
        return [name
                for name, props in self._properties.items()
                for k, v in props.items()
                if k == prop_name and v == prop_val]

    def has_assignment(self, name):
        return name in self._assignments

    def register_assignment(self, name):
        self._assignments[name] = None

    def variable(self, name):
        # Convenience utility for returning a VariableReference
        return VariableReference(name, self)


_IDENTIFIER_SANITIZER_RE = re.compile('[^a-zA-Z0-9_]')
_IDENTIFIER_START_RE = re.compile('^[a-zA-Z_]')


def cleanup_name(name):
    # See https://docs.python.org/2/reference/lexical_analysis.html#grammar-token-identifier
    name = _IDENTIFIER_SANITIZER_RE.sub('', name)
    if not _IDENTIFIER_START_RE.match(name):
        name = "n" + name
    return name


class Statement(object):
    pass


class _Assignment(Statement, PythonAst):
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def as_ast(self):
        if not allowable_name(self.name):
            raise AssertionError("Expected {0} to be a valid Python identifier".format(self.name))
        return ast.Assign(
            targets=[ast.Name(id=self.name,
                              ctx=ast.Store(),
                              **DEFAULT_AST_ARGS)],
            value=self.value.as_ast(),
            **DEFAULT_AST_ARGS)

    def simplify(self, changes, simplifier):
        self.value = self.value.simplify(changes, simplifier)
        return simplifier(self, changes)


class Block(PythonAstList):
    def __init__(self, scope):
        self.scope = scope
        self.statements = []

    def as_ast_list(self, allow_empty=True):
        retval = []
        for s in self.statements:
            if hasattr(s, 'as_ast_list'):
                retval.extend(s.as_ast_list(allow_empty=True))
            else:
                if isinstance(s, Statement):
                    retval.append(s.as_ast())
                else:
                    # Things like bare function/method calls need to be wrapped
                    # in `Expr` to match the way Python parses.
                    retval.append(ast.Expr(s.as_ast(), **DEFAULT_AST_ARGS))

        if len(retval) == 0 and not allow_empty:
            return [ast.Pass(**DEFAULT_AST_ARGS)]
        return retval

    # Safe alternatives to Block.statements being manipulated directly:
    def add_assignment(self, name, value, allow_multiple=False):
        """
        Adds an assigment of the form:

           x = value
        """
        if name not in self.scope.names_in_use():
            raise AssertionError("Cannot assign to unreserved name '{0}'".format(name))

        if self.scope.has_assignment(name):
            if not allow_multiple:
                raise AssertionError("Have already assigned to '{0}' in this scope".format(name))
        else:
            self.scope.register_assignment(name)

        self.statements.append(_Assignment(name, value))

    def add_function(self, func_name, func):
        assert func.func_name == func_name
        self.statements.append(func)

    def add_return(self, value):
        self.statements.append(Return(value))

    def simplify(self, changes, simplifier):
        self.statements = [s.simplify(changes, simplifier) for s in self.statements]
        return simplifier(self, changes)


class Module(Block, PythonAst):
    def __init__(self):
        scope = Scope(parent_scope=None)
        Block.__init__(self, scope)

    def as_ast(self):
        return ast.Module(body=self.as_ast_list(), **DEFAULT_AST_ARGS)


class Function(Scope, Statement, PythonAst):
    def __init__(self, name, args=None, parent_scope=None):
        super(Function, self).__init__(parent_scope=parent_scope)
        self.body = Block(self)
        self.func_name = name
        if args is None:
            args = ()
        for arg in args:
            if (arg in self.names_in_use()):
                raise AssertionError("Can't use '{0}' as function argument name because it shadows other names"
                                     .format(arg))
            self.reserve_name(arg, function_arg=True)
        self.args = args

    def as_ast(self):
        if not allowable_name(self.func_name):
            raise AssertionError("Expected '{0}' to be a valid Python identifier".format(self.func_name))
        for arg in self.args:
            if not allowable_name(arg):
                raise AssertionError("Expected '{0}' to be a valid Python identifier".format(arg))
        return ast.FunctionDef(
            name=self.func_name,
            args=ast.arguments(
                args=([ast.arg(arg=arg_name, annotation=None,
                               **DEFAULT_AST_ARGS)
                       for arg_name in self.args]),
                vararg=None,
                kwonlyargs=[],
                kw_defaults=[],
                kwarg=None,
                defaults=[],
                **DEFAULT_AST_ARGS),
            body=self.body.as_ast_list(allow_empty=False),
            decorator_list=[],
            **DEFAULT_AST_ARGS)

    def add_return(self, value):
        self.body.add_return(value)

    def simplify(self, changes, simplifier):
        self.body = self.body.simplify(changes, simplifier)
        return simplifier(self, changes)


class Return(Statement, PythonAst):
    def __init__(self, value):
        self.value = value

    def as_ast(self):
        return ast.Return(self.value.as_ast(), **DEFAULT_AST_ARGS)

    def simplify(self, changes, simplifier):
        self.value = self.value.simplify(changes, simplifier)
        return simplifier(self, changes)

    def __repr__(self):
        return 'Return({0}'.format(repr(self.value))


class If(Statement, PythonAstList):
    def __init__(self, parent_scope):
        self.if_blocks = []
        self._conditions = []
        self.else_block = Block(parent_scope)
        self._parent_scope = parent_scope

    def add_if(self, condition):
        new_if = Block(self._parent_scope)
        self.if_blocks.append(new_if)
        self._conditions.append(condition)
        return new_if

    # We implement as_ast_list here to allow us to return a list of statements
    # in some cases.
    def as_ast_list(self, allow_empty=True):
        if len(self.if_blocks) == 0:
            return self.else_block.as_ast_list(allow_empty=allow_empty)
        if_ast = ast.If(orelse=[], **DEFAULT_AST_ARGS)
        current_if = if_ast
        previous_if = None
        for condition, if_block in zip(self._conditions, self.if_blocks):
            current_if.test = condition.as_ast()
            current_if.body = if_block.as_ast_list()
            if previous_if is not None:
                previous_if.orelse.append(current_if)

            previous_if = current_if
            current_if = ast.If(orelse=[], **DEFAULT_AST_ARGS)

        if self.else_block.statements:
            previous_if.orelse = self.else_block.as_ast_list()

        return [if_ast]

    def simplify(self, changes, simplifier):
        self.if_blocks = [block.simplify(changes, simplifier) for block in self.if_blocks]
        self._conditions = [expr.simplify(changes, simplifier) for expr in self._conditions]
        self.else_block = self.else_block.simplify(changes, simplifier)
        if not self.if_blocks:
            # Unusual case of no conditions, only default case, but it
            # simplifies other code to be able to handle this uniformly. We can
            # replace this if statement with a single unconditional block.
            changes.append(True)
            return simplifier(self.else_block, changes)
        return simplifier(self, changes)


class Try(Statement, PythonAst):
    def __init__(self, catch_exceptions, parent_scope):
        self.catch_exceptions = catch_exceptions
        self.try_block = Block(parent_scope)
        self.except_block = Block(parent_scope)
        self.else_block = Block(parent_scope)

    def as_ast(self):
        return ast.Try(
            body=self.try_block.as_ast_list(allow_empty=False),
            handlers=[ast.ExceptHandler(
                type=(self.catch_exceptions[0].as_ast()
                      if len(self.catch_exceptions) == 1 else
                      ast.Tuple(elts=[e.as_ast() for e in self.catch_exceptions],
                                ctx=ast.Load(),
                                **DEFAULT_AST_ARGS)),
                name=None,
                body=self.except_block.as_ast_list(allow_empty=False),
                **DEFAULT_AST_ARGS)],
            orelse=self.else_block.as_ast_list(allow_empty=True),
            finalbody=[],
            **DEFAULT_AST_ARGS)

    def simplify(self, changes, simplifier):
        self.catch_exceptions = [e.simplify(changes, simplifier) for e in self.catch_exceptions]
        self.try_block = self.try_block.simplify(changes, simplifier)
        self.except_block = self.except_block.simplify(changes, simplifier)
        self.else_block = self.else_block.simplify(changes, simplifier)
        return simplifier(self, changes)


class Expression(PythonAst):
    # type represents the Python type this expression will produce,
    # if we know it (UNKNOWN_TYPE otherwise).
    type = UNKNOWN_TYPE


class String(Expression):
    type = text_type

    def __init__(self, string_value):
        self.string_value = string_value

    def as_ast(self):
        return ast.Str(self.string_value, **DEFAULT_AST_ARGS)

    def __repr__(self):
        return 'String({0})'.format(repr(self.string_value))

    def __eq__(self, other):
        return isinstance(other, String) and other.string_value == self.string_value

    if sys.version_info < (3,):
        # Python 2 does not implement __ne__ based on __eq__
        def __ne__(self, other):
            return not self == other


class Number(Expression):
    def __init__(self, number):
        self.number = number
        self.type = type(number)

    def as_ast(self):
        return ast.Num(n=self.number, **DEFAULT_AST_ARGS)

    def __repr__(self):
        return 'Number({0})'.format(repr(self.number))


class List(Expression):
    def __init__(self, items):
        self.items = items
        self.type = list

    def as_ast(self):
        return ast.List(
            elts=[i.as_ast() for i in self.items],
            ctx=ast.Load(),
            **DEFAULT_AST_ARGS)

    def simplify(self, changes, simplifier):
        self.items = [item.simplify(changes, simplifier) for item in self.items]
        return simplifier(self, changes)


class Dict(Expression):
    def __init__(self, pairs):
        # pairs is a list of key-value pairs (PythonAst object, PythonAst object)
        self.pairs = pairs
        self.type = dict

    def as_ast(self):
        return ast.Dict(keys=[k.as_ast() for k, v in self.pairs],
                        values=[v.as_ast() for k, v in self.pairs],
                        **DEFAULT_AST_ARGS)

    def simplify(self, changes, simplifier):
        self.pairs = [(k.simplify(changes, simplifier), v.simplify(changes, simplifier))
                      for k, v in self.pairs]
        return simplifier(self, changes)


class StringJoin(Expression):
    type = text_type

    def __init__(self, parts):
        self.parts = parts

    def __repr__(self):
        return 'StringJoin([{0}])'.format(', '.join(repr(p) for p in self.parts))

    def simplify(self, changes, simplifier):
        # Simplify sub parts
        self.parts = [part.simplify(changes, simplifier) for part in self.parts]

        # Merge adjacent String objects.
        new_parts = []
        for part in self.parts:
            if (len(new_parts) > 0 and
                isinstance(new_parts[-1], String) and
                    isinstance(part, String)):
                new_parts[-1] = String(new_parts[-1].string_value +
                                       part.string_value)
            else:
                new_parts.append(part)
        if len(new_parts) < len(self.parts):
            changes.append(True)
        self.parts = new_parts

        # See if we can eliminate the Join altogether
        if len(self.parts) == 0 and self.type is text_type:
            changes.append(True)
            return simplifier(String(''), changes)
        if len(self.parts) == 1:
            changes.append(True)
            return simplifier(self.parts[0], changes)
        return simplifier(self, changes)

    def as_ast(self):
        return MethodCall(String(''), 'join',
                          [List(self.parts)],
                          expr_type=self.type).as_ast()


class VariableReference(Expression):
    def __init__(self, name, scope):
        if name not in scope.names_in_use():
            raise AssertionError("Cannot refer to undefined variable '{0}'".format(name))
        self.name = name
        self.type = scope.get_name_properties(name).get(PROPERTY_TYPE, UNKNOWN_TYPE)

    def as_ast(self):
        if not allowable_name(self.name, allow_builtin=True):
            raise AssertionError("Expected {0} to be a valid Python identifier".format(self.name))
        return ast.Name(id=self.name, ctx=ast.Load(), **DEFAULT_AST_ARGS)

    def __eq__(self, other):
        return type(other) == type(self) and other.name == self.name

    def __repr__(self):
        return 'VariableReference({0})'.format(repr(self.name))


class FunctionCall(Expression):
    def __init__(self, function_name, args, kwargs, scope, expr_type=UNKNOWN_TYPE):
        if function_name not in scope.names_in_use():
            raise AssertionError("Cannot call unknown function '{0}'".format(function_name))
        self.function_name = function_name
        self.args = args
        self.kwargs = kwargs
        if expr_type is UNKNOWN_TYPE:
            # Try to find out automatically
            expr_type = scope.get_name_properties(function_name).get(PROPERTY_RETURN_TYPE, expr_type)
        self.type = expr_type

    def as_ast(self):
        if not allowable_name(self.function_name, allow_builtin=True):
            raise AssertionError("Expected {0} to be a valid Python identifier or builtin".format(self.function_name))

        if self.function_name in SENSITIVE_FUNCTIONS:
            raise AssertionError("Disallowing call to '{0}'".format(self.function_name))

        for name in self.kwargs.keys():
            if not allowable_keyword_arg_name(name):
                raise AssertionError("Expected {0} to be a valid Fluent NamedArgument name".format(name))

        if any(not allowable_name(name) for name in self.kwargs.keys()):
            # `my_function(**{})` syntax
            kwarg_pairs = list(sorted(self.kwargs.items()))
            kwarg_names, kwarg_values = [k for k, v in kwarg_pairs], [v for k, v in kwarg_pairs]
            return ast.Call(
                func=ast.Name(id=self.function_name, ctx=ast.Load(), **DEFAULT_AST_ARGS),
                args=[arg.as_ast() for arg in self.args],
                keywords=[ast.keyword(arg=None,
                                      value=ast.Dict(keys=[ast.Str(k, **DEFAULT_AST_ARGS)
                                                           for k in kwarg_names],
                                                     values=[v.as_ast() for v in kwarg_values],
                                                     **DEFAULT_AST_ARGS),
                                      **DEFAULT_AST_ARGS)],
                **DEFAULT_AST_ARGS)

        # Normal `my_function(kwarg=foo)` syntax
        return ast.Call(
            func=ast.Name(id=self.function_name, ctx=ast.Load(), **DEFAULT_AST_ARGS),
            args=[arg.as_ast() for arg in self.args],
            keywords=[ast.keyword(arg=name, value=value.as_ast(), **DEFAULT_AST_ARGS)
                      for name, value in self.kwargs.items()],
            **DEFAULT_AST_ARGS)

    def simplify(self, changes, simplifier):
        self.args = [arg.simplify(changes, simplifier) for arg in self.args]
        self.kwargs = {name: val.simplify(changes, simplifier) for name, val in self.kwargs.items()}
        return simplifier(self, changes)

    def __repr__(self):
        return 'FunctionCall({0}, {1}, {2})'.format(self.function_name, self.args, self.kwargs)


class MethodCall(Expression):
    def __init__(self, obj, method_name, args, expr_type=UNKNOWN_TYPE):
        # We can't check method_name because we don't know the type of obj yet.
        self.obj = obj
        self.method_name = method_name
        self.args = args
        self.type = expr_type

    def as_ast(self):
        if not allowable_name(self.method_name, for_method=True):
            raise AssertionError("Expected {0} to be a valid Python identifier".format(self.method_name))
        return ast.Call(
            func=ast.Attribute(value=self.obj.as_ast(),
                               attr=self.method_name,
                               ctx=ast.Load(),
                               **DEFAULT_AST_ARGS),
            args=[arg.as_ast() for arg in self.args],
            keywords=[],
            **DEFAULT_AST_ARGS)

    def simplify(self, changes, simplifier):
        self.obj = self.obj.simplify(changes, simplifier)
        self.args = [arg.simplify(changes, simplifier) for arg in self.args]
        return simplifier(self, changes)

    def __repr__(self):
        return 'MethodCall({0}, {1}, {2})'.format(repr(self.obj),
                                                  repr(self.method_name),
                                                  repr(self.args))


class DictLookup(Expression):
    def __init__(self, lookup_obj, lookup_arg, expr_type=UNKNOWN_TYPE):
        self.lookup_obj = lookup_obj
        self.lookup_arg = lookup_arg
        self.type = expr_type

    def as_ast(self):
        return ast.Subscript(
            value=self.lookup_obj.as_ast(),
            slice=ast.Index(value=self.lookup_arg.as_ast(), **DEFAULT_AST_ARGS),
            ctx=ast.Load(),
            **DEFAULT_AST_ARGS)

    def simplify(self, changes, simplifier):
        self.lookup_obj = self.lookup_obj.simplify(changes, simplifier)
        self.lookup_arg = self.lookup_arg.simplify(changes, simplifier)
        return simplifier(self, changes)


ObjectCreation = FunctionCall


class NoneExpr(Expression):
    type = type(None)

    def as_ast(self):
        return ast.NameConstant(
            value=None,
            **DEFAULT_AST_ARGS)


class BinaryOperator(Expression):
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def simplify(self, changes, simplifier):
        self.left = self.left.simplify(changes, simplifier)
        self.right = self.right.simplify(changes, simplifier)
        return simplifier(self, changes)


class Equals(BinaryOperator):
    type = bool

    def as_ast(self):
        return ast.Compare(
            left=self.left.as_ast(),
            comparators=[self.right.as_ast()],
            ops=[ast.Eq()],
            **DEFAULT_AST_ARGS)


class BoolOp(BinaryOperator):
    type = bool
    op = NotImplemented

    def as_ast(self):
        return ast.BoolOp(
            op=self.op(), values=[self.left.as_ast(),
                                  self.right.as_ast()],
            **DEFAULT_AST_ARGS)


class Or(BoolOp):
    op = ast.Or


def simplify(codegen_ast, simplifier=None):
    if simplifier is None:
        def simplifier(n, changes):
            return n
    changes = [True]
    while any(changes):
        changes = []
        codegen_ast = codegen_ast.simplify(changes, simplifier)
    return codegen_ast
