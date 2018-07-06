"""
Utilities for doing Python code generation
"""
from __future__ import absolute_import, unicode_literals

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


class Scope(object):
    def __init__(self, parent_scope=None):
        super(Scope, self).__init__()
        self.parent_scope = parent_scope
        self.statements = []
        self.names = set()
        self._function_arg_reserved_names = set()

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

    def reserve_name(self, requested, function_arg=False):
        """
        Reserve a name as being in use in a scope.

        Pass function_arg=True if this is a function argument.
        """
        if function_arg:
            if requested in self.function_arg_reserved_names():
                assert requested not in self.names_in_use()
                self.names.add(requested)
                return requested
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
        while attempt in used:
            attempt = attempt + str(count)
            count += 1
        self.names.add(attempt)
        return attempt

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


def cleanup_name(name):
    # TODO - a lot more sanitising required
    return name.replace(".", "_").replace("-", "_")


class Module(Scope):
    pass


class Statement(object):
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


class Block(Scope):
    def as_source_code(self):
        if not self.statements:
            return 'pass\n'
        else:
            return super(Block, self).as_source_code()


class Function(Block, Statement):
    def __init__(self, name, args, parent_scope, **kwargs):
        super(Function, self).__init__(parent_scope=parent_scope)
        self.func_name = name
        for arg in args:
            if (arg in parent_scope.names_in_use()):
                raise AssertionError("Can't use '{0}' as function argument name because it shadows other names"
                                     .format(arg))
            self.reserve_name(arg, function_arg=True)
        self.args = args

    def as_source_code(self):
        self.simplify()
        line1 = 'def {0}({1}):\n'.format(self.func_name,
                                         ', '.join(self.args))
        body = super(Function, self).as_source_code()
        return line1 + indent(body)

    def add_return(self, value):
        self.statements.append(Return(value))

    def simplify(self):
        if len(self.statements) < 2:
            return
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


class Return(Statement):
    def __init__(self, value):
        self.value = value

    def as_source_code(self):
        return 'return {0}'.format(self.value.as_source_code())


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


class Expression(object):
    pass


class String(Expression):
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

    def as_source_code(self):
        return repr(self.number)


class List(Expression):
    def __init__(self, items):
        self.items = items

    def as_source_code(self):
        return '[' + ', '.join(i.as_source_code() for i in self.items) + ']'


class StringJoin(Expression):
    def __init__(self, parts):
        self.parts = parts

    def as_source_code(self):
        return "''.join(" + List(self.parts).as_source_code() + ')'


class Tuple(Expression):
    def __init__(self, *items):
        assert len(items) > 1
        self.items = items

    def as_source_code(self):
        return '(' + ", ".join(i.as_source_code() for i in self.items) + ')'


class VariableReference(Expression):
    def __init__(self, name, scope):
        if name not in scope.names_in_use():
            raise AssertionError("Cannot refer to undefined variable '{0}'".format(name))
        self.name = name

    def as_source_code(self):
        return self.name


class FunctionCall(Expression):
    def __init__(self, function_name, args, scope):
        if function_name not in scope.names_in_use():
            raise AssertionError("Cannot call unknown function '{0}'".format(function_name))
        self.function_name = function_name
        self.args = args

    def as_source_code(self):
        return "{0}({1})".format(self.function_name,
                                 ", ".join(arg.as_source_code() for arg in self.args))


class MethodCall(Expression):
    def __init__(self, obj, method_name, args):
        # We can't check method_name because we don't know the type of obj yet.
        self.obj = obj
        self.method_name = method_name
        self.args = args

    def as_source_code(self):
        return "{0}.{1}({2})".format(
            self.obj.as_source_code(),
            self.method_name,
            ", ".join(arg.as_source_code() for arg in self.args))


class DictLookup(Expression):
    def __init__(self, lookup_obj, lookup_arg):
        self.lookup_obj = lookup_obj
        self.lookup_arg = lookup_arg

    def as_source_code(self):
        return "{0}[{1}]".format(self.lookup_obj.as_source_code(),
                                 self.lookup_arg.as_source_code())


ObjectCreation = FunctionCall


class Verbatim(Expression):
    def __init__(self, code):
        self.code = code

    def as_source_code(self):
        return self.code


def indent(text):
    return ''.join('    ' + l + '\n' for l in text.rstrip('\n').split('\n'))
