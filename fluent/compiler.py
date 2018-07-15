from __future__ import absolute_import, unicode_literals

from collections import OrderedDict

import attr
import babel
import six

from . import codegen, runtime
from .exceptions import FluentCyclicReferenceError, FluentReferenceError
from .syntax.ast import (AttributeExpression, BaseNode, CallExpression, ExternalArgument, MessageReference,
                         NamedArgument, NumberExpression, Pattern, Placeable, SelectExpression, StringExpression,
                         TextElement, VariantExpression, VariantName)
from .types import FluentDateType, FluentNumber, FluentType
from .utils import args_match, inspect_function_args, numeric_to_native, partition

try:
    from functools import singledispatch
except ImportError:
    # Python < 3.4
    from singledispatch import singledispatch

text_type = six.text_type

# Unicode bidi isolation characters.
FSI = "\u2068"
PDI = "\u2069"

BUILTIN_NUMBER = 'NUMBER'
BUILTIN_DATETIME = 'DATETIME'

BUILTIN_RETURN_TYPES = {
    BUILTIN_NUMBER: FluentNumber,
    BUILTIN_DATETIME: FluentDateType,
}


MESSAGE_ARGS_NAME = "message_args"
ERRORS_NAME = "errors"
MESSAGE_FUNCTION_ARGS = [MESSAGE_ARGS_NAME, ERRORS_NAME]

VARIANT_NAME = "variant"
VARIANT_FUNCTION_KWARGS = {VARIANT_NAME: codegen.NoneExpr()}

LOCALE_NAME = "locale"

PLURAL_FORM_FOR_NUMBER_NAME = 'plural_form_for_number'


CLDR_PLURAL_FORMS = set([
    'zero',
    'one',
    'two',
    'few',
    'many',
    'other',
])


@attr.s
class CompilerEnvironment(object):
    locale = attr.ib()
    use_isolating = attr.ib()
    message_mapping = attr.ib(factory=dict)
    errors = attr.ib(factory=list)
    functions = attr.ib(factory=dict)
    function_renames = attr.ib(factory=dict)
    debug = attr.ib(default=False)
    functions_arg_spec = attr.ib(factory=dict)
    msg_ids_to_ast = attr.ib(factory=dict)

    def add_current_message_error(self, error):
        self.errors.append((self._current_message_id, error))


def compile_messages(messages, locale, use_isolating=True, functions=None, debug=False):
    """
    Compile a dictionary of {id: Message/Term objects} to a Python module,
    and returns a tuple:
       (dictionary mapping the message IDs to Python functions,
        error list)

    The error list is itself a list of two tuples:
       (message id, exception object)
    """
    if functions is None:
        functions = {}
    module, message_mapping, module_globals, errors = messages_to_module(
        messages, locale,
        use_isolating=use_isolating,
        functions=functions,
        debug=debug)
    # TODO - it would be nice to be able to get back to FTL source file lines,
    # if were knew what they were, and pass absolute filename that to 'compile'
    # builtin as the filepath. Instead of that just use 'exec' for now.
    exec(module.as_source_code(), module_globals)
    retval = {}
    for key, val in message_mapping.items():
        if key.startswith('-'):
            # term, shouldn't be in publicly available messages
            continue
        retval[six.text_type(key)] = module_globals[val]

    return (retval, errors)


