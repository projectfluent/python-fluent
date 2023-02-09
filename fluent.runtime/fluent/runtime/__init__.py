from fluent.syntax import FluentParser
from fluent.syntax.ast import Resource

from .bundle import FluentBundle
from .fallback import FluentLocalization, AbstractResourceLoader, FluentResourceLoader


__all__ = [
    'FluentLocalization',
    'AbstractResourceLoader',
    'FluentResourceLoader',
    'FluentResource',
    'FluentBundle',
]


def FluentResource(source: str) -> Resource:
    parser = FluentParser()
    return parser.parse(source)
