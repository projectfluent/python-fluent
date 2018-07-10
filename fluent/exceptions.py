from __future__ import absolute_import, unicode_literals


class FluentFormatError(ValueError):
    def __eq__(self, other):
        return ((other.__class__ == self.__class__) and
                other.args == self.args)


class FluentReferenceError(FluentFormatError):
    pass


class FluentCyclicReferenceError(FluentFormatError):
    pass
