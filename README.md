Project Fluent
==============

This is a Python implementation of Project Fluent, a localization framework
designed to unleash the entire expressive power of natural language
translations.

Project Fluent keeps simple things simple and makes complex things possible.
The syntax used for describing translations is easy to read and understand.  At
the same time it allows, when necessary, to represent complex concepts from
natural languages like gender, plurals, conjugations, and others.


Learn the FTL syntax
--------------------

FTL is a localization file format used for describing translation resources.
FTL stands for _Fluent Translation List_.

FTL is designed to be simple to read, but at the same time allows to represent
complex concepts from natural languages like gender, plurals, conjugations, and
others.

    hello-user = Hello, { $username }!

[Read the Fluent Syntax Guide][] in order to learn more about the syntax.  If
you're a tool author you may be interested in the formal [EBNF grammar][].

[Read the Fluent Syntax Guide]: http://projectfluent.org/fluent/guide/
[EBNF grammar]: https://github.com/projectfluent/fluent/tree/master/spec


Installation
------------

python-fluent consists of two namepsace packages:

* `fluent.syntax` - includes AST classes and parser. Most end users will not
  need this directly. Documentation coming soon!

  To install:

        pip install fluent.syntax


* `fluent.bundle` - methods for generating translations from FTL files.
  Documentation below.

  To install:

        pip install fluent.bundle

  (The correct version of ``fluent.syntax`` will be installed automatically)


PyPI also contains an old `fluent` package which is an older version of just
`fluent.syntax`.

Usage
-----

To generate translations using ``fluent.bundle``, you start with the
`FluentBundle` class:

    >>> from fluent.bundle import FluentBundle

You pass a list of locales to the constructor - the first being the desired
locale, with fallbacks after that:

    >>> bundle = FluentBundle(["en-US"])


You must then add messages. These would normally come from a `.ftl` file stored
on disk, here we will just add them directly:

    >>> bundle.add_messages("""
    ... welcome = Welcome to this great app!
    ... greet-by-name = Hello, { $name }!
    ... """)

To generate translations, use the `format` method, passing a message ID and an
optional dictionary of substitution parameters. If the the message ID is not
found, a `LookupError` is raised. Otherwise, as per the Fluent philosophy, the
implementation tries hard to recover from any formatting errors and generate the
most human readable representation of the value. The `format` method therefore
returns a tuple containing `(translated string, errors)`, as below.

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

You will notice the extra characters `\u2068` and `\u2069` in the output. These
are Unicode bidi isolation characters that help to ensure that the interpolated
strings are handled correctly in the situation where the text direction of the
substitution might not match the text direction of the localized text. These
characters can be disabled if you are sure that is not possible for your app by
passing `use_isolating=False` to the `FluentBundle` constructor.

Python 2
--------

