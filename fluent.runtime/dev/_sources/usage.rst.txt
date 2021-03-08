Using fluent.runtime
====================

Learn the FTL syntax
--------------------

FTL is a localization file format used for describing translation
resources. FTL stands for *Fluent Translation List*.

FTL is designed to be simple to read, but at the same time allows to
represent complex concepts from natural languages like gender, plurals,
conjugations, and others.

::

    hello-user = Hello, { $username }!

In order to use fluent.runtime, you will need to create FTL files. `Read the
Fluent Syntax Guide <http://projectfluent.org/fluent/guide/>`_ in order to
learn more about the syntax.

Using FluentLocalization
------------------------

Once you have some FTL files, you can generate translations using the
``fluent.runtime`` package. You start with the ``FluentLocalization`` class:

.. code-block:: python

    >>> from fluent.runtime import FluentLocalization, FluentResourceLoader

The Fluent files of your application are loaded with a ``FluentResourceLoader``.

.. code-block:: python

    >>> loader = FluentResourceLoader("l10n/{locale}")

The main entrypoint for your application is a ``FluentLocalization``.
You pass a list of locales to the constructor - the first being the
desired locale, with fallbacks after that - as well as resource IDs and your
loader.

.. code-block:: python

    >>> l10n = FluentLocalization(["de", "en-US"], ["main.ftl"], loader)
    >>> val = l10n.format_value("my-first-string")
    "Fluent can be easy"

This assumes that you have a directory layout like so

.. code-block::

    l10n/
      de/
        main.ftl
      en-US/
        main.ftl

and ``l10n/de/main.ftl`` with:

.. code-block:: fluent

  second-string = Eine Übersetzung

as well as ``l10n/en-US/main.ftl`` with:

.. code-block:: fluent

  my-first-string = Fluent can be easy
  second-string = An original string

As you can see, our first example returned the English string, as that's on
our fallback list. When retrieving an existing translation, you get the
translated results as expected:

.. code-block:: python

  >>> l10n.format_value("second-string")
  "Eine Übersetzung"



Python 2
~~~~~~~~

