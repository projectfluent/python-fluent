Escaping and markup
-------------------

In some cases it is common to to have other kinds of markup mixed in to
translatable text, especially for things like HTML/web outputs. Handling these
requires extra functionality to ensure that everything is escaped properly,
especially external arguments that are passed in.

For example, suppose you need embedded HTML in your translated text::

  happy-birthday =
       Hello { $name }, <b>happy birthday!</b>

In this situation, it is important that ``$name`` is HTML-escaped. The rest of
the text needs to be treated as already escaped (i.e. it is HTML markup), so
that ``<b>`` is not changed to ``&lt;b&gt;``.

python-fluent supports this use case by allowing a list of ``escapers`` to be
passed to the ``FluentBundle`` constructor:

.. code-block:: python

   bundle = FluentBundle(['en'], escapers=[my_escaper])

An ``escaper`` is an object that defines the following set of attributes. The
object could be a module, or a simple namespace object you could create using
``types.SimpleNamespace`` (or ``fluent.runtime.utils.SimpleNamespace`` on Python 2), or
an instance of a class with appropriate methods defined. The attributes are:

- ``name`` - a simple text value that is used in error messages.

- ``select(**hints)``

  A callable that is used to decide whether or not to use this escaper for a
  given message (or message attribute). It is passed a number of hints as
  keyword arguments, currently only the following:

  - ``message_id`` - a string that is the name of the message or term. For terms
     it is a string with a leading dash - e.g. ``-brand-name``. For message
     attributes, it is a string in the form ``messsage-name.attribute-name``

In the future, probably more hints will be passed (for example, comments
attached to the message), so for future compatibility this callable should use
the ``**hints`` syntax to collect remaining keyword arguments.

The callable should return ``True`` if the escaper should be used for that
message, ``False`` otherwise. For every message and message attribute, the
``select`` callable of each escaper in the list of escapers is tried in turn,
and the first to return ``True`` is used.

- ``output_type`` - the type of values that are returned by ``escape``,
  ``mark_escape``, and ``join``, and therefore by the whole message.

- ``escape(text_to_be_escaped)``

  A callable that will escape the passed in text. It must return a value that is
  an instance of ``output_type`` (or a subclass).

  ``escape`` must also be able to handle values that have already been escaped
  without escaping a second time.

- ``mark_escaped(markup)``

  A callable that marks the passed in text as markup i.e. already escaped. It
  must return a value that is an instance of ``output_type`` (or a subclass).

- ``join(parts)``

  A callable that accepts an iterable of components, each of type
  ``output_type``, and combines them into a larger value of the same type.

- ``use_isolating``

  A boolean that determines whether the normal bidi isolating characters should
  be inserted. If it is ``None`` the value from the ``FluentBundle`` will be
  used, otherwise use ``True`` or ``False`` to override.

The escaping functions need to obey some rules:

- escape must be idempotent:

  ``escape(escape(text)) == escape(text)``

- escape must be a no-op on the output of ``mark_escaped``:

  ``escape(mark_escaped(text)) == mark_escaped(text)``

- ``mark_escaped`` should be distributive with string
  concatenation:

  ``join([mark_escaped(a), mark_escaped(b)]) == mark_escaped(a + b)``

Example
~~~~~~~

This example is for
`MarkupSafe <https://pypi.org/project/MarkupSafe/>`__:

.. code-block:: python

   from fluent.runtime.utils import SimpleNamespace
   from markupsafe import Markup, escape

   empty_markup = Markup('')

   html_escaper = SimpleNamespace(
       select=lambda message_id=None, **hints: message_id.endswith('-html'),
       output_type=Markup,
       mark_escaped=Markup,
       escape=escape,
       join=empty_markup.join,
       name='html_escaper',
       use_isolating=False,
   )

This escaper uses the convention that message IDs that end with
``-html`` are selected by this escaper. This will match
``message-html``, ``message.attr-html``, and ``-term-html``, for
example, but not ``message-html.attr``.

We have set ``use_isolating=False`` here because isolation characters
can cause problems in various HTML contexts - for example:

::

    signup-message-html =
      Hello guest - please remember to
      <a href="{ $signup_url}">make an account.</a>

Isolation characters around ``$signup_url`` will break the link. For HTML, you
should instead use the `bdi element
<https://developer.mozilla.org/en-US/docs/Web/HTML/Element/bdi>`__ in the FTL
messages when necessary.

Escaper compatibility
~~~~~~~~~~~~~~~~~~~~~

When using escapers that with messages that include other messages or terms,
some rules apply:

- A message or term with an escaper applied can include another message or term
  with no escaper applied (the included message will have ``escape`` called on
  its output).

- A message with an escaper applied can include a message or term with the same
  escaper applied.

- A message with an escaper applied cannot include a message or term with a
  different esacper applied - this will generate a ``TypeError`` in the list of
  errors returned.

- A message with no escaper applied cannot include a message with an escaper
  applied.