def messages_to_module(messages, locale, use_isolating=True, functions=None, debug=False):
    """
    Compile a set of messages to a Python module, returning a tuple:
    (Python source code as a string, dictionary mapping message IDs to Python functions)
    """
    if functions is None:
        functions = {}

    msg_ids_to_ast = OrderedDict(get_message_functions(messages))

    compiler_env = CompilerEnvironment(
        locale=locale,
        use_isolating=use_isolating,
        functions=functions,
        debug=debug,
        functions_arg_spec={name: inspect_function_args(func)
                            for name, func in functions.items()},
        msg_ids_to_ast=msg_ids_to_ast,
    )
    # Setup globals, and reserve names for them
    module_globals = {
        k: getattr(runtime, k) for k in runtime.__all__
    }
    module_globals.update(six.moves.builtins.__dict__)
    module_globals[LOCALE_NAME] = locale

    # Return types of known functions.
    known_return_types = {}
    known_return_types.update(BUILTIN_RETURN_TYPES)
    known_return_types.update(runtime.RETURN_TYPES)

    # Plural form function
    plural_form_for_number_main = babel.plural.to_python(locale.plural_form)

    def plural_form_for_number(number):
        try:
            return plural_form_for_number_main(number)
        except TypeError:
            # This function can legitimately be passed strings if we incorrectly
            # guessed it was a CLDR category. So we ignore silently
            return None

    module_globals[PLURAL_FORM_FOR_NUMBER_NAME] = plural_form_for_number
    known_return_types[PLURAL_FORM_FOR_NUMBER_NAME] = text_type

    def get_name_properties(name):
        properties = {}
        if name in known_return_types:
            properties[codegen.PROPERTY_RETURN_TYPE] = known_return_types[name]
        return properties

    module = codegen.Module()
    for k in module_globals:
        name = module.reserve_name(k, properties=get_name_properties(k))
        # We should have chosen all our module_globals to avoid name conflicts:
        assert name == k

    # functions from context
    for name, func in functions.items():
        # These might clash, because we can't control what the user passed in.
        assigned_name = module.reserve_name(name, properties=get_name_properties(name))
        compiler_env.function_renames[name] = assigned_name
        module_globals[assigned_name] = func

    # Reserve names for function arguments, so that we always
    # know the name of these arguments without needing to do
    # lookups etc.
    for arg in (list(MESSAGE_FUNCTION_ARGS) + list(VARIANT_FUNCTION_KWARGS.keys())):
        module.reserve_function_arg_name(arg)

    # Pass one, find all the names, so that we can populate message_mapping,
    # which is needed for compilation.
    for msg_id, msg in msg_ids_to_ast.items():
        function_name = module.reserve_name(
            message_function_name_for_msg_id(msg_id))
        compiler_env.message_mapping[msg_id] = function_name

    # Pass 2, actual compilation
    for msg_id, msg in msg_ids_to_ast.items():
        compiler_env._current_message_id = msg_id
        function_name = compiler_env.message_mapping[msg_id]
        function = compile_message(msg, msg_id, function_name, module, compiler_env)
        del compiler_env._current_message_id
        module.add_function(function_name, function)

    module = codegen.simplify(module)
    return (module, compiler_env.message_mapping, module_globals, compiler_env.errors)


def get_message_functions(message_dict):
    for msg_id, msg in message_dict.items():
        if msg.value is None:
            # No body, skip it.
            pass
        else:
            yield (msg_id, msg)
        for msg_attr in msg.attributes:
            yield (message_id_for_attr(msg_id, msg_attr.id.name), msg_attr)


def message_id_for_attr(parent_msg_id, attr_name):
    return "{0}.{1}".format(parent_msg_id, attr_name)


def message_id_for_attr_expression(attr_expr):
    return message_id_for_attr(attr_expr.id.name, attr_expr.name.name)


def message_function_name_for_msg_id(msg_id):
    # Scope.reserve_name does further sanitising of name, which we don't need to
    # worry about.
    return msg_id.replace('.', '__').replace('-', '_')


