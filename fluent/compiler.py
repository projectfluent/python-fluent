from __future__ import absolute_import, unicode_literals

import attr
import six

from . import codegen
from .exceptions import FluentCyclicReferenceError, FluentReferenceError
from .syntax.ast import (AttributeExpression, CallExpression, ExternalArgument, Message, MessageReference,
                         NamedArgument, NumberExpression, Pattern, Placeable, SelectExpression, StringExpression, Term,
                         TextElement, VariantExpression, VariantName)


@attr.s
class CompilerEnvironment(object):
    locale = attr.ib()
    use_isolating = attr.ib()
    message_mapping = attr.ib(factory=dict)
    errors = attr.ib(factory=list)


def compile_messages(messages, locale, use_isolating=True):
    """
    Compile a dictionary of {id: Message/Term objects} to a Python module,
    and return a dictionary mapping the message IDs to Python functions
    """
    module, message_mapping, module_globals = messages_to_module(messages, locale,
                                                                 use_isolating=use_isolating, strict=False)
    # TODO - it would be nice to be able to get back to FTL source file lines,
    # if were knew what they were, and pass absolute filename that to 'compile'
    # builtin as the filepath. Instead of that just use 'exec' for now.
    exec(module.as_source_code(), module_globals)
    retval = {}
    for key, val in message_mapping.items():
        try:
            retval[six.text_type(key)] = module_globals[val]
        except KeyError:
            pass

    return retval


def messages_to_module(messages, locale, use_isolating=True, strict=False):
    """
    Compile a set of messages to a Python module, returning a tuple:
    (Python source code as a string, dictionary mapping message IDs to Python functions)

    If strict=True is passed, raise exceptions for any errors instead of suppressing them.
    """
    compile_env = CompilerEnvironment(
        locale=locale,
        use_isolating=use_isolating
    )
    # Setup globals, and reserve names for them
    module_globals = {
        'FluentReferenceError': FluentReferenceError,
    }
    module_globals.update(six.moves.builtins.__dict__)
    module = codegen.Module()
    for k in module_globals:
        name = module.reserve_name(k)
        assert name == k

    # Reserve names for function arguments
    for arg in MESSAGE_FUNCTION_ARGS:
        module.reserve_function_arg_name(arg)

    # Pass one, find all the names, so that we can populate message_mapping,
    # which is need for compilation.
    for msg_id, msg in messages.items():
        # TODO - handle duplicate names correctly
        function_name = module.reserve_name(msg_id)
        compile_env.message_mapping[msg_id] = function_name

    # Pass 2, actual compilation
    for msg_id, msg in messages.items():
        function_name = compile_env.message_mapping[msg_id]
        try:
            function = compile_message(msg, function_name, module, compile_env)
        except Exception as e:
            compile_env.errors.append(e)
            if strict:
                raise
        else:
            module.add_function(function_name, function)
    return (module, compile_env.message_mapping, module_globals)


# TODO Need to choose args that are guaranteed not to clash with other generated
# names
MESSAGE_ARGS_NAME = "message_args"
ERRORS_NAME = "errors"

MESSAGE_FUNCTION_ARGS = [MESSAGE_ARGS_NAME, ERRORS_NAME]


def compile_message(msg, function_name, module, compile_env):
    msg_func = codegen.Function(parent_scope=module,
                                name=function_name,
                                args=MESSAGE_FUNCTION_ARGS)

    start = msg.value
    if not isinstance(start, Pattern):
        raise AssertionError("Not expecting object of type {0}".format(type(start)))

    return_expression = compile_expr(start, msg_func, compile_env)
    msg_func.add_return(codegen.Tuple(return_expression, codegen.VariableReference(ERRORS_NAME, msg_func)))
    return msg_func


def compile_expr(element, local_scope, compile_env):
    """
    Compiles a Fluent expression into a Python one, return
    an object of type codegen.Expression.

    This may also add statements into local_scope, which is assumed
    to be a function that returns a message, or a branch of that
    function.
    """

    # TODO cyclic reference errors. For this to be detected at compile time,
    # we've got to fully resolve everything referenced, and then get
    # the generated function to insert an error message at the appropriate
    # point.

    if isinstance(element, Pattern):
        parts = []
        subelements = element.elements

        if len(subelements) == 1:
            if isinstance(subelements[0], TextElement):
                # Optimization for the very common case of a simple static string
                return compile_expr(subelements[0], local_scope, compile_env)
            elif isinstance(subelements[0], Placeable):
                # or a single placeable
                return compile_expr(subelements[0], local_scope, compile_env)

        for element in element.elements:
            parts.append(compile_expr(element, local_scope, compile_env))

        return codegen.StringJoin(parts)
    elif isinstance(element, TextElement):
        return codegen.String(element.value)
    elif isinstance(element, StringExpression):
        return codegen.String(element.value)
    elif isinstance(element, Placeable):
        return compile_expr(element.expression, local_scope, compile_env)
    elif isinstance(element, MessageReference):
        name = element.id.name
        if name in compile_env.message_mapping:
            tmp_name = local_scope.reserve_name('_tmp')
            local_scope.add_assignment(
                (tmp_name, ERRORS_NAME),
                codegen.FunctionCall(compile_env.message_mapping[name],
                                     [codegen.VariableReference(a, local_scope) for a in MESSAGE_FUNCTION_ARGS],
                                     local_scope))

            return codegen.VariableReference(tmp_name, local_scope)

        else:
            if name.startswith('-'):
                error = FluentReferenceError("Unknown term: {0}".format(name))
            else:
                error = FluentReferenceError("Unknown message: {0}".format(name))
            add_msg_error(local_scope, error)
            return codegen.String(name)

    raise NotImplementedError("Cannot handle object of type {0}"
                              .format(type(element).__name__))


def add_msg_error(local_scope, exception):
    """
    Given a scope and an exception object, add the code
    to the scope needed to generate that add that exception
    to the returned errors list
    """
    # ObjectCreation checks that the exception name is available in the scope,
    # so we don't need to do that.
    local_scope.statements.append(
        codegen.Verbatim(
            "{0}.append({1})".format(
                ERRORS_NAME,
                codegen.ObjectCreation(exception.__class__.__name__,
                                       [codegen.String(exception.args[0])],
                                       local_scope).as_source_code())))
