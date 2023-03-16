Internals of fluent.runtime
===========================

The application-facing API for ``fluent.runtime`` is ``FluentLocalization``.
This is the binding providing basic functionality for using Fluent in a
project. ``FluentLocalization`` builds on top of ``FluentBundle`` on top of
``FluentResource``.

``FluentLocalization`` handles

* Basic binding as an application-level API
* Language fallback
* uses resource loaders like ``FluentResourceLoader`` to create ``FluentResource``

``FluentBundle`` handles

* Internationalization with plurals, number formatting, and date formatting
* Aggregating multiple Fluent resources with message and term references
* Functions exposed to Select and Call Expressions

``FluentResource`` handles parsing of Fluent syntax.

Determining which language to use, and which languages to fall back to is
outside of the scope of the ``fluent.runtime`` package. A concrete
application stack might have functionality for that. Otherwise it needs to
be built, `Babel <http://babel.pocoo.org/en/latest/>`_ has
`helpers <http://babel.pocoo.org/en/latest/api/core.html#babel.core.negotiate_locale>`_
for that. ``fluent.runtime`` uses Babel internally for the international
functionality.


These bindings benefit from being adapted to the stack. Say,
a Django project would configure the localization binding through 
``django.conf.settings``, and load Fluent files from the installed apps.

Subclassing FluentLocalization
------------------------------

In the :doc:`usage` documentation, we used ``DemoLocalization``, which we'll
use here to exemplify how to subclass ``FluentLocalization`` for the needs
of specific stacks.

.. code-block:: python

  from fluent.runtime import FluentLocalization, FluentResource
  class DemoLocalization(FluentLocalization):
    def __init__(self, fluent_content, locale='en', functions=None):
      # Call super() with one locale, no resources nor loader
      super(DemoLocalization, self).__init__([locale], [], None, functions=functions)
      self.resource = FluentResource(fluent_content)

This set up the custom class, passing ``locale`` and ``functions`` to the
base implementation. What's left to do is to customize the resource loading.

.. code-block:: python

    def _bundles(self):
      bundle = self._create_bundle(self.locales)
      bundle.add_resource(self.resource)
      yield bundle

That's all that we need for our demo purposes.

Using FluentBundle
------------------

The actual interaction with Fluent content is implemented in ``FluentBundle``.
Optimizations between the parsed content in ``FluentResource`` and a
representation suitable for the resolving of Patterns is also handled inside
``FluentBundle``.

.. code-block:: python

    >>> from fluent.runtime import FluentBundle, FluentResource

You pass a list of locales to the constructor - the first being the
desired locale, with fallbacks after that:

.. code-block:: python

    >>> bundle = FluentBundle(["en-US"])

The passed locales are used for internationalization purposes inside Fluent,
being plural forms, as well as formatting of values. The locales passed in
don't affect the loaded messages, handling multiple localizations and the
fallback from one to the other is done in the ``FluentLocalization`` class.

You must then add messages. These would normally come from a ``.ftl``
file stored on disk, here we will just add them directly:

.. code-block:: python

    >>> resource = FluentResource("""
    ... welcome = Welcome to this great app!
    ... greet-by-name = Hello, { $name }!
    ... """)
    >>> bundle.add_resource(resource)

To generate translations, use the ``get_message`` method to retrieve
a message from the bundle. This returns an object with ``value`` and
``attributes`` properties. The ``value`` can be ``None`` or an abstract pattern.
``attributes`` is a dictionary mapping attribute names to abstract patterns.
If the the message ID is not found, a ``LookupError`` is raised. An abstract
pattern is an implementation-dependent representation of a Pattern in the
Fluent syntax. Then use the ``format_pattern`` method, passing the message value
or one of its attributes and an optional dictionary of substitution parameters.
You should only pass patterns to ``format_pattern`` that you got from that same
bundle. As per the Fluent philosophy, the implementation tries hard to recover
from any formatting errors and generate the most human readable representation
of the value. The ``format_pattern`` method thereforereturns a tuple containing
``(translated string, errors)``, as below.

.. code-block:: python

    >>> welcome = bundle.get_message('welcome')
    >>> translated, errs = bundle.format_pattern(welcome.value)
    >>> translated
    "Welcome to this great app!"
    >>> errs
    []

    >>> greet = bundle.get_message('greet-by-name')
    >>> translated, errs = bundle.format_pattern(greet.value, {'name': 'Jane'})
    >>> translated
    'Hello, \u2068Jane\u2069!'

    >>> translated, errs = bundle.format_pattern(greet.value, {})
    >>> translated
    'Hello, \u2068{$name}\u2069!'
    >>> errs
    [FluentReferenceError('Unknown external: name')]

You will notice the extra characters ``\u2068`` and ``\u2069`` in the
output. These are Unicode bidi isolation characters that help to ensure
that the interpolated strings are handled correctly in the situation
where the text direction of the substitution might not match the text
direction of the localized text. These characters can be disabled if you
are sure that is not possible for your app by passing
``use_isolating=False`` to the ``FluentBundle`` constructor.
