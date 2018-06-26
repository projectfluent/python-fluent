from __future__ import absolute_import, unicode_literals

from .syntax.ast import (AttributeExpression, CallExpression, ExternalArgument, Message, MessageReference,
                         NamedArgument, NumberExpression, Pattern, Placeable, SelectExpression, StringExpression, Term,
                         TextElement, VariantExpression, VariantName)

from . import codegen


import attr


@attr.s
class CompilerEnvironment(object):
    locale = attr.ib()
    errors = attr.ib()
    use_isolating = attr.ib()


def compile_messages(messages, locale, use_isolating=True):
    """
    Compile a dictionary of {id: Message/Term objects} to a Python module,
    and return a dictionary mapping the message IDs to Python functions
    """
    module, message_mapping = messages_to_module(messages, locale, use_isolating=use_isolating, strict=False)
    module_globals = {}
    # TODO - it would be nice to be able to get back to FTL source file lines,
    # if were knew what they were, and pass absolute filename that to 'compile'
    # builtin as the filepath. Instead of that just use 'exec' for now.
    exec(module.as_source_code(), module_globals)
    retval = {}
    for key, val in message_mapping.items():
        retval[key] = module_globals[val]

    return retval


def messages_to_module(messages, locale, use_isolating=True, strict=False):
    message_mapping = {}
    module = codegen.Module()
    compile_env = CompilerEnvironment(
        locale=locale,
        errors=[],
        use_isolating=use_isolating
    )
    for msg_id, msg in messages.items():
        function_name = module.reserve_name(msg_id)
        try:
            function = compile_message(msg, function_name, module, compile_env)
        except Exception as e:
            compile_env.errors.append(e)
            if strict:
                raise
        else:
            message_mapping[msg_id] = function_name
            module.add_function(function_name, function)
    return module, message_mapping


# TODO Need to choose args that are guaranteed not to clash with other generated
# names
MESSAGE_ARGS_NAME = "message_args"
ERRORS_NAME = "errors"


def compile_message(msg, function_name, module, compile_env):
    msg_func = codegen.Function(parent_scope=module,
                                name=function_name,
                                args=[MESSAGE_ARGS_NAME, ERRORS_NAME])

    start = msg.value
    if not isinstance(start, Pattern):
        raise AssertionError("Not expecting object of type {0}".format(type(start)))

    return_expression = compile_expr(start, msg_func, compile_env)
    msg_func.add_return(codegen.Tuple(return_expression, codegen.VariableReference(ERRORS_NAME)))
    return msg_func


def compile_expr(element, into_func, compile_env):
    # TODO cyclic reference errors. For this to be detected at compile time,
    # we've got to fully resolve everything referenced, and then get
    # the generated function to insert an error message at the appropriate
    # point.

    if isinstance(element, Pattern):
        parts = []
        subelements = element.elements

        if len(subelements) == 1 and isinstance(subelements[0], TextElement):
            # Optimization for the very common case of a simple static string
            return compile_expr(subelements[0], into_func, compile_env)

        for element in element.elements:
            parts.append(compile_expr(element, into_func, compile_env))

        return codegen.StringJoin(parts)
    elif isinstance(element, TextElement):
        return codegen.String(element.value)

    raise NotImplementedError("Cannot handle object of type {0}"
                              .format(type(element).__name__))
