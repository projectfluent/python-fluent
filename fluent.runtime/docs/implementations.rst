FluentBundle Implementations
============================

python-fluent comes with two implementations of ``FluentBundle``. The default is
``fluent.runtime.InterpretingFluentBundle``, which is what you get under the
alias ``fluent.runtime.FluentBundle``. It implements an interpreter for the FTL
Abstract Syntax Tree.

The alternative is ``fluent.runtime.CompilingFluentBundle``, which works by
compiling a set of FTL messages to a set of Python functions using Python `ast
<https://docs.python.org/3/library/ast.html>`_. This results in very good
performance (see below for more info).

While the two implementations have the same API, and return the same values
under most situations, there are some differences, as follows:

* ``InterpretingFluentBundle`` has some protection against malicious FTL input
  which could attempt things like a `billion laughs attack
  <https://en.wikipedia.org/wiki/Billion_laughs_attack>`_ to consume a large
  amount of memory or CPU time. For the sake of performance,
  ``CompilingFluentBundle`` does not have these protections.

  It should be noted that both implementations are able to detect and stop
  infinite recursion errors (``CompilingFluentBundle`` does this at compile
  time), which is important to stop infinite loops and memory exhaustion which
  could otherwise occur due to accidental cyclic references in messages.

* While the error handling strategy for both implementations is the same, when
  errors occur (e.g. a missing value in the arguments dictionary, or a cyclic
  reference, or a string is passed to ``NUMBER()`` builtin), the exact errors
  returned by ``format`` may be different between the two implementations.

  Also, when an error occurs, in some cases (such as a cyclic reference), the
  error string embedded into the returned formatted message may be different.
  For cases where there is no error, the output is identical (or should be).

  Neither implementations guarantees that the exact errors returned will be the
  same between different versions of ``fluent.runtime``.

Performance
-----------

Due to the strategy of compiling to Python, ``CompilingFluentBundle`` has very
good performance, especially for the simple common cases. The
``tools/benchmark/gettext_comparisons.py`` script includes some benchmarks that
compare speed to GNU gettext as a reference. Below is a rough summary:

For the simple but very common case of a message defining a static string,
``CompilingFluentBundle.format`` is very close to GNU gettext, or much faster,
depending on whether you are using Python 2 or 3, and your Python implementation
(e.g. CPython or PyPy). (The worst case we found was 5% faster than gettext on
CPython 2.7, and the best case was about 3.5 times faster for PyPy2 5.1.2). For
cases of substituting a single string into a message,
``CompilingFluentBundle.format`` is between 30% slower and 70% faster than an
equivalent implementation using GNU gettext and Python ``%`` interpolation.

For message where plural rules are involved, currently ``CompilingFluentBundle``
can be significantly slower than using GNU gettext, partly because it uses
plural rules from CLDR that can be much more complex (and correct) than the ones
that gettext normally does. Further work could be done to optimize some of these
cases though.

For more complex operations (for example, using locale-aware date and number
formatting), formatting messages can take a lot longer. Comparisons to GNU
gettext fall down at this point, because it doesn't include a lot of this
functionality. However, usually these types of messages make up a small fraction
of the number of internationalized strings in an application.

``InterpretingFluentBundle`` is, as you would expect, much slower that
``CompilingFluentBundle``, often by a factor of 10. In cases where there are a
large number of messages, ``CompilingFluentBundle`` will be a lot slower to
format the first message because it first compiles all the messages, whereas
``InterpretingFluentBundle`` does not have this compilation step, and tries to
reduce any up-front work to a minimum (sometimes at the cost of runtime
performance).


Security
--------

You should not pass un-trusted FTL code to ``FluentBundle.add_messages``. This
is because carefully constructed messages could potentially cause large resource
usage (CPU time and memory). The ``InterpretingFluentBundle`` implementation
does have some protection against these attacks, although it may not be
foolproof, while ``CompilingFluentBundle`` does not have any protection against
these attacks, either at compile time or run time.

``CompilingFluentBundle`` works by compiling FTL messages to Python `ast
<https://docs.python.org/3/library/ast.html>`_, which is passed to `compile
<https://docs.python.org/3/library/functions.html#compile>`_ and then `exec
<https://docs.python.org/3/library/functions.html#exec>`_. The use of ``exec``
like this is an established technique for high performance Python code, used in
template engines like Mako, Jinja2 and Genshi.

However, there can understandably be some concerns around the use of ``exec``
which can open up remote execution vulnerabilities. If this is of paramount
concern to you, you should consider using ``InterpretingFluentBundle`` instead
(which is the default).

To reduce the possibility of our use of ``exec`` harbouring security issues, the
following things are in place:

1. We generate `ast <https://docs.python.org/3/library/ast.html>`_ objects and
   not strings. This greatly reduces the security problems, since there is no
   possibility of a vulnerability due to incorrect string interpolation.

2. We use ``exec`` only on AST derived from FTL files, never on "end user input"
   (such as the arguments passed into ``FluentBundle.format``). This reduces the
   attack vector to only the situation where the source of your FTL files is
   potentially malicious or compromised.

3. We employ defence-in-depth techniques in our code generation and compiler
   implementation to reduce the possibility of a cleverly crafted FTL code
   producing security holes, and ensure these techniques have full test
   coverage.