The above examples assume Python 3. Since Fluent uses unicode everywhere
internally (and doesn't accept bytestrings), if you are using Python 2
you will need to make adjustments to the above example code. Either add
``u`` unicode literal markers to strings or add this at the top of the
module or the start of your repl session:

.. code-block:: python

    from __future__ import unicode_literals

DemoLocalization
~~~~~~~~~~~~~~~~

To make the documentation easier to read, we're using a ``DemoLocalization``,
that just uses a single literal Fluent resource. Find out more about the
details in the :doc:`internals` section.

.. code-block:: python

  >>> l10n = DemoLocalization("key = A localization")
  >>> pl = DemoLocalization("key = A localization", locale="pl")

Numbers
~~~~~~~

When rendering translations, Fluent passes any numeric arguments (``int``,
``float`` or ``Decimal``) through locale-aware formatting functions:

.. code-block:: python

    >>> l10n = DemoLocalization(
    ... "show-total-points = You have { $points } points."
    ... )
    >>> val = l10n.format_value("show-total-points", {'points': 1234567})
    >>> val
    'You have 1,234,567 points.'

You can specify your own formatting options on the arguments passed in
by wrapping your numeric arguments with
``fluent.runtime.types.fluent_number``:

.. code-block:: python

    >>> from fluent.runtime.types import fluent_number
    >>> points = fluent_number(1234567, useGrouping=False)
    >>> l10n.format_value("show-total-points", {'points': 1234567})
    'You have 1234567 points.'

    >>> amount = fluent_number(1234.56, style="currency", currency="USD")
    >>> l10n = DemoLocalization(
    ... "your-balance = Your balance is { $amount }"
    ... )
    >>> l10n.format_value(balance.value, {'amount': amount})
    'Your balance is $1,234.56'

The options available are defined in the Fluent spec for
`NUMBER <https://projectfluent.org/fluent/guide/functions.html#number>`_.
Some of these options can also be defined in the FTL files, as described
in the Fluent spec, and the options will be merged.

Date and Time
~~~~~~~~~~~~~

Python ``datetime.datetime`` and ``datetime.date`` objects are also
passed through locale aware functions:

.. code-block:: python

    >>> from datetime import date
    >>> l10n = DemoLocalization("today-is = Today is { $today }")
    >>> val = l10n.format_value("today-is", {"today": date.today() })
    >>> val
    'Today is Jun 16, 2018'

You can explicitly call the ``DATETIME`` builtin to specify options:

.. code-block:: python

    >>> l10n = DemoLocalization(
    ... 'today-is = Today is { DATETIME($today, dateStyle: "short") }'
    ... )

See the `DATETIME
docs <https://projectfluent.org/fluent/guide/functions.html#datetime>`_.
However, currently the only supported options to ``DATETIME`` are:

-  ``timeZone``
-  ``dateStyle`` and ``timeStyle`` which are `proposed
   additions <https://github.com/tc39/proposal-ecma402-datetime-style>`_
   to the ECMA i18n spec.

To specify options from Python code, use
``fluent.runtime.types.fluent_date``:

.. code-block:: python

    >>> from fluent.runtime.types import fluent_date
    >>> today = date.today()
    >>> short_today = fluent_date(today, dateStyle='short')
    >>> val = l10n.format_value("today-is", {"today": short_today })
    >>> val
    'Today is 6/17/18'

You can also specify timezone for displaying ``datetime`` objects in two
ways:

-  Create timezone aware ``datetime`` objects, and pass these to the
   ``format`` call e.g.:

   .. code-block:: python


       >>> import pytz
       >>> from datetime import datetime
       >>> utcnow = datime.utcnow().replace(tzinfo=pytz.utc)
       >>> moscow_timezone = pytz.timezone('Europe/Moscow')
       >>> now_in_moscow = utcnow.astimezone(moscow_timezone)

-  Or, use timezone naive ``datetime`` objects, or ones with a UTC
   timezone, and pass the ``timeZone`` argument to ``fluent_date`` as a
   string:

   .. code-block:: python

       >>> utcnow = datetime.utcnow()
       >>> utcnow
       datetime.datetime(2018, 6, 17, 12, 15, 5, 677597)

       >>> l10n = DemoLocalization("now-is = Now is { $now }")
       >>> val = bundle.format_pattern("now-is",
       ...    {"now": fluent_date(utcnow,
       ...                        timeZone="Europe/Moscow",
       ...                        dateStyle="medium",
       ...                        timeStyle="medium")})
       >>> val
       'Now is Jun 17, 2018, 3:15:05 PM'

Custom functions
~~~~~~~~~~~~~~~~

You can add functions to the ones available to FTL authors by passing a
``functions`` dictionary to the ``FluentLocalization`` constructor:

.. code-block:: python

    >>> import platform
    >>> def os_name():
    ...    """Returns linux/mac/windows/other"""
    ...    return {'Linux': 'linux',
    ...            'Darwin': 'mac',
    ...            'Windows': 'windows'}.get(platform.system(), 'other')

    >>> l10n = FluentLocalization(['en-US'], ['os.ftl'], loader, functions={'OS': os_name})
    >>> l10n.format_value('welcome')
    Welcome to Linux

That's with ``l10n/en-US/os.ftl`` as:

.. code-block:: fluent

    welcome = { OS() ->
       [linux]    Welcome to Linux
       [mac]      Welcome to Mac
       [windows]  Welcome to Windows
      *[other]    Welcome
      }

These functions can accept positional and keyword arguments (like the
``NUMBER`` and ``DATETIME`` builtins), and in this case must accept the
following types of arguments:

-  unicode strings (i.e. ``unicode`` on Python 2, ``str`` on Python 3)
-  ``fluent.runtime.types.FluentType`` subclasses, namely:
-  ``FluentNumber`` - ``int``, ``float`` or ``Decimal`` objects passed
   in externally, or expressed as literals, are wrapped in these. Note
   that these objects also subclass builtin ``int``, ``float`` or
   ``Decimal``, so can be used as numbers in the normal way.
-  ``FluentDateType`` - ``date`` or ``datetime`` objects passed in are
   wrapped in these. Again, these classes also subclass ``date`` or
   ``datetime``, and can be used as such.
-  ``FluentNone`` - in error conditions, such as a message referring to
   an argument that hasn't been passed in, objects of this type are
   passed in.

Custom functions should not throw errors, but return ``FluentNone``
instances to indicate an error or missing data. Otherwise they should
return unicode strings, or instances of a ``FluentType`` subclass as
above.

Known limitations and bugs
~~~~~~~~~~~~~~~~~~~~~~~~~~

-  We do not yet support ``NUMBER(..., currencyDisplay="name")`` - see
   `this python-babel pull
   request <https://github.com/python-babel/babel/pull/585>`_ which
   needs to be merged and released.

- Most options to ``DATETIME`` are not yet supported. See the `MDN docs for
  Intl.DateTimeFormat
  <https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/DateTimeFormat>`_,
  the `ECMA spec for BasicFormatMatcher
  <http://www.ecma-international.org/ecma-402/1.0/#BasicFormatMatcher>`_ and the
  `Intl.js polyfill
  <https://github.com/andyearnshaw/Intl.js/blob/master/src/12.datetimeformat.js>`_.

Help with the above would be welcome!
