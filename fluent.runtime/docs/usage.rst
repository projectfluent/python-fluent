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

Using FluentBundle
------------------

Once you have some FTL files, you can generate translations using the
``fluent.runtime`` package. You start with the ``FluentBundle`` class:

.. code-block:: python

    >>> from fluent.runtime import FluentBundle

You pass a list of locales to the constructor - the first being the
desired locale, with fallbacks after that:

.. code-block:: python

    >>> bundle = FluentBundle(["en-US"])

You must then add messages. These would normally come from a ``.ftl``
file stored on disk, here we will just add them directly:

.. code-block:: python

    >>> bundle.add_messages("""
    ... welcome = Welcome to this great app!
    ... greet-by-name = Hello, { $name }!
    ... """)

To generate translations, use the ``format`` method, passing a message
ID and an optional dictionary of substitution parameters. If the the
message ID is not found, a ``LookupError`` is raised. Otherwise, as per
the Fluent philosophy, the implementation tries hard to recover from any
formatting errors and generate the most human readable representation of
the value. The ``format`` method therefore returns a tuple containing
``(translated string, errors)``, as below.

.. code-block:: python

    >>> translated, errs = bundle.format('welcome')
    >>> translated
    "Welcome to this great app!"
    >>> errs
    []

    >>> translated, errs = bundle.format('greet-by-name', {'name': 'Jane'})
    >>> translated
    'Hello, \u2068Jane\u2069!'

    >>> translated, errs = bundle.format('greet-by-name', {})
    >>> translated
    'Hello, \u2068name\u2069!'
    >>> errs
    [FluentReferenceError('Unknown external: name')]

You will notice the extra characters ``\u2068`` and ``\u2069`` in the
output. These are Unicode bidi isolation characters that help to ensure
that the interpolated strings are handled correctly in the situation
where the text direction of the substitution might not match the text
direction of the localized text. These characters can be disabled if you
are sure that is not possible for your app by passing
``use_isolating=False`` to the ``FluentBundle`` constructor.

Python 2
~~~~~~~~

The above examples assume Python 3. Since Fluent uses unicode everywhere
internally (and doesn't accept bytestrings), if you are using Python 2
you will need to make adjustments to the above example code. Either add
``u`` unicode literal markers to strings or add this at the top of the
module or the start of your repl session:

.. code-block:: python

    from __future__ import unicode_literals

CompilingFluentBundle
~~~~~~~~~~~~~~~~~~~~~

In addition to the default ``FluentBundle`` implementation, there is also a high
performance implementation that compilers to Python AST. You can use it just the same:

.. code-block:: python

   from fluent.runtime import CompilingFluentBundle as FluentBundle

Be sure to check the notes on :doc:`implementations`, especially the security
section.

Numbers
~~~~~~~

When rendering translations, Fluent passes any numeric arguments (``int``,
``float`` or ``Decimal``) through locale-aware formatting functions:

.. code-block:: python

    >>> bundle.add_messages("show-total-points = You have { $points } points.")
    >>> val, errs = bundle.format("show-total-points", {'points': 1234567})
    >>> val
    'You have 1,234,567 points.'

You can specify your own formatting options on the arguments passed in
by wrapping your numeric arguments with
``fluent.runtime.types.fluent_number``:

.. code-block:: python

    >>> from fluent.runtime.types import fluent_number
    >>> points = fluent_number(1234567, useGrouping=False)
    >>> bundle.format("show-total-points", {'points': points})[0]
    'You have 1234567 points.'

    >>> amount = fluent_number(1234.56, style="currency", currency="USD")
    >>> bundle.add_messages("your-balance = Your balance is { $amount }")
    >>> bundle.format("your-balance", {'amount': amount})[0]
    'Your balance is $1,234.56'

The options available are defined in the Fluent spec for
`NUMBER <https://projectfluent.org/fluent/guide/functions.html#number>`_.
Some of these options can also be defined in the FTL files, as described
in the Fluent spec, and the options will be merged.

Date and time
~~~~~~~~~~~~~

Python ``datetime.datetime`` and ``datetime.date`` objects are also
passed through locale aware functions:

.. code-block:: python

    >>> from datetime import date
    >>> bundle.add_messages("today-is = Today is { $today }")
    >>> val, errs = bundle.format("today-is", {"today": date.today() })
    >>> val
    'Today is Jun 16, 2018'

You can explicitly call the ``DATETIME`` builtin to specify options:

.. code-block:: python

    >>> bundle.add_messages('today-is = Today is { DATETIME($today, dateStyle: "short") }')

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
    >>> val, errs = bundle.format("today-is", {"today": short_today })
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

       >>> bundle.add_messages("now-is = Now is { $now }")
       >>> val, errs = bundle.format("now-is",
       ...    {"now": fluent_date(utcnow,
       ...                        timeZone="Europe/Moscow",
       ...                        dateStyle="medium",
       ...                        timeStyle="medium")})
       >>> val
       'Now is Jun 17, 2018, 3:15:05 PM'


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


Other features and further information
--------------------------------------

* :doc:`implementations`
* :doc:`functions`
* :doc:`errors`