def compile_message(msg, msg_id, function_name, module, compiler_env):
    start = msg.value
    if is_variant_definition_message(msg):
        func_kwargs = VARIANT_FUNCTION_KWARGS
    else:
        func_kwargs = None
    msg_func = codegen.Function(parent_scope=module,
                                name=function_name,
                                args=MESSAGE_FUNCTION_ARGS,
                                kwargs=func_kwargs,
                                debug=compiler_env.debug)

    if not isinstance(start, Pattern):
        raise AssertionError("Not expecting object of type {0}".format(type(start)))

    if contains_reference_cycle(msg, msg_id, compiler_env):
        error = FluentCyclicReferenceError("Cyclic reference in {0}".format(msg_id))
        add_static_msg_error(msg_func, error)
        compiler_env.add_current_message_error(error)
        return_expression = finalize_expr_as_string(make_fluent_none(None, module), msg_func, compiler_env)
    else:
        return_expression = compile_expr(start, msg_func, None, compiler_env)
    # > return ($return_expression, errors)
    msg_func.add_return(codegen.Tuple(return_expression, codegen.VariableReference(ERRORS_NAME, msg_func)))
    return msg_func


def is_variant_definition_message(msg):
    return contains_matching_node(msg, is_variant_definition_expression)


def contains_matching_node(start_node, predicate):
    checks = []

    def checker(node):
        if predicate(node):
            checks.append(True)

    traverse_ast(start_node, checker)
    return any(checks)


def traverse_ast(node, fun, exclude_attributes=None):
    """Postorder-traverse this node and apply `fun` to all child nodes.

    Traverse this node depth-first applying `fun` to subnodes and leaves.
    Children are processed before parents (postorder traversal).
    """

    def visit(value):
        """Call `fun` on `value` and its descendants."""
        if isinstance(value, BaseNode):
            return traverse_ast(value, fun)
        if isinstance(value, list):
            return fun(list(map(visit, value)))
        else:
            return fun(value)

    # Use all attributes found on the node
    parts = vars(node).items()
    for name, value in parts:
        if exclude_attributes is not None and name in exclude_attributes:
            continue
        visit(value)

    return fun(node)


def is_variant_definition_expression(expr):
    return (isinstance(expr, SelectExpression) and
            expr.expression is None)


def contains_reference_cycle(msg, msg_id, compiler_env):
    msg_ids_to_ast = compiler_env.msg_ids_to_ast
    return contains_matching_node_deep(
        msg,
        lambda node: (
            (isinstance(node, MessageReference) and
             node.id.name == msg_id) or
            (isinstance(node, AttributeExpression) and
             message_id_for_attr_expression(node) == msg_id) or
            (isinstance(node, AttributeExpression) and
             message_id_for_attr_expression(node) not in msg_ids_to_ast
             and node.id.name == msg_id)
        ),
        msg_ids_to_ast)


def contains_matching_node_deep(start_node, predicate, msg_ids_to_ast):
    checks = []

    checked_nodes = set([])

    # We don't recurse into message attributes, because a message and its
    # attributes are considered distinct. For example, the following is fine,
    # there is cycle, foo.attr is not reached from foo
    #
    #  foo = Foo
    #     .attr = { foo } Attribute

    exclude_attributes = ['attributes']

    def checker(node):
        node_id = id(node)
        if node_id in checked_nodes:
            # break infinite loop for this checking code
            return
        checked_nodes.add(node_id)

        if predicate(node):
            checks.append(True)
            return

        sub_node = None
        if isinstance(node, MessageReference):
            ref = node.id.name
            if ref in msg_ids_to_ast:
                sub_node = msg_ids_to_ast[ref]
        elif isinstance(node, AttributeExpression):
            ref = message_id_for_attr_expression(node)
            if ref in msg_ids_to_ast:
                sub_node = msg_ids_to_ast[ref]
            else:
                # Compiler falls back to parent ref in this situation,
                # so we have to as well to check for cycles
                parent_ref = node.id.name
                if parent_ref in msg_ids_to_ast:
                    sub_node = msg_ids_to_ast[parent_ref]

        if sub_node is not None:
            traverse_ast(sub_node, checker, exclude_attributes=exclude_attributes)
            if any(checks):
                return

        return

    traverse_ast(start_node, checker, exclude_attributes=exclude_attributes)
    return any(checks)


@singledispatch
def compile_expr(element, local_scope, parent_expr, compiler_env):
    """
    Compiles a Fluent expression into a Python one, return
    an object of type codegen.Expression.

    This may also add statements into local_scope, which is assumed
    to be a function that returns a message, or a branch of that
    function.
    """
    raise NotImplementedError("Cannot handle object of type {0}"
                              .format(type(element).__name__))


