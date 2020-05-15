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

python-fluent consists of these packages:

`fluent.syntax` ![fluent.syntax](https://github.com/projectfluent/python-fluent/workflows/fluent.syntax/badge.svg)
-------------------------------------------------------------------------------------------------------------------------

The syntax package includes the parser, serializer, and traversal utilities
like Visitor and Transformer. You're looking for this package if you work on tooling
for Fluent in Python.


`fluent.runtime` ![fluent.runtime](https://github.com/projectfluent/python-fluent/workflows/fluent.runtime/badge.svg)
---------------------------------------------------------------------------------------------------------------------------

This package includes the library required to use Fluent to localize your
Python application. It comes with a `Localization` class to use, based on
an implementation of bundle. It uses the tooling parser above to read
Fluent files.

`fluent.pygments`
-----------------

A plugin for pygments to add syntax highlighting to Sphinx.

Usage
-----

For fluent.runtime, see the [docs folder](fluent.runtime/docs) or [read them on
readthedocs.org](https://fluent-runtime.readthedocs.io/en/latest/).

Discuss
-------

We'd love to hear your thoughts on Project Fluent!  Whether you're a localizer
looking for a better way to express yourself in your language, or a developer
trying to make your app localizable and multilingual, or a hacker looking for
a project to contribute to, please do get in touch on the mailing list and the
IRC channel.

 - Mozilla Discourse: https://discourse.mozilla.org/c/fluent
 - Matrix channel: [#fluent:mozilla.org](https://chat.mozilla.org/#/room/#fluent:mozilla.org)


Get Involved
------------

python-fluent is open-source, licensed under the Apache License, Version 2.0.
We encourage everyone to take a look at our code and we'll listen to your
feedback.
