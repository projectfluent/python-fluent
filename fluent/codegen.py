from __future__ import absolute_import, unicode_literals


class Scope(object):
    def __init__(self, parent_scope=None):
        super(Scope, self).__init__()
        self.parent_scope = parent_scope
        self.statements = []
        self.names = set()

    def self_and_parent_names(self):
        names = self.names
        if self.parent_scope is not None:
            names = names | self.parent_scope.self_and_parent_names()
        return names

    def reserve_name(self, requested):
        cleaned = cleanup_name(requested)
        attempt = cleaned
        count = 2
        # To avoid shadowing of global names in local scope, we
        # take into account parent scope when assigning names.
        used = self.self_and_parent_names()
        while attempt in used:
            attempt = attempt + str(count)
            count += 1
        self.names.add(attempt)
        return attempt

    def add_function(self, func_name, func):
        assert func.name == func_name
        self.statements.append(func)

    def as_source_code(self):
        return "\n".join(s.as_source_code() for s in self.statements)


def cleanup_name(name):
    # TODO - a lot more sanitising required
    return name.replace(".", "_").replace("-", "_")


class Module(Scope):
    pass


class Statement(object):
    pass


class Function(Scope, Statement):
    def __init__(self, name, args, **kwargs):
        self.name = name
        self.args = args
        super(Function, self).__init__(**kwargs)

    # TODO reserve_name should take into account function args as 'taken'

    def as_source_code(self):
        line1 = 'def {0}({1}):\n'.format(self.name,
                                         ', '.join(self.args))
        if not self.statements:
            body = 'pass\n'
        else:
            body = super(Function, self).as_source_code()
        return line1 + indent(body)

    def add_return(self, value):
        self.statements.append(Return(value))


class Return(Statement):
    def __init__(self, value):
        self.value = value

    def as_source_code(self):
        return 'return {0}\n'.format(self.value.as_source_code())


class Expression(object):
    pass


class String(Expression):
    def __init__(self, string_value):
        self.string_value = string_value

    def as_source_code(self):
        retval = repr(self.string_value)
        # We use 'unicode_literals' at module level, so avoid unicode markers
        # on strings for the sake of Python2/3 consistency.
        if retval.startswith('u'):
            return retval[1:]
        else:
            return retval


class StringJoin(Expression):
    def __init__(self, parts):
        self.parts = parts

    def as_source_code(self):
        return '"".join([' + ', '.join(p.as_source_code() for p in self.parts) + '])'


class Tuple(Expression):
    def __init__(self, *items):
        assert len(items) > 1
        self.items = items

    def as_source_code(self):
        return '(' + ", ".join(i.as_source_code() for i in self.items) + ')'


class VariableReference(Expression):
    def __init__(self, name):
        self.name = name

    def as_source_code(self):
        return self.name


def indent(text):
    return "\n".join("    " + l for l in text.split("\n"))
