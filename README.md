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

    pip install fluent

Usage
-----

Fluent uses unicode everywhere internally, and doesn't accept bytestrings, so
that you avoid problems down the road when non-ASCII characters start appearing
in FTL files. If you are using Python 2, for the following examples you will
first need to do:

    >>> from __future__ import unicode_literals

or add unicode literal markers to strings.

To generate translations from this Python libary, you start with the
`MessageContext` class:

    >>> from fluent.context import MessageContext

You pass a list of locales to the constructor - the first being the desired
locale, with fallbacks after that:

    >>> context = MessageContext(["en-US"], use_isolating=False)

Here we have passed `use_isolating=False` which disables the use of Unicode bidi
isolation characters, to make the example output easier to read. If you might
have mixed right-to-left and left-to-right output from your messages then you
should omit this parameter to get the default `True` value.

You must then add messages. These would normally come from a `.ftl` file stored
on disk, here we will just add them directly:

    >>> context.add_messages("""
    ... welcome = Welcome to this great app!
    ... greet-by-name = Hello, { $name }!
    ... """)

To generate translations, use the `format` method, passing a message ID and an
optional dictionary of substitution parameters. If the the message ID is not
found, a `LookupError` is raised. Otherwise, as per the Fluent philosophy, the
implementation tries hard to generate *something* even if there are errors. The
`format` method therefore returns a tuple containing `(translated string,
errors)`, as below.

    >>> translated, errs = context.format('welcome')
    >>> translated
    "Welcome to this great app!"
    >>> errs
    []

    >>> translated, errs = context.format('greet-by-name', {'name': 'Jane'})
    >>> translated
    "Hello, Jane!"

    >>> translated, errs = context.format('greet-by-name', {})
    >>> translated
    "Hello, name!"
    >>> errs
    [FluentReferenceError('Unknown external: name')]

The use of `LookupError` for missing messages also means that you can choose to
fall back to a default locale. If you need this, it is expected that you will
wrap use of `MessageContext.format` in your own utility functions that implement
your fallback strategy.

See also the 'Error handling' section below for more information on errors.


Numbers
-------

When rendering translations, Fluent passes any numeric arguments (int or float)
through locale-aware formatting functions:

    >>> context.add_messages("show-total-points = You have { $points } points.")
    >>> val, errs = context.format("show-total-points", {'points': 1234567})
    >>> val
    'You have 1,234,567 points.'


You can specify your own formatting options on the arguments passed in by
wrapping your numeric arguments with `fluent.types.fluent_number`:

    >>> from fluent.types import fluent_number
    >>> points = fluent_number(1234567, useGrouping=False)
    >>> context.format("show-total-points", {'points': points})[0]
    'You have 1234567 points.'

    >>> amount = fluent_number(1234.56, style="currency", currency="USD")
    >>> context.add_messages("your-balance = Your balance is { $amount }")
    >>> context.format("your-balance", {'amount': amount})[0]
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
    >>> context.add_messages("today-is = Today is { $today }")
    >>> val, errs = context.format("today-is", {"today": date.today() })
    >>> val
    'Today is Jun 16, 2018'

You can explicitly call the `DATETIME` builtin to specify options:

    >>> context.add_messages('today-is = Today is { DATETIME($today, dateStyle: "short") }')

See the [DATETIME
docs](https://projectfluent.org/fluent/guide/functions.html#datetime). However,
currently the only supported options to `DATETIME` are:

* `timeZone`
* `dateStyle` and `timeStyle` which are [proposed
  additions](https://github.com/tc39/proposal-ecma402-datetime-style) to the ECMA i18n spec.

To specify options from Python code, use `fluent.types.fluent_date`:

    >>> from fluent.types import fluent_date
    >>> today = date.today()
    >>> short_today = fluent_date(today, dateStyle='short')
    >>> val, errs = context.format("today-is", {"today": short_today })
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

        >>> context.add_messages("now-is = Now is { $now }")
        >>> val, errs = context.format("now-is",
        ...    {"now": fluent_date(utcnow,
        ...                        timeZone="Europe/Moscow",
        ...                        dateStyle="medium",
        ...                        timeStyle="medium")})
        >>> val
        'Now is Jun 17, 2018, 3:15:05 PM'


Custom functions
----------------

You can add functions to the ones available to FTL authors by passing
a `functions` dictionary to the `MessageContext` constructor:


    >>> def happy(message, very=False):
    ...     message = "😄 " + message
    ...     if very:
    ...         message = message + " 😄"
    ...     return message

    >>> context = MessageContext(['en-US'], functions={'HAPPY': happy})
    >>> context.add_messages("""
    ... greet-by-name = Hello { HAPPY($name, very: 1) }
    ... """)
    >>> print(context.format('greet-by-name', {'name': 'Jane'})[0])
    Hello 😄 Jane 😄

These functions need to accept the following types of arguments:

* unicode strings (i.e. `unicode` on Python 2, `str` on Python 3)
* `fluent.types.FluentType` subclasses, namely:
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
or instances of a `FluentType` subclass as above. Return numbers and datetimes
should be converted to `FluentNumber` or `FluentDateType` subclasses using
`fluent.types.fluent_number` and `fluent.types.fluent_date` respectively.

The type signatures of custom functions will be checked before they are used, to
ensure the right the numnber of positional arguments are used, and only
available keyword arguments are used - otherwise a `TypeError` will be appended
to the `errors` list. Using `*args` or `**kwargs` to allow any number of
positional or keyword arguments is supported, but you should ensure that your
function actually does allow all positional or keyword arguemtns.

If you want to override the detected type signature (for example, to limit the
arguments that can be used in an FTL file, or to provide a proper signature for
a function that has a signature using `*args` and `**kwargs` but is more
restricted in reality), you can add an `ftl_arg_spec` attribute to the function.
The value should be a two-tuple containing 1) a integer specifying the number of
positional arguments, and 2) a list of allowed keyword arguments. For example,
for a custom function `my_func` the following will stop the `restricted` keyword
argument from being used from FTL files, while allowing `allowed`, and requiring
that a single positional argument is passed:

    def my_func(arg1, allowed=None, restricted=None):
        pass

    my_func.ftl_arg_spec = (1, ['allowed'])


