Changelog
=========

fluent.runtime 0.4.0 (March 13, 2023)
-------------------------------------

* Drop support for Python 2.7 and 3.5 & support for Python 3.6 through 3.9 ([#163](https://github.com/projectfluent/python-fluent/pull/163))
* Add type hints ([#180](https://github.com/projectfluent/python-fluent/pull/180))

fluent.runtime 0.3.1 (May 20, 2020)
-----------------------------------

* Updated documentation to be hosted on https://projectfluent.org/python-fluent/fluent.runtime/.
* Updated package metadata.

fluent.runtime 0.3 (October 23, 2019)
-------------------------------------

* Added ``fluent.runtime.FluentResource`` and
  ``fluent.runtime.FluentBundle.add_resource``.
* Removed ``fluent.runtime.FluentBundle.add_messages``.
* Replaced ``bundle.format()`` with ``bundle.format_pattern(bundle.get_message().value)``.
* Added ``fluent.runtime.FluentLocalization`` as main entrypoint for applications.

fluent.runtime 0.2 (September 10, 2019)
---------------------------------------

* Support for Fluent spec 1.0 (``fluent.syntax`` 0.17), including parameterized
  terms.

fluent.runtime 0.1 (January 21, 2019)
-------------------------------------

First release to PyPI of ``fluent.runtime``. This release contains a
``FluentBundle`` implementation that can generate translations from FTL
messages. It targets the `Fluent 0.7 spec
<https://github.com/projectfluent/fluent/releases/tag/v0.7.0>`_.
