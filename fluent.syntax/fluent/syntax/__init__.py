from typing import Any
from .ast import Resource
from .parser import FluentParser
from .serializer import FluentSerializer


def parse(source: str, **kwargs: Any) -> Resource:
    """Create an ast.Resource from a Fluent Syntax source.
    """
    parser = FluentParser(**kwargs)
    return parser.parse(source)


def serialize(resource: Resource, **kwargs: Any) -> str:
    """Serialize an ast.Resource to a unicode string.
    """
    serializer = FluentSerializer(**kwargs)
    return serializer.serialize(resource)
