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

    >>> context = MessageContext(["en-US"])

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


When rendering translations, Fluent passes any numeric arguments (int or float)
through locale-aware formatting functions:

    >>> context.add_messages("show-total-points = You have { $points } points.")
    >>> val, errs = context.format("show-total-points", {'points': 1234567})
    >>> val
    'You have 1,234,567 points.'


You can specify you own formatting options on the arguments passed in by
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



TODO
----

Unimplemented features:

- [ ] All handling of datetime objects and `DATETIME` builtin function.
- [ ] Some `MessageContext` options e.g. use_isolating
- [ ] DOS protection - `MAX_PLACEABLE_LENGTH`
- [ ] Infinite recursion protection
- [ ] decimal.Decimal support
- [ ] Other parts of code that have TODO in them!


Help with the above would be welcome!

Known limitations and bugs
--------------------------

These are also 'TODO' items but might be harder to address due to blocks
elsewhere.

* We do not yet support `NUMBER(..., currencyDisplay="name")` - see
  https://github.com/python-babel/babel/issues/578


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