The above examples assume Python 3. Since Fluent uses unicode everywhere
internally (and doesn't accept bytestrings), if you are using Python 2 you will
need to make adjustments to the above example code. Either add `u` unicode
literal markers to strings or add this at the top of the module or the start of
your repl session:

    from __future__ import unicode_literals


Numbers
-------

When rendering translations, Fluent passes any numeric arguments (int or float)
through locale-aware formatting functions:

    >>> bundle.add_messages("show-total-points = You have { $points } points.")
    >>> val, errs = bundle.format("show-total-points", {'points': 1234567})
    >>> val
    'You have 1,234,567 points.'


You can specify your own formatting options on the arguments passed in by
wrapping your numeric arguments with `fluent.types.fluent_number`:

    >>> from fluent.bundle.types import fluent_number
    >>> points = fluent_number(1234567, useGrouping=False)
    >>> bundle.format("show-total-points", {'points': points})[0]
    'You have 1234567 points.'

    >>> amount = fluent_number(1234.56, style="currency", currency="USD")
    >>> bundle.add_messages("your-balance = Your balance is { $amount }")
    >>> bundle.format("your-balance", {'amount': amount})[0]
    'Your balance is $1,234.56'

Thee options available are defined in the Fluent spec for
[NUMBER](https://projectfluent.org/fluent/guide/functions.html#number). Some of
these options can also be defined in the FTL files, as described in the Fluent
spec, and the options will be merged.

Date and time
-------------

Python `dateime.datetime` and `datetime.date` objects are also passed through
locale aware functions:

    >>> from datetime import date
    >>> bundle.add_messages("today-is = Today is { $today }")
    >>> val, errs = bundle.format("today-is", {"today": date.today() })
    >>> val
    'Today is Jun 16, 2018'

You can explicitly call the `DATETIME` builtin to specify options:

    >>> bundle.add_messages('today-is = Today is { DATETIME($today, dateStyle: "short") }')

See the [DATETIME
docs](https://projectfluent.org/fluent/guide/functions.html#datetime). However,
currently the only supported options to `DATETIME` are:

* `timeZone`
* `dateStyle` and `timeStyle` which are [proposed
  additions](https://github.com/tc39/proposal-ecma402-datetime-style) to the ECMA i18n spec.

To specify options from Python code, use `fluent.bundle.types.fluent_date`:

    >>> from fluent.bundle.types import fluent_date
    >>> today = date.today()
    >>> short_today = fluent_date(today, dateStyle='short')
    >>> val, errs = bundle.format("today-is", {"today": short_today })
    >>> val
    'Today is 6/17/18'

You can also specify timezone for displaying `datetime` objects in two ways:

* Create timezone aware `datetime` objects, and pass these to the `format` call
  e.g.:

        >>> import pytz
        >>> from datetime import datetime
        >>> utcnow = datime.utcnow().replace(tzinfo=pytz.utc)
        >>> moscow_timezone = pytz.timezone('Europe/Moscow')
        >>> now_in_moscow = utcnow.astimezone(moscow_timezone)

* Or, use timezone naive `datetime` objects, or ones with a UTC timezone, and
  pass the `timeZone` argument to `fluent_date` as a string:

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


Custom functions
----------------

You can add functions to the ones available to FTL authors by passing
a `functions` dictionary to the `FluentBundle` constructor:


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

These functions can accept positioal and keyword arguments (like the `NUMBER`
and `DATETIME` builtins), and in this case must accept the following types of
arguments:

* unicode strings (i.e. `unicode` on Python 2, `str` on Python 3)
* `fluent.bundle.types.FluentType` subclasses, namely:
  * `FluentNumber` - `int`, `float` or `Decimal` objects passed in externally,
    or expressed as literals, are wrapped in these. Note that these objects also
    subclass builtin `int`, `float` or `Decimal`, so can be used as numbers in
    the normal way.
  * `FluentDateType` - `date` or `datetime` objects passed in are wrapped in
    these. Again, these classes also subclass `date` or `datetime`, and can be
    used as such.
  * `FluentNone` - in error conditions, such as a message referring to an argument
    that hasn't been passed in, objects of this type are passed in.

Custom functions should not throw errors, but return `FluentNone` instances to
indicate an error or missing data. Otherwise they should return unicode strings,
or instances of a `FluentType` subclass as above.


Known limitations and bugs
--------------------------

* We do not yet support `NUMBER(..., currencyDisplay="name")` - see [this python-babel
  pull request](https://github.com/python-babel/babel/pull/585) which needs to
  be merged and released.

* Most options to `DATETIME` are not yet supported. See the [MDN docs for
  Intl.DateTimeFormat](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/DateTimeFormat),
  the [ECMA spec for
  BasicFormatMatcher](http://www.ecma-international.org/ecma-402/1.0/#BasicFormatMatcher)
  and the [Intl.js
  polyfill](https://github.com/andyearnshaw/Intl.js/blob/master/src/12.datetimeformat.js).

Help with the above would be welcome!


Discuss
-------

We'd love to hear your thoughts on Project Fluent!  Whether you're a localizer
looking for a better way to express yourself in your language, or a developer
trying to make your app localizable and multilingual, or a hacker looking for
a project to contribute to, please do get in touch on the mailing list and the
IRC channel.

 - mailing list: https://lists.mozilla.org/listinfo/tools-l10n
 - IRC channel: [irc://irc.mozilla.org/l20n](irc://irc.mozilla.org/l20n)


Get Involved
------------

python-fluent is open-source, licensed under the Apache License, Version 2.0.
We encourage everyone to take a look at our code and we'll listen to your
feedback.
