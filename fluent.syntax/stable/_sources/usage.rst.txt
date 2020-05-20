Using fluent.syntax
===================

The ``fluent.syntax`` package provides a parser, a serializer, and libraries
for analysis and processing of Fluent files.

Parsing
-------

To parse a full resource, you can use the :py:func:`fluent.syntax.parse`
shorthand:

.. code-block:: python

   from fluent.syntax import parse
   resource = parse("""
   ### Fluent resource comment

   first = creating a { $thing }
   second = more content
   """)

To parse a single :py:class:`fluent.syntax.ast.Message` or :py:class:`fluent.syntax.ast.Term`, use
:py:meth:`fluent.syntax.parser.FluentParser.parse_entry`:

.. code-block:: python

   from fluent.syntax.parser import FluentParser
   parser = FluentParser()
   key_message = parser.parse_entry("""
   ### Fluent resource comment

   key = value
   """)

Serialization
-------------

To create Fluent syntax from AST objects, use :py:func:`fluent.syntax.serialize` or
:py:class:`fluent.syntax.serializer.FluentSerializer`.

.. code-block:: python

   from fluent.syntax import serialize
   from fluent.syntax.serializer import FluentSerializer
   serialize(resource)
   serializer = FluentSerializer()
   serializer.serialize(resource)
   serializer.serialize_entry(key_message)

Analysis (Visitor)
------------------

To analyze an AST tree in a read-only fashion, you can subclass
:py:class:`fluent.syntax.visitor.Visitor`.

You overload individual :py:func:`visit_NodeName` methods to
handle nodes of that type, and then call into :py:func`self.generic_visit`
to continue iteration.

.. code-block:: python

   from fluent.syntax import visitor
   import re

   class WordCounter(visitor.Visitor):
       COUNTER = re.compile(r"[\w,.-]+")
       @classmethod
       def count(cls, node):
           wordcounter = cls()
           wordcounter.visit(node)
           return wordcounter.word_count
       def __init__(self):
           super()
           self.word_count = 0
       def visit_TextElement(self, node):
           self.word_count += len(self.COUNTER.findall(node.value))
           self.generic_visit(node)

   WordCounter.count(resource)
   WordCounter.count(key_message)

In-place Modification (Transformer)
-----------------------------------

Manipulation of an AST tree can be done in-place with a subclass of
:py:class:`fluent.syntax.visitor.Transformer`. The coding pattern matches that
of :py:class:`visitor.Visitor`, but you can modify the node in-place.
You can even return different types, or remove nodes alltogether.

.. code-block:: python

   class Skeleton(visitor.Transformer):
       def visit_SelectExpression(self, node):
           # This should do more checks, good enough for docs
           for variant in node.variants:
               if variant.default:
                   default_variant = variant
                   break
           template_variant = self.visit(default_variant)
           template_variant.default = False
           node.variants[:] = []
           for key in ('one', 'few', 'many'):
               variant = template_variant.clone()
               variant.key.name = key
               node.variants.append(variant)
           node.variants[-1].default = True
           return node
       def visit_TextElement(self, node):
         return None

   skeleton = Skeleton()
   skeleton.visit(key_message)
   WordCounter.count(key_message)
   # Returns 0.
   new_plural = skeleton.visit(parser.parse_entry("""
   with-plural = { $num ->
     [one] Using { -one-term-reference } to hide
    *[other] Using { $num } {-term-reference} as template
   }
   """))
   print(serializer.serialize_entry(new_plural))

This returns

.. code-block:: fluent

   with-plural =
       { $num ->
           [one] { $num }{ -term-reference }
           [few] { $num }{ -term-reference }
          *[many] { $num }{ -term-reference }
       }


.. warning::

   Serializing an AST tree that was created like this might not produce
   valid Fluent content.

