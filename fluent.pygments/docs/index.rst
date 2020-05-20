Fluent Syntax Highlighting
==========================

The :py:mod:`fluent.pygments` library is built to do syntax highlighting
for `Fluent`_ files in Sphinx.


Installation
------------

.. code-block:: bash

   pip install fluent.pygments


Usage
-----

.. code-block:: rst


   .. code-block:: fluent

      my-key = Localize { -brand-name }

Example
-------

.. code-block:: fluent

   ### A resource comment for the whole file

   my-key = Localize { -brand-name }
   -brand-name = Fluent

   # $num is the number of strings to localize
   plurals = { $num ->
     [one] One string
    *[other] {$num} strings
   }
   an error ;-)
   Most-strings = are just simple strings.

.. _fluent: https://projectfluent.org/
