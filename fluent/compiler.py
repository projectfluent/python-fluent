from __future__ import absolute_import, unicode_literals

import contextlib
from collections import OrderedDict

import attr
import babel
import six

from . import codegen, runtime
from .exceptions import FluentCyclicReferenceError, FluentReferenceError
from .syntax.ast import (Attribute, AttributeExpression, BaseNode, CallExpression, Message, MessageReference,
                         NumberLiteral, Pattern, Placeable, SelectExpression, StringLiteral, Term, TermReference,
                         TextElement, VariableReference, VariantExpression, VariantList, VariantName)
from .types import FluentDateType, FluentNumber, FluentType
from .utils import args_match, inspect_function_args, numeric_to_native

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
class CurrentEnvironment(object):
    # The parts of CompilerEnvironment that we want to mutate (and restore)
    # temporarily for some parts of a call chain.
    message_id = attr.ib(default=None)


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
    message_ids_to_ast = attr.ib(factory=dict)
    term_ids_to_ast = attr.ib(factory=dict)
    current = attr.ib(factory=CurrentEnvironment)

    def add_current_message_error(self, error):
        self.errors.append((self.current.message_id, error))

    @contextlib.contextmanager
    def modified(self, **replacements):
        """
        Context manager that modifies the 'current' attribute of the
        environment, restoring the old data at the end.
        """
        # CurrentEnvironment only has immutable args at the moment, so the
        # shallow copy returned by attr.evolve is fine.
        old_current = self.current
        self.current = attr.evolve(old_current, **replacements)
        yield self
        self.current = old_current


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

    message_ids_to_ast = OrderedDict(get_message_function_ast(messages))
    term_ids_to_ast = OrderedDict(get_term_ast(messages))

    compiler_env = CompilerEnvironment(
        locale=locale,
        use_isolating=use_isolating,
        functions=functions,
        debug=debug,
        functions_arg_spec={name: inspect_function_args(func)
                            for name, func in functions.items()},
        message_ids_to_ast=message_ids_to_ast,
        term_ids_to_ast=term_ids_to_ast,
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
        name = module.reserve_name(k,
                                   properties=get_name_properties(k),
                                   is_builtin=k in six.moves.builtins.__dict__
                                   )
        # We should have chosen all our module_globals to avoid name conflicts:
        assert name == k, "Expected {0}=={1}".format(name, k)

    # Reserve names for function arguments, so that we always
    # know the name of these arguments without needing to do
    # lookups etc.
    for arg in list(MESSAGE_FUNCTION_ARGS):
        module.reserve_function_arg_name(arg)

    # -- User defined names
    # functions from context
    for name, func in functions.items():
        # These might clash, because we can't control what the user passed in,
        # so we make a record in 'function_renames'
        assigned_name = module.reserve_name(name, properties=get_name_properties(name))
        compiler_env.function_renames[name] = assigned_name
        module_globals[assigned_name] = func

    # Pass one, find all the names, so that we can populate message_mapping,
    # which is needed for compilation.
    for msg_id, msg in message_ids_to_ast.items():
        function_name = module.reserve_name(
            message_function_name_for_msg_id(msg_id),
            properties={codegen.PROPERTY_RETURN_TYPE: text_type}
        )
        compiler_env.message_mapping[msg_id] = function_name

    # Pass 2, actual compilation
    for msg_id, msg in message_ids_to_ast.items():
        with compiler_env.modified(message_id=msg_id):
            function_name = compiler_env.message_mapping[msg_id]
            function = compile_message(msg, msg_id, function_name, module, compiler_env)
            module.add_function(function_name, function)

    module = codegen.simplify(module)
    return (module, compiler_env.message_mapping, module_globals, compiler_env.errors)


def get_message_function_ast(message_dict):
    for msg_id, msg in message_dict.items():
        if msg.value is None:
            # No body, skip it.
            pass
        elif isinstance(msg, Term):
            pass
        else:
            yield (msg_id, msg)
        for msg_attr in msg.attributes:
            yield (message_id_for_attr(msg_id, msg_attr.id.name), msg_attr)


def get_term_ast(message_dict):
    for term_id, term in message_dict.items():
        if term.value is None:
            # No body, skip it.
            pass
        elif isinstance(term, Message):
            pass
        else:
            yield (term_id, term)
        for term_attr in term.attributes:
            yield (message_id_for_attr(term_id, term_attr.id.name), term_attr)


def message_id_for_attr(parent_msg_id, attr_name):
    return "{0}.{1}".format(parent_msg_id, attr_name)


def message_id_for_attr_expression(attr_expr):
    return message_id_for_attr(attr_expr.ref.id.name, attr_expr.name.name)


def message_function_name_for_msg_id(msg_id):
    # Scope.reserve_name does further sanitising of name, which we don't need to
    # worry about.
    return msg_id.replace('.', '__').replace('-', '_')


def compile_message(msg, msg_id, function_name, module, compiler_env):
    msg_func = codegen.Function(parent_scope=module,
                                name=function_name,
                                args=MESSAGE_FUNCTION_ARGS,
                                debug=compiler_env.debug)

    if contains_reference_cycle(msg, msg_id, compiler_env):
        error = FluentCyclicReferenceError("Cyclic reference in {0}".format(msg_id))
        add_static_msg_error(msg_func, error)
        compiler_env.add_current_message_error(error)
        return_expression = finalize_expr_as_string(make_fluent_none(None, module), msg_func, compiler_env)
    else:
        return_expression = compile_expr(msg, msg_func, None, compiler_env)
    # > return $return_expression
    msg_func.add_return(return_expression)
    return msg_func


def traverse_ast(node, fun, exclude_attributes=None):
    """Postorder-traverse this node and apply `fun` to all child nodes.

    Traverse this node depth-first applying `fun` to subnodes and leaves.
    Children are processed before parents (postorder traversal).

    exclude_attributes is a list of (node type, attribute name) tuples
    that should not be recursed into.
    """

    def visit(value):
        """Call `fun` on `value` and its descendants."""
        if isinstance(value, BaseNode):
            return traverse_ast(value, fun, exclude_attributes=exclude_attributes)
        if isinstance(value, list):
            return fun(list(map(visit, value)))
        else:
            return fun(value)

    # Use all attributes found on the node
    parts = vars(node).items()
    for name, value in parts:
        if exclude_attributes is not None and (type(node), name) in exclude_attributes:
            continue
        visit(value)

    return fun(node)


def contains_reference_cycle(msg, msg_id, compiler_env):
    message_ids_to_ast = compiler_env.message_ids_to_ast
    term_ids_to_ast = compiler_env.term_ids_to_ast

    # We exclude recursing into certain attributes, because we already cover
    # these recursions explicitly by jumping to a subnode for the case of
    # references.
    exclude_attributes = [
        # Message and Term attributes have already been loaded into the message_ids_to_ast dict,
        # and we get to their contents via AttributeExpression
        (Message, 'attributes'),
        (Term, 'attributes'),

        # We don't recurse into AttributeExpression.ref, which is a
        # MessageReference, because we have handled the contents of this ref via
        # the parent AttributeExpression, and we don't want it to be handled as
        # a standalone MessageReference which would mean something different.
        (AttributeExpression, 'ref'),

        # for speed
        (Message, 'comment'),
        (Term, 'comment'),
    ]
    visited_nodes = set([])
    checks = []

    def checker(node):
        if isinstance(node, BaseNode):
            node_id = id(node)
            if node_id in visited_nodes:
                checks.append(True)
                return
            visited_nodes.add(node_id)
        else:
            return

        # The logic below duplicates the logic that is used for 'jumping' to
        # different nodes (messages via a runtime function call, terms via
        # inlining), including the fallback strategies that are used.
        sub_node = None
        if isinstance(node, MessageReference):
            ref = node.id.name
            if ref in message_ids_to_ast:
                sub_node = message_ids_to_ast[ref]
        elif isinstance(node, TermReference):
            ref = node.id.name
            if ref in term_ids_to_ast:
                sub_node = term_ids_to_ast[ref]
        elif isinstance(node, AttributeExpression):
            ref = message_id_for_attr_expression(node)
            if ref in message_ids_to_ast:
                sub_node = message_ids_to_ast[ref]
            elif ref in term_ids_to_ast:
                sub_node = term_ids_to_ast[ref]
            else:
                # Compiler falls back to parent ref in this situation
                parent_ref = node.ref.id.name
                if parent_ref in message_ids_to_ast:
                    sub_node = message_ids_to_ast[parent_ref]
                elif parent_ref in term_ids_to_ast:
                    sub_node = term_ids_to_ast[parent_ref]

        if sub_node is not None:
            traverse_ast(sub_node, checker, exclude_attributes=exclude_attributes)
            if any(checks):
                return

        return

    traverse_ast(msg, checker, exclude_attributes=exclude_attributes)
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


@compile_expr.register(Message)
def compile_expr_message(message, local_scope, parent_expr, compiler_env):
    return compile_expr(message.value, local_scope, message, compiler_env)


@compile_expr.register(Term)
def compile_expr_term(term, local_scope, parent_expr, compiler_env):
    return compile_expr(term.value, local_scope, term, compiler_env)


@compile_expr.register(Attribute)
def compile_expr_attribute(attribute, local_scope, parent_expr, compiler_env):
    return compile_expr(attribute.value, local_scope, attribute, compiler_env)


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


@compile_expr.register(StringLiteral)
def compile_expr_string_expression(expr, local_scope, parent_expr, compiler_env):
    return codegen.String(expr.value)


@compile_expr.register(NumberLiteral)
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


@compile_expr.register(TermReference)
def compile_expr_term_reference(reference, local_scope, parent_expr, compiler_env):
    name = reference.id.name
    if name in compiler_env.term_ids_to_ast:
        term = compiler_env.term_ids_to_ast[name]
        return compile_expr(term.value, local_scope, reference, compiler_env)
    else:
        error = FluentReferenceError("Unknown term: {0}".format(name))
        add_static_msg_error(local_scope, error)
        compiler_env.add_current_message_error(error)
        return make_fluent_none(name, local_scope)


def do_message_call(name, local_scope, parent_expr, compiler_env):
    if name in compiler_env.message_mapping:
        msg_func_name = compiler_env.message_mapping[name]
        return codegen.FunctionCall(msg_func_name,
                                    [codegen.VariableReference(a, local_scope) for a in MESSAGE_FUNCTION_ARGS],
                                    {},
                                    local_scope)

    else:
        return unknown_reference(name, local_scope, compiler_env)


def unknown_reference(name, local_scope, compiler_env):
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
    parent_id = attribute.ref.id.name
    msg_id = message_id_for_attr_expression(attribute)
    # Message attribute
    if msg_id in compiler_env.message_mapping:
        return do_message_call(msg_id, local_scope, attribute, compiler_env)
    # Term attribute
    elif msg_id in compiler_env.term_ids_to_ast:
        term = compiler_env.term_ids_to_ast[msg_id]
        return compile_expr(term, local_scope, attribute, compiler_env)
    # Message fallback to parent
    elif parent_id in compiler_env.message_mapping:
        error = FluentReferenceError("Unknown attribute: {0}"
                                     .format(msg_id))
        add_static_msg_error(local_scope, error)
        compiler_env.add_current_message_error(error)
        return do_message_call(parent_id, local_scope, attribute, compiler_env)
    # Term fallback to parent
    elif parent_id in compiler_env.term_ids_to_ast:
        term = compiler_env.term_ids_to_ast[parent_id]
        error = FluentReferenceError("Unknown attribute: {0}"
                                     .format(msg_id))
        add_static_msg_error(local_scope, error)
        compiler_env.add_current_message_error(error)
        return compile_expr(term, local_scope, attribute, compiler_env)
    # Final fallback
    else:
        return unknown_reference(msg_id, local_scope, compiler_env)


@compile_expr.register(VariantList)
def compile_expr_variant_list(variant_list, local_scope, parent_expr, compiler_env,
                              selected_key=None, term_id=None):
    default = None
    found = None
    for variant in variant_list.variants:
        if variant.default:
            default = variant
        if selected_key is not None and variant.key.name == selected_key.name:
            found = variant

    if found is None:
        found = default
        if selected_key is not None:
            error = FluentReferenceError("Unknown variant: {0}[{1}]"
                                         .format(term_id,
                                                 selected_key.name))
            add_static_msg_error(local_scope, error)
            compiler_env.add_current_message_error(error)
    return compile_expr(found.value, local_scope, variant_list, compiler_env)


def is_cldr_plural_form_key(key_expr):
    return (isinstance(key_expr, VariantName) and
            key_expr.name in CLDR_PLURAL_FORMS)


@compile_expr.register(SelectExpression)
def compile_expr_select_expression(select_expr, local_scope, parent_expr, compiler_env):
    # This is very similar to compile_expr_variant_list, but it is different
    # enough that implementing them together makes the code rather hard to understand
    if_statement = codegen.If(local_scope)
    key_tmp_name = local_scope.reserve_name('_key')
    key_value = compile_expr(select_expr.selector, local_scope, select_expr, compiler_env)
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
    term_id = variant_expr.ref.id.name
    if term_id in compiler_env.term_ids_to_ast:
        term_val = compiler_env.term_ids_to_ast[term_id].value
        if isinstance(term_val, VariantList):
            return compile_expr_variant_list(term_val, local_scope, variant_expr, compiler_env,
                                             selected_key=variant_expr.key,
                                             term_id=term_id)
        else:
            error = FluentReferenceError('Unknown variant: {0}[{1}]'.format(
                term_id, variant_expr.key.name))
            add_static_msg_error(local_scope, error)
            compiler_env.add_current_message_error(error)
            return compile_expr(term_val, local_scope, variant_expr, compiler_env)
    else:
        error = FluentReferenceError("Unknown term: {0}".format(term_id))
        add_static_msg_error(local_scope, error)
        compiler_env.add_current_message_error(error)
        return make_fluent_none(term_id, local_scope)


@compile_expr.register(VariableReference)
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
        args = [compile_expr(arg, local_scope, expr, compiler_env) for arg in expr.positional]
        kwargs = {kwarg.name.name: compile_expr(kwarg.value, local_scope, expr, compiler_env) for kwarg in expr.named}
        match, error = args_match(function_name, args, kwargs, compiler_env.functions_arg_spec[function_name])
        if match:
            function_name_in_module = compiler_env.function_renames[function_name]
            return codegen.FunctionCall(function_name_in_module, args, kwargs, local_scope)
        else:
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
