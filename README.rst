Project Fluent
==============

This is a collection of Python packages to use the `Fluent localization
system <http://projectfluent.org/>`__.

python-fluent consists of these packages:

``fluent.syntax``
-----------------

The `syntax package <fluent.syntax>`_ includes the parser, serializer, and traversal
utilities like Visitor and Transformer. You’re looking for this package
if you work on tooling for Fluent in Python.

``fluent.runtime``
------------------

The `runtime package <fluent.runtime>`__ includes the library required to use Fluent to localize
your Python application. It comes with a ``Localization`` class to use,
based on an implementation of ``FluentBundle``. It uses the tooling parser above
to read Fluent files.

``fluent.pygments``
-------------------

A `plugin for pygments <fluent.pygments>`_ to add syntax highlighting to Sphinx.

Discuss
-------

We’d love to hear your thoughts on Project Fluent! Whether you’re a
localizer looking for a better way to express yourself in your language,
or a developer trying to make your app localizable and multilingual, or
a hacker looking for a project to contribute to, please do get in touch
on the mailing list and the IRC channel.

-  Mozilla Discourse: https://discourse.mozilla.org/c/fluent
-  Matrix channel:
   `#fluent:mozilla.org <https://chat.mozilla.org/#/room/#fluent:mozilla.org>`__

Get Involved
------------

python-fluent is open-source, licensed under the Apache License, Version
2.0. We encourage everyone to take a look at our code and we’ll listen
to your feedback.
