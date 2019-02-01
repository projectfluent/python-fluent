Custom functions
----------------

You can add functions to the ones available to FTL authors by passing a
``functions`` dictionary to the ``FluentBundle`` constructor:

.. code-block:: python

    >>> import platform
    >>> def os_name():
    ...    """Returns linux/mac/windows/other"""
    ...    return {'Linux': 'linux',
    ...            'Darwin': 'mac',
    ...            'Windows': 'windows'}.get(platform.system(), 'other')

    >>> bundle = FluentBundle(['en-US'], functions={'OS': os_name})
    >>> bundle.add_messages("""
    ... welcome = { OS() ->
    ...    [linux]    Welcome to Linux
    ...    [mac]      Welcome to Mac
    ...    [windows]  Welcome to Windows
    ...   *[other]    Welcome
    ...   }
    ... """)
    >>> print(bundle.format('welcome')[0]
    Welcome to Linux

These functions can accept positional and keyword arguments, like the ``NUMBER``
and ``DATETIME`` builtins. They must accept the following types of objects
passed as arguments:

- unicode strings (i.e. ``unicode`` on Python 2, ``str`` on Python 3)
- ``fluent.runtime.types.FluentType`` subclasses, namely:

  - ``FluentNumber`` - ``int``, ``float`` or ``Decimal`` objects passed in
    externally, or expressed as literals, are wrapped in these. Note that these
    objects also subclass builtin ``int``, ``float`` or ``Decimal``, so can be
    used as numbers in the normal way.
  - ``FluentDateType`` - ``date`` or ``datetime`` objects passed in are wrapped in
    these. Again, these classes also subclass ``date`` or ``datetime``, and can
    be used as such.
  - ``FluentNone`` - in error conditions, such as a message referring to an
    argument that hasn't been passed in, objects of this type are passed in.

Custom functions should not throw errors, but return ``FluentNone`` instances to
indicate an error or missing data. Otherwise they should return unicode strings,
or instances of a ``FluentType`` subclass as above. Returned numbers and
datetimes should be converted to ``FluentNumber`` or ``FluentDateType``
subclasses using ``fluent.types.fluent_number`` and ``fluent.types.fluent_date``
respectively.

The type signatures of custom functions are checked before they are used, to
ensure the right the number of positional arguments are used, and only available
keyword arguments are used - otherwise a ``TypeError`` will be appended to the
``errors`` list. Using ``*args`` or ``**kwargs`` to allow any number of
positional or keyword arguments is supported, but you should ensure that your
function actually does allow all positional or keyword arguments.

If you want to override the detected type signature (for example, to limit the
arguments that can be used in an FTL file, or to provide a proper signature for
a function that has a signature using ``*args`` and ``**kwargs`` but is more
restricted in reality), you can add an ``ftl_arg_spec`` attribute to the
function. The value should be a two-tuple containing 1) an integer specifying
the number of positional arguments, and 2) a list of allowed keyword arguments.
For example, for a custom function ``my_func`` the following will stop the
``restricted`` keyword argument from being used from FTL files, while allowing
``allowed``, and will require that a single positional argument is passed:

.. code-block:: python

    def my_func(arg1, allowed=None, restricted=None):
        pass

    my_func.ftl_arg_spec = (1, ['allowed'])

The Fluent spec allows keyword arguments with hyphens (``-``) in them.
Since these cannot be used in valid Python keyword arguments, they are
disallowed by ``fluent.runtime`` and will be filtered out and generate
errors if you specify such a keyword in ``ftl_arg_spec`` or use one in a
message.