@compile_expr.register(Pattern)
def compile_expr_pattern(pattern, local_scope, parent_expr, compiler_env):
    parts = []
    subelements = pattern.elements

    use_isolating = compiler_env.use_isolating and len(subelements) > 1

    for element in pattern.elements:
        wrap_this_with_isolating = use_isolating and not isinstance(element, TextElement)
        if wrap_this_with_isolating:
            parts.append(codegen.String(FSI))
        parts.append(compile_expr(element, local_scope, pattern, compiler_env))
        if wrap_this_with_isolating:
            parts.append(codegen.String(PDI))

    # > ''.join($[p for p in parts])
    return codegen.StringJoin([finalize_expr_as_string(p, local_scope, compiler_env) for p in parts])


@compile_expr.register(TextElement)
def compile_expr_text(text, local_scope, parent_expr, compiler_env):
    return codegen.String(text.value)


@compile_expr.register(StringExpression)
def compile_expr_string_expression(expr, local_scope, parent_expr, compiler_env):
        return codegen.String(expr.value)


@compile_expr.register(NumberExpression)
def compile_expr_number_expression(expr, local_scope, parent_expr, compiler_env):
    number_expr = codegen.Number(numeric_to_native(expr.value))
    if is_NUMBER_call_expr(parent_expr):
        # Don't need two calls to NUMBER
        return number_expr
    if isinstance(parent_expr, SelectExpression):
        # Don't need to wrap in NUMBER for either the key expression or
        # the variant selector.
        return number_expr

    # > NUMBER($number_expr)
    return codegen.FunctionCall(BUILTIN_NUMBER,
                                [number_expr],
                                {},
                                local_scope)


@compile_expr.register(Placeable)
def compile_expr_placeable(placeable, local_scope, parent_expr, compiler_env):
    return compile_expr(placeable.expression, local_scope, placeable, compiler_env)


@compile_expr.register(MessageReference)
def compile_expr_message_reference(reference, local_scope, parent_expr, compiler_env):
    name = reference.id.name
    return do_message_call(name, local_scope, parent_expr, compiler_env)


def do_message_call(name, local_scope, parent_expr, compiler_env, call_kwargs=None):
    if call_kwargs is None:
        call_kwargs = {}
    if name in compiler_env.message_mapping:
        # Message functions always return strings, so we can type this variable:
        tmp_name = local_scope.reserve_name('_tmp', properties={codegen.PROPERTY_TYPE: text_type})
        msg_func_name = compiler_env.message_mapping[name]
        # > $tmp_name = $msg_func_name(message_args, errors)
        # OR:
        # > $tmp_name = $msg_func_name(message_args, errors, variant=$variant)
        local_scope.add_assignment(
            (tmp_name, ERRORS_NAME),
            codegen.FunctionCall(msg_func_name,
                                 [codegen.VariableReference(a, local_scope) for a in MESSAGE_FUNCTION_ARGS],
                                 call_kwargs,
                                 local_scope))

        # > $tmp_name
        return codegen.VariableReference(tmp_name, local_scope)

    else:
        if name.startswith('-'):
            error = FluentReferenceError("Unknown term: {0}".format(name))
        else:
            error = FluentReferenceError("Unknown message: {0}".format(name))
        add_static_msg_error(local_scope, error)
        compiler_env.add_current_message_error(error)
        return make_fluent_none(name, local_scope)


def make_fluent_none(name, local_scope):
    # > FluentNone(name)
    # OR
    # > FluentNone()
    return codegen.ObjectCreation('FluentNone',
                                  [codegen.String(name)] if name else [],
                                  {},
                                  local_scope)


