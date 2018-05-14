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
