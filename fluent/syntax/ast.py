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
    def __init__(self, id, value=None, attributes=None, comment=None):
        super(Message, self).__init__()
        self.id = id
        self.value = value
        self.attributes = attributes
        self.comment = comment

class Pattern(Node):
    def __init__(self, elements, quoted=False):
        super(Pattern, self).__init__()
        self.elements = elements
        self.quoted = quoted

class Expression(Node):
    def __init__(self):
        super(Expression, self).__init__()

class StringExpression(Node):
    def __init__(self, value):
        super(StringExpression, self).__init__()
        self.value = value

class Section(Node):
    def __init__(self, key, body=None, comment=None):
        super(Section, self).__init__(body, comment)
        self.key = key

class Identifier(Node):
    def __init__(self, name):
        super(Identifier, self).__init__()
        self.name = name




class Member(Node):
    def __init__(self, key, value, default=False):
        super(Member, self).__init__()
        self.key = key
        self.value = value
        self.default = default



class Placeable(Node):
    def __init__(self, expressions):
        super(Placeable, self).__init__()
        self.expressions = expressions


class SelectExpression(Node):
    def __init__(self, expression, variants=None):
        super(SelectExpression, self).__init__()
        self.expression = expression
        self.variants = variants


class MemberExpression(Node):
    def __init__(self, obj, keyword):
        super(MemberExpression, self).__init__()
        self.object = obj
        self.keyword = keyword


class CallExpression(Node):
    def __init__(self, callee, args):
        super(CallExpression, self).__init__()
        self.callee = callee
        self.args = args


class ExternalArgument(Node):
    def __init__(self, name):
        super(ExternalArgument, self).__init__()
        self.name = name


class KeyValueArg(Node):
    def __init__(self, name, value):
        super(KeyValueArg, self).__init__()
        self.name = name
        self.value = value


class EntityReference(Identifier):
    def __init__(self, name):
        super(EntityReference, self).__init__(name)


class FunctionReference(Identifier):
    def __init__(self, name):
        super(FunctionReference, self).__init__(name)


class Keyword(Identifier):
    def __init__(self, name, namespace=None):
        super(Keyword, self).__init__(name)
        self.namespace = namespace


class Number(Node):
    def __init__(self, value):
        super(Number, self).__init__()
        self.value = value


class TextElement(Node):
    def __init__(self, value):
        super(TextElement, self).__init__()
        self.value = value


class Comment(Node):
    def __init__(self, content):
        super(Comment, self).__init__()
        self.content = content


class JunkEntry(Node):
    def __init__(self, content):
        super(JunkEntry, self).__init__()
        self.content = content
