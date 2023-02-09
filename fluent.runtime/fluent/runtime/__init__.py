from fluent.syntax import FluentParser

from .bundle import FluentBundle
from .fallback import FluentLocalization, AbstractResourceLoader, FluentResourceLoader


__all__ = [
    'FluentLocalization',
    'AbstractResourceLoader',
    'FluentResourceLoader',
    'FluentResource',
    'FluentBundle',
]


def FluentResource(source):
    parser = FluentParser()
    return parser.parse(source)