@compile_expr.register(AttributeExpression)
def compile_expr_attribute_expression(attribute, local_scope, parent_expr, compiler_env):
    parent_id = attribute.id.name
    msg_id = message_id_for_attr_expression(attribute)
    if msg_id in compiler_env.message_mapping:
        return do_message_call(msg_id, local_scope, attribute, compiler_env)
    else:
        error = FluentReferenceError("Unknown attribute: {0}"
                                     .format(msg_id))
        add_static_msg_error(local_scope, error)
        compiler_env.add_current_message_error(error)
        # Fallback to parent
        return do_message_call(parent_id, local_scope, parent_expr, compiler_env)


@compile_expr.register(SelectExpression)
def compile_expr_select_expression(select_expr, local_scope, parent_expr, compiler_env):
    if is_variant_definition_expression(select_expr):
        return compile_expr_variant_definition(select_expr, local_scope, parent_expr, compiler_env)
    else:
        return compile_expr_select_definition(select_expr, local_scope, parent_expr, compiler_env)


def compile_expr_variant_definition(variant_expr, local_scope, parent_expr, compiler_env):
    if_statement = codegen.If(local_scope)
    return_name = local_scope.reserve_name('_ret')
    assigned_types = []
    for variant in variant_expr.variants:
        if variant.default:
            # This is default, so gets chosen if nothing else matches, or there
            # was no requested variant. Therefore we use the final 'else' block
            # with no condition.
            block = if_statement.else_block

            # However, we should report an error if the requested variant
            # doesn't match. TODO - in fact we ought to be able to detect all
            # missing variants at compile time, and therefore eliminate this
            # runtime check.
            no_match_if_statement = codegen.If(block)
            # > if variant is not None and variant != $variant.key
            no_match_condition = (
                codegen.And(
                    codegen.IsNot(
                        codegen.VariableReference(VARIANT_NAME, local_scope),
                        codegen.NoneExpr()
                    ),
                    codegen.NotEquals(
                        codegen.VariableReference(VARIANT_NAME, local_scope),
                        compile_expr(variant.key, local_scope, variant_expr, compiler_env)
                    )
                )
            )

            no_match_body = no_match_if_statement.add_if(no_match_condition)
            add_msg_error_with_expr(
                no_match_body,
                codegen.ObjectCreation(
                    "FluentReferenceError",
                    [codegen.MethodCall(
                        codegen.String("Unknown variant: {0}"),
                        "format",
                        [codegen.VariableReference(VARIANT_NAME, local_scope)]
                    )],
                    {},
                    local_scope
                )
            )
            block.statements.append(no_match_if_statement)
        else:
            # TODO - do we need to handle number/plural form matching for variants,
            # like in select expressions?

            # > if variant == $variant.key
            condition = codegen.Equals(codegen.VariableReference(VARIANT_NAME, local_scope),
                                       compile_expr(variant.key, local_scope, variant_expr, compiler_env))
            block = if_statement.add_if(condition)
        assigned_value = compile_expr(variant.value, block, variant_expr, compiler_env)
        block.add_assignment(return_name, assigned_value)
        assigned_types.append(assigned_value.type)

    # If all branches return the same type, record the type against the variable
    if assigned_types:
        first_type = assigned_types[0]
        if all(t == first_type for t in assigned_types):
            local_scope.set_name_properties(return_name, {codegen.PROPERTY_TYPE: first_type})

    local_scope.statements.append(if_statement)
    return codegen.VariableReference(return_name, local_scope)


def is_cldr_plural_form_key(key_expr):
    return (isinstance(key_expr, VariantName) and
            key_expr.name in CLDR_PLURAL_FORMS)


