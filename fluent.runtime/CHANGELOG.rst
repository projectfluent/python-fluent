Changelog
=========

fluent.runtime development version (unreleased)
-----------------------------------------------

* Support for Fluent spec 0.8 (``fluent.syntax`` 0.10), including parameterized
  terms.
* Refined error handling regarding function calls to be more tolerant of errors
  in FTL files, while silencing developer errors less.
* Added ``CompilingFluentBundle`` implementation.

fluent.runtime 0.1 (January 21, 2019)
-------------------------------------

First release to PyPI of ``fluent.runtime``. This release contains a
``FluentBundle`` implementation that can generate translations from FTL
messages. It targets the `Fluent 0.7 spec
<https://github.com/projectfluent/fluent/releases/tag/v0.7.0>`_.
