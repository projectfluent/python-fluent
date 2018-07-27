"""
Utilities for doing Python code generation
"""
from __future__ import absolute_import, unicode_literals

import keyword
import re

from six import text_type

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
#    In particular, we should try to make it hard to generate incorrect code,
#    esepcially incorrect code that is syntactically correct and therefore
#    compiles but doesn't work. In particular, we try to make it hard to
#    generate accidental name clashes, or use variables that are not defined.
#
# 3. Simplicity
#
#    The resulting Python code should be easy to read and understand.
#
# 4. Predictability
#
#    Since we want to test the resulting source code, we have made some design
#    decisions that aim to ensure things like function argument names are
#    consistent and so can predicted easily.


PROPERTY_TYPE = 'PROPERTY_TYPE'
PROPERTY_RETURN_TYPE = 'PROPERTY_RETURN_TYPE'
UNKNOWN_TYPE = object


class PythonAst(object):
    def simplify(self, changes):
        """
        Simplify the statement/expression, returning either a modified
        self, or a new object.

        This method should call .simplify(changes) on any contained subexpressions
        or statements.

        If changes were made, a True value must be appended to the passed in changes list.
        """
        return self


class Scope(PythonAst):
    def __init__(self, parent_scope=None):
        super(Scope, self).__init__()
        self.parent_scope = parent_scope
        self.statements = []
        self.names = set()
        self._function_arg_reserved_names = set()
        self._properties = {}

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
            else:
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
        else:
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

    # self.statements can be manipulated explicitly, appending statement
    # objects. But in some cases for a better and safe API we have explicit
    # 'add_X' methods and sometimes make the statement objects private
    def add_assignment(self, names, value):
        """
        Adds an assigment of the form:

           x = value

        or

           x, y = value

        Pass a string for the former, a tuple of strings for the later
        """
        if not isinstance(names, tuple):
            names = tuple([names])

        for name in names:
            if name not in self.names_in_use():
                raise AssertionError("Cannot assign to unreserved name '{0}'".format(name))

        self.statements.append(_Assignment(names, value))

    def add_function(self, func_name, func):
        assert func.func_name == func_name
        self.statements.append(func)

    def as_source_code(self):
        return "".join(s.as_source_code() + "\n" for s in self.statements)

    def simplify(self, changes):
        self.statements = [s.simplify(changes) for s in self.statements]
        return self


_IDENTIFIER_SANITIZER_RE = re.compile('[^a-zA-Z0-9_]')
_IDENTIFIER_START_RE = re.compile('^[a-zA-Z_]')


def cleanup_name(name):
    # See https://docs.python.org/2/reference/lexical_analysis.html#grammar-token-identifier
    name = _IDENTIFIER_SANITIZER_RE.sub('', name)
    if not _IDENTIFIER_START_RE.match(name):
        name = "n" + name
    return name


class Module(Scope):
    pass


class Statement(PythonAst):
    pass


class _Assignment(Statement):
    def __init__(self, names, value):
        self.names = names
        self.value = value

    def format_names(self):
        return ", ".join(n for n in self.names)

    def as_source_code(self):
        return "{0} = {1}".format(self.format_names(),
                                  self.value.as_source_code())

    def simplify(self, changes):
        self.value = self.value.simplify(changes)
        return self


class Block(Scope):
    def as_source_code(self):
        if not self.statements:
            return 'pass\n'
        else:
            return super(Block, self).as_source_code()


class Function(Block, Statement):
    def __init__(self, name, args=None, kwargs=None, parent_scope=None, debug=False):
        super(Function, self).__init__(parent_scope=parent_scope)
        self.func_name = name
        if args is None:
            args = ()
        if kwargs is None:
            kwargs = {}
        for arg_set in [args, kwargs.keys()]:
            for arg in arg_set:
                if (arg in parent_scope.names_in_use()):
                    raise AssertionError("Can't use '{0}' as function argument name because it shadows other names"
                                         .format(arg))
                self.reserve_name(arg, function_arg=True)
        self.args = args
        self.kwargs = kwargs

        if debug:
            self.statements.append(SetBreakpoint())

    def as_source_code(self):
        line1 = 'def {0}({1}{2}):\n'.format(
            self.func_name,
            ', '.join(self.args),
            (", " if self.args and self.kwargs else "") +
            ", ".join("{0}={1}".format(name, val.as_source_code())
                      for name, val in self.kwargs.items())
        )
        body = super(Function, self).as_source_code()
        return line1 + indent(body)

    def add_return(self, value):
        self.statements.append(Return(value))

    def simplify(self, changes):
        self = super(Function, self).simplify(changes)
        if len(self.statements) < 2:
            return self
        # Remove needless unpacking and repacking of final return tuple
        if (isinstance(self.statements[-1], Return) and
                isinstance(self.statements[-2], _Assignment)):
            return_s = self.statements[-1]
            assign_s = self.statements[-2]
            return_source = return_s.value.as_source_code()
            assign_names = assign_s.format_names()
            if (return_source == assign_names or
                (isinstance(return_s.value, Tuple) and
                    return_source == "(" + assign_names + ")")):
                new_return = Return(self.statements[-2].value)
                self.statements = self.statements[:-2]
                self.statements.append(new_return)
                changes.append(True)
        return self