def compile_expr_select_definition(select_expr, local_scope, parent_expr, compiler_env):
    # This is very similar to compile_expr_variant_definition, but it is different
    # enough that implementing them together makes the code rather hard to understand
    if_statement = codegen.If(local_scope)
    key_tmp_name = local_scope.reserve_name('_key')
    key_value = compile_expr(select_expr.expression, local_scope, select_expr, compiler_env)
    local_scope.add_assignment(key_tmp_name, key_value)

    return_tmp_name = local_scope.reserve_name('_ret')

    need_plural_form = any(is_cldr_plural_form_key(variant.key)
                           for variant in select_expr.variants)
    if need_plural_form:
        plural_form_tmp_name = local_scope.reserve_name('_plural_form')
        plural_form_value = codegen.FunctionCall(PLURAL_FORM_FOR_NUMBER_NAME,
                                                 [codegen.VariableReference(key_tmp_name, local_scope)],
                                                 {},
                                                 local_scope)
        # > $plural_form_tmp_name = plural_form_for_number($key_tmp_name)
        local_scope.add_assignment(plural_form_tmp_name, plural_form_value)

    assigned_types = []
    for variant in select_expr.variants:
        if variant.default:
            # This is default, so gets chosen if nothing else matches, or there
            # was no requested variant. Therefore we use the final 'else' block
            # with no condition.
            block = if_statement.else_block
        else:
            # For cases like:
            #    { $arg ->
            #       [one] X
            #       [other] Y
            #      }
            # we can't be sure whether $arg is a string, and the 'one' and 'other'
            # keys are just strings, or whether $arg is a number and we need to
            # do a plural category comparison. So we have to do both. We can use equality
            # checks because they implicitly do a type check
            # > $key_tmp_name == $variant.key
            condition1 = codegen.Equals(codegen.VariableReference(key_tmp_name, local_scope),
                                        compile_expr(variant.key, local_scope, select_expr, compiler_env))

            if is_cldr_plural_form_key(variant.key):
                # > $plural_form_tmp_name == $variant.key
                condition2 = codegen.Equals(codegen.VariableReference(plural_form_tmp_name, local_scope),
                                            compile_expr(variant.key, local_scope, select_expr, compiler_env))
                condition = codegen.Or(condition1, condition2)
            else:
                condition = condition1
            block = if_statement.add_if(condition)
        assigned_value = compile_expr(variant.value, block, select_expr, compiler_env)
        block.add_assignment(return_tmp_name, assigned_value)
        assigned_types.append(assigned_value.type)

    if assigned_types:
        first_type = assigned_types[0]
        if all(t == first_type for t in assigned_types):
            local_scope.set_name_properties(return_tmp_name, {codegen.PROPERTY_TYPE: first_type})

    local_scope.statements.append(if_statement)
    return codegen.VariableReference(return_tmp_name, local_scope)


@compile_expr.register(VariantName)
def compile_expr_variant_name(name, local_scope, parent_expr, compiler_env):
    # TODO - handle numeric literals here?
    return codegen.String(name.name)


@compile_expr.register(VariantExpression)
def compile_expr_variant_expression(variant_expr, local_scope, parent_expr, compiler_env):
    msg_id = variant_expr.ref.id.name
    if msg_id in compiler_env.message_mapping:
        # TODO - compile time detection of missing variant
        return do_message_call(
            msg_id, local_scope, parent_expr, compiler_env,
            call_kwargs={VARIANT_NAME: compile_expr(variant_expr.key, local_scope, variant_expr, compiler_env)})
    else:
        error = FluentReferenceError("Unknown message: {0}"
                                     .format(msg_id))
        add_static_msg_error(local_scope, error)
        compiler_env.add_current_message_error(error)
        return make_fluent_none(msg_id, local_scope)