Error handling
--------------

The Fluent philosophy is to try to recover from errors, and not throw
exceptions, on the basis that a partial translation is usually better than one
that is entirely missing or a 500 page.

python-fluent adopts that philosophy, but also tries to abide by the Zen of
Python - “Errors should never pass silently. Unless explicitly silenced.”

The combination of these two different philosophies works as follows:

* Errors made by **translators** in the contents of FTL files do not raise
  exceptions. Instead the errors are collected in the `errors` argument returned
  by `MessageContext.format`, and some kind of substitute string is returned.
  For example, if a non-existent term `-brand-name` is referenced from a
  message, the string `-brand-name` is inserted into the returned string.

  Also, if the translator uses a function and passes the wrong number of
  positional arguments, or unavailable keyword arguments, this error will be
  caught and reported, without allowing the exception to propagate.

* Exceptions triggered by **developer** errors (whether the authors of
  python-fluent or a user of python-fluent) are not caught, but are allowed to
  propagate. For example, an incorrect message ID passed to
  `MessageContext.format` is most likely a developer error (a typo in the
  message ID), and so causes an exception to be raised. Exceptions raised by
  custom functions are also assumed to be developer errors (as documented above,
  these functions should not raise exceptions), and are not caught.


Security
--------

You should not pass untrusted FTL code to `MessageContext.add_messages`. This is
because carefully constructed messages could potentially cause large resource
usage (CPU time and memory). However, the `InterpretingMessageContext`
implementation (see below) does have some protection against these attacks,
although it may not be foolproof.

CompilingMessageContext and InterpretingMessageContext
------------------------------------------------------

python-fluent comes with two implementations of `MessageContext`. The default is
`fluent.context.CompilingMessageContext`, which is what you get under the alias
as `fluent.context.MessageContext`. This works by compiling a set of FTL
messages to a set of Python functions, which results in very good performance
(see below for more info).

The alternative is `fluent.context.InterpretingMessageContext`, which implements
an interpreter for the FTL Abstract Syntax Tree.

While the two implementations have the same API, and return the same values
under most situations, there are some differences, as follows:

* `InterpretingMessageContext` has some protection against malicious FTL input
  which could attempt things like a [billion laughs
  attack](https://en.wikipedia.org/wiki/Billion_laughs_attack) to consume a large amount
  of memory or CPU time. For the sake of performance, `CompilingMessageContext` does not
  have these protections.

  It should be noted that both implementations are able to detect and stop
  infinite recursion errors (`CompilingMessageContext` does this at compile
  time), which is important to stop infinite loops and memory exhaustion which
  could otherwise occur due to accidental cyclic references in messages.

* While the error handling strategy for both implementations is the same, when
  errors occur (e.g. a missing value in the arguments dictionary, or a cyclic
  reference, or a string is passed to `NUMBER()` builtin), the exact errors
  returned by `format` may be different between the two implementations.

  Also, when an error occurs, in some cases (such as a cyclic reference), the
  error string embedded into the returned formatted message may be different.
  For cases where there is no error, the output is identical (or should be).

  Neither implementations guarantees that the exact errors returned will be the
  same between different versions of python-fluent.

Performance
-----------

Due to the strategy of compiling to Python, `CompilingMessageContext` has very
good performance, especially for the simple common cases. The
`tools/benchmark/benchmark.py` script includes some benchmarks that compare
speed to GNU gettext as a reference. Below is a rough summary:

For the simple but very common case of a message defining a static string,
`CompilingMessageContext.format` (the default implmentation) is very close to
GNU gettext, or much faster, depending on whether you are using Python 2 or 3,
and your Python implementation (e.g. CPython or PyPy). (The worst case we found
was 5% slower on CPython 2.7, and the best case was about 4 times faster for
PyPy2 5.1.2). For cases of substituting a single string into a message,
`CompilingMessageContext.format` is between 30% slower and 70% faster than an
equivalent implementation using GNU gettext and Python `%` interpolation.

For message where plural rules are involved, currently `CompilingMessageContext`
can be significantly slower than using GNU gettext, partly because fluent uses
plural rules from CLDR that can be much more complex (and correct) than the ones
that gettext normally does. Further work could be done to optimize some of these
cases though.

For more complex operations (for example, using locale-aware date and number
formatting), formatting messages can take a lot longer. Comparisons to GNU
gettext fall down at this point, because it doesn't include a lot of this
functionality. However, usually these types of messages make up a small fraction
of the number of internationalized strings in an application.

`InterpretingMessageContext` is, as you would expect, much slower that
`CompilingMessageContext`, often by a factor of 10, which is why it is not the
default. If you have a large set of messages, most likely
`CompilingMessageContext` will be a lot slower to format the first message
because it first compiles all the messages, whereas `InterpretingMessageContext`
does not have this compilation step.


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
