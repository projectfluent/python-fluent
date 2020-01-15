Project Fluent [![Build Status][travisimage]][travislink]
=========================================================

[travisimage]: https://travis-ci.org/projectfluent/python-fluent.svg?branch=master
[travislink]: https://travis-ci.org/projectfluent/python-fluent

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

python-fluent consists of these packages:

* `fluent.syntax` - includes AST classes and parser. Most end users will not
  need this directly. Documentation coming soon!

  To install:

        pip install fluent.syntax


* `fluent.runtime` - methods for generating translations from FTL files.

  To install:

        pip install fluent.runtime

  (The correct version of ``fluent.syntax`` will be installed automatically)

* `fluent.pygments` - a plugin for pygments to add syntax highlighting to Sphinx.

    To install:

        pip install fluent.pygments

PyPI also contains an old `fluent` package which is an older version of just
`fluent.syntax`.

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
 - IRC channel: [irc://irc.mozilla.org/l20n](irc://irc.mozilla.org/l20n)


Get Involved
------------

python-fluent is open-source, licensed under the Apache License, Version 2.0.
We encourage everyone to take a look at our code and we'll listen to your
feedback.