class Return(Statement):
    def __init__(self, value):
        self.value = value

    def as_source_code(self):
        return 'return {0}'.format(self.value.as_source_code())

    def simplify(self, changes):
        self.value = self.value.simplify(changes)
        return self


class If(Statement):
    def __init__(self, parent_scope):
        self.if_blocks = []
        self._conditions = []
        self.else_block = Block(parent_scope=parent_scope)
        self._parent_scope = parent_scope

    def add_if(self, condition):
        new_if = Block(parent_scope=self._parent_scope)
        self.if_blocks.append(new_if)
        self._conditions.append(condition)
        return new_if

    def as_source_code(self):
        first = True
        output = []

        for condition, if_block in zip(self._conditions, self.if_blocks):
            if_start = "if" if first else "elif"
            condition_rendered = condition.as_source_code()
            if (condition_rendered.startswith('(') and
                    condition_rendered.endswith(')')):
                condition_rendered = condition_rendered[1:-1]
            output.append("{0} {1}:\n".format(if_start, condition_rendered))
            output.append(indent(if_block.as_source_code()))
            first = False
        if self.else_block.statements:
            output.append("else:\n")
            output.append(indent(self.else_block.as_source_code()))
        return ''.join(output)

    def simplify(self, changes):
        self.if_blocks = [block.simplify(changes) for block in self.if_blocks]
        self._conditions = [expr.simplify(changes) for expr in self._conditions]
        self.else_block = self.else_block.simplify(changes)
        if not self.if_blocks:
            # Unusual case of no conditions, only default case, but it
            # simplifies other code to be able to handle this uniformly. We can
            # replace this if statement with a single unconditional block.
            changes.append(True)
            return self.else_block
        else:
            return self


class TryCatch(Statement):
    def __init__(self, catch_exception, parent_scope):
        self.catch_exception = catch_exception
        self.try_block = Block(parent_scope=parent_scope)
        self.except_block = Block(parent_scope=parent_scope)
        self.else_block = Block(parent_scope=parent_scope)

    def as_source_code(self):
        retval = ("try:\n" +
                  indent(self.try_block.as_source_code()) +
                  "except {0}:\n".format(self.catch_exception.as_source_code()) +
                  indent(self.except_block.as_source_code()))
        if self.else_block.statements:
            retval += ("else:\n" +
                       indent(self.else_block.as_source_code()))
        return retval

    def simplify(self, changes):
        self.catch_exception = self.catch_exception.simplify(changes)
        self.try_block = self.try_block.simplify(changes)
        self.except_block = self.except_block.simplify(changes)
        self.else_block = self.else_block.simplify(changes)
        return self


class Expression(PythonAst):
    # type represents the Python type this expression will produce,
    # if we know it (UNKNOWN_TYPE otherwise).
    type = UNKNOWN_TYPE


class String(Expression):
    type = text_type

    def __init__(self, string_value):
        self.string_value = string_value

    def as_source_code(self):
        retval = repr(self.string_value)
        # We eventually call 'exec' in a module that has 'from __future__ import
        # unicode_literals' at module level, which means that without a 'u' prefix we
        # still get unicode objects in Python 2. So for consistency with Python 3
        # and easier testing we remove these unnecessary prefixes.
        if retval.startswith('u'):
            return retval[1:]
        else:
            return retval


class Number(Expression):
    def __init__(self, number):
        self.number = number
        self.type = type(number)

    def as_source_code(self):
        return repr(self.number)


