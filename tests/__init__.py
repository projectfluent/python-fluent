from __future__ import absolute_import, unicode_literals

from fluent.context import CompilingMessageContext, InterpretingMessageContext

message_context_implementations = [
    (InterpretingMessageContext, "_Interpreter"),
    (CompilingMessageContext, "_Compiler")
]


def all_message_context_implementations(test_cls):
    """
    Modifies a TestCase subclass to run all test methods
    against all implementations of MessageContext
    """
    # Replace 'test_' methods with multiple versions, one for each
    # implementation.
    for attr_key, attr_value in list(test_cls.__dict__.items()):
        if attr_key.startswith('test_') and callable(attr_value):
            delattr(test_cls, attr_key)
            for cls, suffix in message_context_implementations:
                new_attr_key = attr_key + suffix
                setattr(test_cls, new_attr_key, attr_value)

    # Add an '__init__' that selects the right implementation.
    def __init__(self, methodName='runTest'):
        for cls, suffix in message_context_implementations:
            if methodName.endswith(suffix):
                self.message_context_cls = cls
        super(test_cls, self).__init__(methodName=methodName)

    test_cls.__init__ = __init__
    return test_cls
