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


def partition(iterable, predicate):
    """
    Partition a list into two lists, the first with items that match the
    predicate, the second with the rest.
    """
    matching = []
    other = []
    for i in iterable:
        if predicate(i):
            matching.append(i)
        else:
            other.append(i)

    return matching, other


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