@compile_expr.register(ExternalArgument)
def compile_expr_external_argument(argument, local_scope, parent_expr, compiler_env):
    name = argument.id.name
    tmp_name = local_scope.reserve_name('_tmp')
    try_catch = codegen.TryCatch(codegen.VariableReference("LookupError", local_scope), local_scope)
    # Try block
    # > $tmp_name = message_args[$name]
    try_catch.try_block.add_assignment(
        tmp_name,
        codegen.DictLookup(codegen.VariableReference(MESSAGE_ARGS_NAME, local_scope),
                           codegen.String(name)))
    # Except block
    add_static_msg_error(try_catch.except_block, FluentReferenceError("Unknown external: {0}".format(name)))
    # > $tmp_name = FluentNone("$name")
    try_catch.except_block.add_assignment(
        tmp_name,
        make_fluent_none(name, local_scope))

    # Else block

    # In a select expression, we only care about matching against a
    # selector, not the other things (like wrapping in fluent_number, which is
    # expensive). So we miss that out if possible.
    add_handle_argument = not isinstance(parent_expr, SelectExpression)
    if add_handle_argument:
        # > $tmp_name = handle_argument($tmp_name, "$name", locale, errors)
        try_catch.else_block.add_assignment(
            tmp_name,
            codegen.FunctionCall("handle_argument",
                                 [codegen.VariableReference(tmp_name, local_scope),
                                  codegen.String(name),
                                  codegen.VariableReference(LOCALE_NAME, local_scope),
                                  codegen.VariableReference(ERRORS_NAME, local_scope)],
                                 {},
                                 local_scope))

    local_scope.statements.append(try_catch)
    return codegen.VariableReference(tmp_name, local_scope)


@compile_expr.register(CallExpression)
def compile_expr_call_expression(expr, local_scope, parent_expr, compiler_env):
    function_name = expr.callee.name

    if function_name in compiler_env.functions:
        kwargs, args = partition(expr.args,
                                 lambda i: isinstance(i, NamedArgument))
        args = [compile_expr(arg, local_scope, expr, compiler_env) for arg in args]
        kwargs = {kwarg.name.name: compile_expr(kwarg.val, local_scope, expr, compiler_env) for kwarg in kwargs}
        if args_match(args, kwargs, compiler_env.functions_arg_spec[function_name]):
            function_name_in_module = compiler_env.function_renames[function_name]
            return codegen.FunctionCall(function_name_in_module, args, kwargs, local_scope)
        else:
            error = TypeError("function {0} called with incorrect parameters".format(function_name))
            add_static_msg_error(local_scope, error)
            compiler_env.add_current_message_error(error)
            return make_fluent_none(function_name + "()", local_scope)

    else:
        error = FluentReferenceError("Unknown function: {0}"
                                     .format(function_name))
        add_static_msg_error(local_scope, error)
        compiler_env.add_current_message_error(error)
        return make_fluent_none(function_name + "()", local_scope)


def finalize_expr_as_string(python_expr, scope, compiler_env):
    """
    Wrap an outputted Python expression with code to ensure that it will return
    a string.
    """
    if issubclass(python_expr.type, text_type):
        return python_expr
    elif issubclass(python_expr.type, FluentType):
        # > $python_expr.format(locale)
        return codegen.MethodCall(python_expr,
                                  'format',
                                  [codegen.VariableReference(LOCALE_NAME, scope)],
                                  expr_type=text_type)
    else:
        # > handle_output($python_expr, locale, errors)
        return codegen.FunctionCall('handle_output',
                                    [python_expr,
                                     codegen.VariableReference(LOCALE_NAME, scope),
                                     codegen.VariableReference(ERRORS_NAME, scope)],
                                    {},
                                    scope,
                                    expr_type=text_type)


def is_NUMBER_call_expr(expr):
    """
    Returns True if the object is a FTL ast.CallExpression representing a call to NUMBER
    """
    return (isinstance(expr, CallExpression) and
            expr.callee.name == 'NUMBER')


def add_static_msg_error(local_scope, exception):
    """
    Given a scope and an exception object, inspect the object and add the code
    to the scope needed to create and add that exception to the returned errors
    list.

    """
    return add_msg_error_with_expr(
        local_scope,
        codegen.ObjectCreation(exception.__class__.__name__,
                               [codegen.String(exception.args[0])],
                               {},
                               local_scope))


def add_msg_error_with_expr(local_scope, exception_expr):
    local_scope.statements.append(
        codegen.MethodCall(
            codegen.VariableReference(ERRORS_NAME, local_scope),
            "append",
            [exception_expr]))
