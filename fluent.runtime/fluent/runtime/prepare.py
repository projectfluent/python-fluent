from __future__ import absolute_import, unicode_literals
from fluent.syntax import ast as FTL
from . import resolver


class Compiler(object):
    def __call__(self, item):
        if isinstance(item, FTL.BaseNode):
            return self.compile(item)
        if isinstance(item, (tuple, list)):
            return [self(elem) for elem in item]
        return item

    def compile(self, node):
        nodename = type(node).__name__
        if not hasattr(resolver, nodename):
            return node
        kwargs = vars(node).copy()
        for propname, propvalue in kwargs.items():
            kwargs[propname] = self(propvalue)
        handler = getattr(self, 'compile_' + nodename, self.compile_generic)
        return handler(nodename, **kwargs)

    def compile_generic(self, nodename, **kwargs):
        return getattr(resolver, nodename)(**kwargs)

    def compile_Placeable(self, _, expression, **kwargs):
        if isinstance(expression, resolver.Literal):
            return expression
        return resolver.Placeable(expression=expression, **kwargs)

    def compile_Pattern(self, _, elements, **kwargs):
        if (
            len(elements) == 1 and
            isinstance(elements[0], resolver.Placeable)
        ):
            # Don't isolate isolated placeables
            return resolver.NeverIsolatingPlaceable(elements[0].expression)
        if any(
            not isinstance(child, resolver.Literal)
            for child in elements
        ):
            return resolver.Pattern(elements=elements, **kwargs)
        if len(elements) == 1:
            return elements[0]
        return resolver.TextElement(
            ''.join(child(None) for child in elements)
        )
