from __future__ import unicode_literals
import sys
import json


def to_json(value):
    if isinstance(value, Node):
        return value.to_json()
    if isinstance(value, list):
        return list(map(to_json, value))
    else:
        return value


def from_json(value):
    if isinstance(value, dict):
        cls = getattr(sys.modules[__name__], value["type"])
        args = {
            k: from_json(v)
            for k, v in value.items() if k != "type"
        }
        return cls(**args)
    if isinstance(value, list):
        return list(map(from_json, value))
    else:
        return value


class Node(object):
    def traverse(self, fun):
        """Postorder-traverse this node and apply `fun` to all child nodes.

        Traverse this node depth-first applying `fun` to subnodes and leaves.
        Children are processed before parents (postorder traversal).

        Return a new instance of the node.
        """

        def visit(value):
            """Call `fun` on `value` and its descendants."""
            if isinstance(value, Node):
                return value.traverse(fun)
            if isinstance(value, list):
                return fun(list(map(visit, value)))
            else:
                return fun(value)

        node = self.__class__(
            **{
                name: visit(value)
                for name, value in vars(self).items()
            }
        )

        return fun(node)

    def to_json(self):
        obj = {
            name: to_json(value)
            for name, value in vars(self).items()
        }
        obj.update(
            {'type': self.__class__.__name__}
        )
        return obj

    def __str__(self):
        return json.dumps(self.to_json())


class Resource(Node):
    def __init__(self, body=None, comment=None):
        super(Resource, self).__init__()
        self.body = body or []
        self.comment = comment


class Entry(Node):
    def __init__(self, span=None, annotations=None):
        super(Entry, self).__init__()
        self.span = span
        self.annotations = annotations or []

    def add_span(self, start, end):
        self.span = Span(start, end)

    def add_annotation(self, annot):
        self.annotations.append(annot)


class Message(Entry):
    def __init__(
            self, id, value=None, attributes=None, tags=None, comment=None,
            span=None, annotations=None):
        super(Message, self).__init__(span, annotations)
        self.id = id
        self.value = value
        self.attributes = attributes
        self.tags = tags
        self.comment = comment

class Pattern(Node):
    def __init__(self, elements):
        super(Pattern, self).__init__()
        self.elements = elements

class TextElement(Node):
    def __init__(self, value):
        super(TextElement, self).__init__()
        self.value = value

class Expression(Node):
    def __init__(self):
        super(Expression, self).__init__()

class StringExpression(Expression):
    def __init__(self, value):
        super(StringExpression, self).__init__()
        self.value = value

class NumberExpression(Expression):
    def __init__(self, value):
        super(NumberExpression, self).__init__()
        self.value = value

class MessageReference(Expression):
    def __init__(self, id):
        super(MessageReference, self).__init__()
        self.id = id

class ExternalArgument(Expression):
    def __init__(self, id):
        super(ExternalArgument, self).__init__()
        self.id = id

class SelectExpression(Expression):
    def __init__(self, expression, variants):
        super(SelectExpression, self).__init__()
        self.expression = expression
        self.variants = variants

class AttributeExpression(Expression):
    def __init__(self, id, name):
        super(AttributeExpression, self).__init__()
        self.id = id
        self.name = name

class VariantExpression(Expression):
    def __init__(self, id, key):
        super(VariantExpression, self).__init__()
        self.id = id
        self.key = key

class CallExpression(Expression):
    def __init__(self, callee, args):
        super(CallExpression, self).__init__()
        self.callee = callee
        self.args = args

class Attribute(Node):
    def __init__(self, id, value):
        super(Attribute, self).__init__()
        self.id = id
        self.value = value

class Tag(Node):
    def __init__(self, name):
        super(Tag, self).__init__()
        self.name = name

class Variant(Node):
    def __init__(self, key, value, default = False):
        super(Variant, self).__init__()
        self.key = key
        self.value = value
        self.default = default

class NamedArgument(Node):
    def __init__(self, name, val):
        super(NamedArgument, self).__init__()
        self.name = name
        self.val = val

class Identifier(Node):
    def __init__(self, name):
        super(Identifier, self).__init__()
        self.name = name

class Symbol(Identifier):
    def __init__(self, name):
        super(Symbol, self).__init__(name)

class Comment(Entry):
    def __init__(self, content=None, span=None, annotations=None):
        super(Comment, self).__init__(span, annotations)
        self.content = content

class Section(Entry):
    def __init__(self, name, comment=None, span=None, annotations=None):
        super(Section, self).__init__(span, annotations)
        self.name = name
        self.comment = comment

class Function(Identifier):
    def __init__(self, name):
        super(Function, self).__init__(name)

class Junk(Entry):
    def __init__(self, content=None, span=None, annotations=None):
        super(Junk, self).__init__(span, annotations)
        self.content = content


class Span(Node):
    def __init__(self, start, end):
        super(Span, self).__init__()
        self.start = start
        self.end = end


class Annotation(Node):
    def __init__(self, name, message, pos):
        super(Annotation, self).__init__()
        self.name = name
        self.message = message
        self.pos = pos
