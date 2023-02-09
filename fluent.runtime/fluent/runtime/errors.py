from typing import cast


class FluentFormatError(ValueError):
    def __eq__(self, other: object) -> bool:
        return ((other.__class__ == self.__class__) and cast(ValueError, other).args == self.args)


class FluentReferenceError(FluentFormatError):
    pass


class FluentCyclicReferenceError(FluentFormatError):
    pass
