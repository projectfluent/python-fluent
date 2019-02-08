from __future__ import unicode_literals
import sys
import json


class Visitor(object):
    '''Read-only visitor pattern.

    Subclass this to gather information from an AST.
    To generally define which nodes not to descend in to, overload
    `generic_visit`.
    To handle specific node types, add methods like `visit_Pattern`.
    The boolean value of the returned value determines if the visitor
    descends into the children of the given AST node.
    '''
    def visit(self, value):
        if isinstance(value, BaseNode):
            self.visit_node(value)
        if isinstance(value, list):
            for node in value:
                self.visit(node)

    def visit_node(self, node):
        nodename = type(node).__name__
        visit = getattr(self, 'visit_{}'.format(nodename), self.generic_visit)
        should_descend = visit(node)
        if not should_descend:
            return
        for propname, propvalue in vars(node).items():
            self.visit(propvalue)

    def generic_visit(self, node):
        return True


class ContextVisitor(object):
    '''Visitor baseclass that collects results.
    '''
    def visit(self, value):
        if isinstance(value, BaseNode):
            return self.visit_node(value)
        if isinstance(value, list):
            return self.value([
                self.visit(node) for node in value
            ])
        return self.value(value)

    def visit_node(self, node):
        nodename = type(node).__name__
        enter = getattr(self, 'enter_{}'.format(nodename), self.generic_enter)
        newprops = {}
        should_descend = enter(node)
        if should_descend:
            for propname, propvalue in vars(node).items():
                newprops[propname] = self.visit(propvalue)
        exit = getattr(self, 'exit_{}'.format(nodename), self.generic_exit)
        return exit(node, newprops)

    def generic_enter(self, node):
        yield True

    def generic_exit(self, node, props):
        return node

    def value(self, value):
        return value


def to_json(value, fn=None):
    if isinstance(value, BaseNode):
        return value.to_json(fn)
    if isinstance(value, list):
        return list(to_json(item, fn) for item in value)
    if isinstance(value, tuple):
        return list(to_json(item, fn) for item in value)
    else:
        return value


def from_json(value):
    if isinstance(value, dict):
        cls = getattr(sys.modules[__name__], value['type'])
        args = {
            k: from_json(v)
            for k, v in value.items()
            if k != 'type'
        }
        return cls(**args)
    if isinstance(value, list):
        return list(map(from_json, value))
    else:
        return value


def scalars_equal(node1, node2, ignored_fields):
    """Compare two nodes which are not lists."""

    if type(node1) != type(node2):
        return False

    if isinstance(node1, BaseNode):
        return node1.equals(node2, ignored_fields)

    return node1 == node2


class Traversal(ContextVisitor):
    def __init__(self, fun):
        self.fun = fun

    def generic_exit(self, node, props):
        return self.fun(node.__class__(**props))

    def value(self, value):
        return self.fun(value)


class BaseNode(object):
    """Base class for all Fluent AST nodes.

    All productions described in the ASDL subclass BaseNode, including Span and
    Annotation.  Implements __str__, to_json and traverse.
    """

    def traverse(self, fun):
        """Postorder-traverse this node and apply `fun` to all child nodes.

        Traverse this node depth-first applying `fun` to subnodes and leaves.
        Children are processed before parents (postorder traversal).

        Return a new instance of the node.
        """

        return Traversal(fun).visit(self)

    def equals(self, other, ignored_fields=['span']):
        """Compare two nodes.

        Nodes are deeply compared on a field by field basis. If possible, False
        is returned early. When comparing attributes and variants in
        SelectExpressions, the order doesn't matter. By default, spans are not
        taken into account.
        """

        self_keys = set(vars(self).keys())
        other_keys = set(vars(other).keys())

        if ignored_fields:
            for key in ignored_fields:
                self_keys.discard(key)
                other_keys.discard(key)

        if self_keys != other_keys:
            return False

        for key in self_keys:
            field1 = getattr(self, key)
            field2 = getattr(other, key)

            # List-typed nodes are compared item-by-item.  When comparing
            # attributes and variants, the order of items doesn't matter.
            if isinstance(field1, list) and isinstance(field2, list):
                if len(field1) != len(field2):
                    return False

                # Sort elements of order-agnostic fields to ensure the
                # comparison is order-agnostic as well. Annotations should be
                # here too but they don't have sorting keys.
                if key in ('attributes', 'variants'):
                    field1 = sorted(field1, key=lambda elem: elem.sorting_key)
                    field2 = sorted(field2, key=lambda elem: elem.sorting_key)

                for elem1, elem2 in zip(field1, field2):
                    if not scalars_equal(elem1, elem2, ignored_fields):
                        return False

            elif not scalars_equal(field1, field2, ignored_fields):
                return False

        return True

    def to_json(self, fn=None):
        obj = {
            name: to_json(value, fn)
            for name, value in vars(self).items()
        }
        obj.update(
            {'type': self.__class__.__name__}
        )
        return fn(obj) if fn else obj

    def __str__(self):
        return json.dumps(self.to_json())


class SyntaxNode(BaseNode):
    """Base class for AST nodes which can have Spans."""

    def __init__(self, span=None, **kwargs):
        super(SyntaxNode, self).__init__(**kwargs)
        self.span = span

    def add_span(self, start, end):
        self.span = Span(start, end)


