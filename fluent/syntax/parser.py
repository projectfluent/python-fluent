from . import stream
from . import ast


def parse(string):
    resource = ast.Resource()
    errors = []

    ps = stream.ParserStream(string)

    return [resource, errors]

class FTLParser():
    def parse(self, string, with_source=True, pos=False):
        _pos = ast.Node._pos
        ast.Node._pos = pos
        try:
            [resource, errors] = parse(string)
        finally:
            ast.Node._pos = _pos
        return [resource, errors]

    def parseResource(self, string, with_source=True, pos=False):
        [resource, errors] = \
            self.parse(string, with_source=with_source, pos=pos)
        return [resource.toJSON(), errors]
