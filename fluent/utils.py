from __future__ import absolute_import, unicode_literals

import inspect

import six


class cachedproperty(object):
    """
    Use cachedproperty as a decorator for turning expensive methods into
    properties whose return values are cached on the instance:

    class Foo(object):

        @cachedproperty
        def my_thing(self):
            print("Calculating...")
            return sum(range(0, 10000000))

    >>> foo = Foo()
    >>> foo.my_thing
    Calculating...
    49999995000000
    >>>
    >>> foo.my_thing
    49999995000000

    """
    def __init__(self, method):
        self.method = method

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        retval = self.method(instance)
        instance.__dict__[self.method.__name__] = retval
        return retval


def numeric_to_native(val):
    """
    Given a numeric string (as defined by fluent spec),
    return an int or float
    """
    # val matches this EBNF:
    #  '-'? [0-9]+ ('.' [0-9]+)?
    if '.' in val:
        return float(val)
    else:
        return int(val)


class Any(object):
    pass


Any = Any()


if hasattr(inspect, 'signature'):
    def inspect_function_args(function):
        """
        For a Python function, returns a 2 tuple containing:
        (number of positional args or Any,
        set of keyword args or Any)

        Keyword args are defined as those with default values.
        'Keyword only' args with no default values are not supported.
        """
        if hasattr(function, 'ftl_arg_spec'):
            return function.ftl_arg_spec
        sig = inspect.signature(function)
        parameters = list(sig.parameters.values())

        positional = (
            Any if any(p.kind == inspect.Parameter.VAR_POSITIONAL
                       for p in parameters)
            else len(list(p for p in parameters
                          if p.default == inspect.Parameter.empty and
                          p.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD)))

        keywords = (
            Any if any(p.kind == inspect.Parameter.VAR_KEYWORD
                       for p in parameters)
            else [p.name for p in parameters
                  if p.default != inspect.Parameter.empty])
        return (positional, keywords)
else:
    def inspect_function_args(function):
        """
        For a Python function, returns a 2 tuple containing:
        (number of positional args or Any,
        set of keyword args or Any)

        Keyword args are defined as those with default values.
        'Keyword only' args with no default values are not supported.
        """
        if hasattr(function, 'ftl_arg_spec'):
            return function.ftl_arg_spec
        args = inspect.getargspec(function)

        num_defaults = 0 if args.defaults is None else len(args.defaults)
        positional = (
            Any if args.varargs is not None
            else len(args.args) - num_defaults
        )

        keywords = (
            Any if args.keywords is not None
            else ([] if num_defaults == 0 else args.args[-num_defaults:])
        )
        return (positional, keywords)


def args_match(function_name, args, kwargs, arg_spec):
    """
    Returns a tuple indicating whether the passed in args tuple and kwargs dict
    match the `arg_spec` provided.

    For a match, returns a tuple
       (True, None)

    For a non-match, returns a tuple
       (False, TypeError instance)

    """
    # We try to match the TypeError raised by Python when calling functions with
    # wrong arguments.

    # TypeError: foo() got an unexpected keyword argument 'bar'
    # TypeError: foo() takes 0 positional arguments but 1 was given

    positional_args, allowed_kwargs = arg_spec
    if (allowed_kwargs is not Any and not all(kw in allowed_kwargs
                                              for kw in kwargs)):
        return (False,
                TypeError("{0}() got an unexpected keyword argument '{1}'"
                          .format(function_name, six.next(kw for kw in kwargs
                                                          if kw not in allowed_kwargs))
                          )
                )
    if (positional_args is not Any and not positional_args == len(args)):
        return (False,
                TypeError("{0}() takes {1} positional arguments but {2} was given"
                          .format(function_name, positional_args, len(args))
                          )
                )

    return (True, None)