class Resource(SyntaxNode):
    def __init__(self, body=None, **kwargs):
        super(Resource, self).__init__(**kwargs)
        self.body = body or []


class Entry(SyntaxNode):
    """An abstract base class for useful elements of Resource.body."""


class Message(Entry):
    def __init__(self, id, value=None, attributes=None,
                 comment=None, **kwargs):
        super(Message, self).__init__(**kwargs)
        self.id = id
        self.value = value
        self.attributes = attributes or []
        self.comment = comment


class Term(Entry):
    def __init__(self, id, value, attributes=None,
                 comment=None, **kwargs):
        super(Term, self).__init__(**kwargs)
        self.id = id
        self.value = value
        self.attributes = attributes or []
        self.comment = comment


class VariantList(SyntaxNode):
    def __init__(self, variants, **kwargs):
        super(VariantList, self).__init__(**kwargs)
        self.variants = variants


class Pattern(SyntaxNode):
    def __init__(self, elements, **kwargs):
        super(Pattern, self).__init__(**kwargs)
        self.elements = elements


class PatternElement(SyntaxNode):
    """An abstract base class for elements of Patterns."""


class TextElement(PatternElement):
    def __init__(self, value, **kwargs):
        super(TextElement, self).__init__(**kwargs)
        self.value = value


class Placeable(PatternElement):
    def __init__(self, expression, **kwargs):
        super(Placeable, self).__init__(**kwargs)
        self.expression = expression


class Expression(SyntaxNode):
    """An abstract base class for expressions."""


class StringLiteral(Expression):
    def __init__(self, raw, value, **kwargs):
        super(StringLiteral, self).__init__(**kwargs)
        self.raw = raw
        self.value = value


class NumberLiteral(Expression):
    def __init__(self, value, **kwargs):
        super(NumberLiteral, self).__init__(**kwargs)
        self.value = value


class MessageReference(Expression):
    def __init__(self, id, **kwargs):
        super(MessageReference, self).__init__(**kwargs)
        self.id = id


class TermReference(Expression):
    def __init__(self, id, **kwargs):
        super(TermReference, self).__init__(**kwargs)
        self.id = id


class VariableReference(Expression):
    def __init__(self, id, **kwargs):
        super(VariableReference, self).__init__(**kwargs)
        self.id = id


class FunctionReference(Expression):
    def __init__(self, id, **kwargs):
        super(FunctionReference, self).__init__(**kwargs)
        self.id = id


class SelectExpression(Expression):
    def __init__(self, selector, variants, **kwargs):
        super(SelectExpression, self).__init__(**kwargs)
        self.selector = selector
        self.variants = variants


class AttributeExpression(Expression):
    def __init__(self, ref, name, **kwargs):
        super(AttributeExpression, self).__init__(**kwargs)
        self.ref = ref
        self.name = name


class VariantExpression(Expression):
    def __init__(self, ref, key, **kwargs):
        super(VariantExpression, self).__init__(**kwargs)
        self.ref = ref
        self.key = key


class CallExpression(Expression):
    def __init__(self, callee, positional=None, named=None, **kwargs):
        super(CallExpression, self).__init__(**kwargs)
        self.callee = callee
        self.positional = positional or []
        self.named = named or []


class Attribute(SyntaxNode):
    def __init__(self, id, value, **kwargs):
        super(Attribute, self).__init__(**kwargs)
        self.id = id
        self.value = value

    @property
    def sorting_key(self):
        return self.id.name


class Variant(SyntaxNode):
    def __init__(self, key, value, default=False, **kwargs):
        super(Variant, self).__init__(**kwargs)
        self.key = key
        self.value = value
        self.default = default

    @property
    def sorting_key(self):
        if isinstance(self.key, NumberLiteral):
            return self.key.value
        return self.key.name


class NamedArgument(SyntaxNode):
    def __init__(self, name, value, **kwargs):
        super(NamedArgument, self).__init__(**kwargs)
        self.name = name
        self.value = value


class Identifier(SyntaxNode):
    def __init__(self, name, **kwargs):
        super(Identifier, self).__init__(**kwargs)
        self.name = name


class BaseComment(Entry):
    def __init__(self, content=None, **kwargs):
        super(BaseComment, self).__init__(**kwargs)
        self.content = content


class Comment(BaseComment):
    def __init__(self, content=None, **kwargs):
        super(Comment, self).__init__(content, **kwargs)


class GroupComment(BaseComment):
    def __init__(self, content=None, **kwargs):
        super(GroupComment, self).__init__(content, **kwargs)


class ResourceComment(BaseComment):
    def __init__(self, content=None, **kwargs):
        super(ResourceComment, self).__init__(content, **kwargs)


class Junk(SyntaxNode):
    def __init__(self, content=None, annotations=None, **kwargs):
        super(Junk, self).__init__(**kwargs)
        self.content = content
        self.annotations = annotations or []

    def add_annotation(self, annot):
        self.annotations.append(annot)


class Span(BaseNode):
    def __init__(self, start, end, **kwargs):
        super(Span, self).__init__(**kwargs)
        self.start = start
        self.end = end


class Annotation(SyntaxNode):
    def __init__(self, code, args=None, message=None, **kwargs):
        super(Annotation, self).__init__(**kwargs)
        self.code = code
        self.args = args or []
        self.message = message