class List(Expression):
    def __init__(self, items):
        self.items = items
        self.type = list

    def as_source_code(self):
        return '[' + ', '.join(i.as_source_code() for i in self.items) + ']'

    def simplify(self, changes):
        self.items = [item.simplify(changes) for item in self.items]
        return self


class StringJoin(Expression):
    type = text_type

    def __init__(self, parts):
        self.parts = parts

    def as_source_code(self):
        return "''.join(" + List(self.parts).as_source_code() + ')'

    def simplify(self, changes):
        # Simplify sub parts
        self.parts = [part.simplify(changes) for part in self.parts]

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

        # See if we eliminate the StringJoin altogether
        if len(self.parts) == 0:
            changes.append(True)
            return String('')
        elif len(self.parts) == 1:
            changes.append(True)
            return self.parts[0]
        else:
            return self


class Tuple(Expression):
    type = tuple

    def __init__(self, *items):
        assert len(items) > 1
        self.items = items

    def as_source_code(self):
        return '(' + ", ".join(i.as_source_code() for i in self.items) + ')'

    def simplify(self, changes):
        self.items = [item.simplify(changes) for item in self.items]
        return self


class VariableReference(Expression):
    def __init__(self, name, scope):
        if name not in scope.names_in_use():
            raise AssertionError("Cannot refer to undefined variable '{0}'".format(name))
        self.name = name
        self.type = scope.get_name_properties(name).get(PROPERTY_TYPE, UNKNOWN_TYPE)

    def as_source_code(self):
        return self.name


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

    def as_source_code(self):
        return "{0}({1}{2})".format(self.function_name,
                                    ", ".join(arg.as_source_code() for arg in self.args),
                                    (", " if self.args and self.kwargs else "") +
                                    ", ".join("{0}={1}".format(name, val.as_source_code())
                                              for name, val in self.kwargs.items())
                                    )

    def simplify(self, changes):
        self.args = [arg.simplify(changes) for arg in self.args]
        self.kwargs = {name: val.simplify(changes) for name, val in self.kwargs.items()}
        return self


class MethodCall(Expression):
    def __init__(self, obj, method_name, args, expr_type=UNKNOWN_TYPE):
        # We can't check method_name because we don't know the type of obj yet.
        self.obj = obj
        self.method_name = method_name
        self.args = args
        self.type = expr_type

    def as_source_code(self):
        return "{0}.{1}({2})".format(
            self.obj.as_source_code(),
            self.method_name,
            ", ".join(arg.as_source_code() for arg in self.args))

    def simplify(self, changes):
        self.args = [arg.simplify(changes) for arg in self.args]
        return self


class DictLookup(Expression):
    def __init__(self, lookup_obj, lookup_arg, expr_type=UNKNOWN_TYPE):
        self.lookup_obj = lookup_obj
        self.lookup_arg = lookup_arg
        self.type = expr_type

    def as_source_code(self):
        return "{0}[{1}]".format(self.lookup_obj.as_source_code(),
                                 self.lookup_arg.as_source_code())

    def simplify(self, changes):
        self.lookup_obj = self.lookup_obj.simplify(changes)
        self.lookup_arg = self.lookup_arg.simplify(changes)
        return self


ObjectCreation = FunctionCall


class Verbatim(Expression):
    def __init__(self, code):
        self.code = code

    def as_source_code(self):
        return self.code


class NoneExpr(Expression):
    type = type(None)

    def as_source_code(self):
        return "None"


class SetBreakpoint(Statement):
    def as_source_code(self):
        return "import ipdb; ipdb.set_trace()"


def infix_operator(operator, return_type):
    class Op(Expression):
        type = return_type

        def __init__(self, left, right):
            self.left = left
            self.right = right

        def as_source_code(self):
            return "({0} {1} {2})".format(self.left.as_source_code(),
                                          operator,
                                          self.right.as_source_code())

        def simplify(self, changes):
            self.left = self.left.simplify(changes)
            self.right = self.right.simplify(changes)
            return self

    return Op


Equals = infix_operator("==", bool)
Or = infix_operator("or", bool)


def indent(text):
    return ''.join('    ' + l + '\n' for l in text.rstrip('\n').split('\n'))


def simplify(source_code):
    changes = [True]
    while any(changes):
        changes = []
        source_code = source_code.simplify(changes)
    return source_code
