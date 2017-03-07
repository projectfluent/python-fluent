from __future__ import unicode_literals
import json


def to_json(value):
    if isinstance(value, Node):
        return value.toJSON()
    if isinstance(value, list):
        return list(map(to_json, value))
    else:
        return value


class Node(object):
    _pos = False

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

    def toJSON(self):
        obj = {
            name: to_json(value)
            for name, value in vars(self).items()
        }
        obj.update(
            {'type': self.__class__.__name__}
        )
        return obj

    def __str__(self):
        return json.dumps(self.toJSON())

    def setPosition(self, start, end):
        if Node._pos is False:
            return

        self._pos = {
            "start": start,
            "end": end
        }


class NodeList(Node):
    def __init__(self, body=None, comment=None):
        super(NodeList, self).__init__()
        self.body = body or []
        self.comment = comment

    def entities(self):
        for entry in self.body:
            if isinstance(entry, Entity):
                yield entry
            if isinstance(entry, Section):
                for entity in entry.entities():
                    yield entity


class Resource(NodeList):
    def __init__(self, body=None, comment=None):
        super(Resource, self).__init__(body, comment)

class Entry(Node):
    def __init__(self):
        super(Entry, self).__init__()

class Message(Entry):
    def __init__(self, id, value=None, attrs=None, tags=None, comment=None):
        super(Message, self).__init__()
        self.id = id
        self.value = value
        self.attributes = attrs
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

class Comment(Node):
    def __init__(self, content):
        super(Comment, self).__init__()
        self.content = content

class Section(Node):
    def __init__(self, name, comment=None):
        super(Section, self).__init__()
        self.name = name
        self.comment = comment

class Function(Identifier):
    def __init__(self, name):
        super(Function, self).__init__(name)

class JunkEntry(Node):
    def __init__(self, content):
        super(JunkEntry, self).__init__()
        self.content = content
