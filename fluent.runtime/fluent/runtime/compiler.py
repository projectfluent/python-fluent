from __future__ import absolute_import, unicode_literals

import contextlib
from collections import OrderedDict

import attr
import babel
import six

from fluent.syntax.ast import (Attribute, AttributeExpression, BaseNode, CallExpression, Identifier, Message,
                               MessageReference, NumberLiteral, Pattern, Placeable, SelectExpression, StringLiteral,
                               Term, TermReference, TextElement, VariableReference, VariantExpression, VariantList)

from . import codegen, runtime
from .errors import FluentCyclicReferenceError, FluentFormatError, FluentReferenceError
from .types import FluentDateType, FluentNone, FluentNumber, FluentType
from .utils import (ATTRIBUTE_SEPARATOR, TERM_SIGIL, args_match, ast_to_id,
                    attribute_ast_to_id, inspect_function_args, reference_to_id,
                    unknown_reference_error_obj)
from .escapers import null_escaper, escaper_for_message, RegisteredEscaper, EscaperJoin, escapers_compatible, identity

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

# Function argument and global names::
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
PROPERTY_EXTERNAL_ARG = 'PROPERTY_EXTERNAL_ARG'


@attr.s
class CurrentEnvironment(object):
    # The parts of CompilerEnvironment that we want to mutate (and restore)
    # temporarily for some parts of a call chain.
    message_id = attr.ib(default=None)
    term_args = attr.ib(default=None)
    in_select_expression = attr.ib(default=False)
    escaper = attr.ib(default=null_escaper)


@attr.s
class CompilerEnvironment(object):
    locale = attr.ib()
    plural_form_function = attr.ib()
    use_isolating = attr.ib()
    message_mapping = attr.ib(factory=dict)
    errors = attr.ib(factory=list)
    escapers = attr.ib(default=None)
    functions = attr.ib(factory=dict)
    function_renames = attr.ib(factory=dict)
    functions_arg_spec = attr.ib(factory=dict)
    message_ids_to_ast = attr.ib(factory=dict)
    term_ids_to_ast = attr.ib(factory=dict)
    current = attr.ib(factory=CurrentEnvironment)

    def add_current_message_error(self, error):
        self.errors.append((self.current.message_id, error))

    def escaper_for_message(self, message_id=None):
        return escaper_for_message(self.escapers, message_id=message_id)

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

    def modified_for_term_reference(self, term_args=None):
        return self.modified(term_args=term_args if term_args is not None else {})


def compile_messages(messages, locale, use_isolating=True, functions=None, escapers=None):
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
        escapers=escapers)

    code_obj = compile(module.as_ast(), '<string>', 'exec')
    exec(code_obj, module_globals)
    retval = {}
    for key, val in message_mapping.items():
        if key.startswith(TERM_SIGIL):
            # term, shouldn't be in publicly available messages
            continue
        retval[six.text_type(key)] = module_globals[val]

    return (retval, errors)


def messages_to_module(messages, locale, use_isolating=True, functions=None, escapers=None):
    """
    Compile a set of {id: Message/Term objects} to a Python module, returning a tuple:
    (codegen.Module object, dictionary mapping message IDs to Python functions,
     module globals dictionary, errors list)
    """
    if functions is None:
        functions = {}

    message_ids_to_ast = OrderedDict(get_message_function_ast(messages))
    term_ids_to_ast = OrderedDict(get_term_ast(messages))

    # Plural form function
    plural_form_for_number_main = babel.plural.to_python(locale.plural_form)

    def plural_form_for_number(number):
        try:
            return plural_form_for_number_main(number)
        except TypeError:
            # This function can legitimately be passed strings if we incorrectly
            # guessed it was a CLDR category. So we ignore silently
            return None

    function_arg_errors = []
    compiler_env = CompilerEnvironment(
        locale=locale,
        plural_form_function=plural_form_for_number,
        use_isolating=use_isolating,
        functions=functions,
        functions_arg_spec={name: inspect_function_args(func, name, function_arg_errors)
                            for name, func in functions.items()},
        message_ids_to_ast=message_ids_to_ast,
        term_ids_to_ast=term_ids_to_ast,
    )
    for err in function_arg_errors:
        compiler_env.add_current_message_error(err)

    if escapers:
        if len(set(e.name for e in escapers)) < len(escapers):
            raise ValueError("Every escaper must have a unique 'name' attribute'")
        compiler_env.escapers = [RegisteredEscaper(escaper, compiler_env)
                                 for escaper in escapers]

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

    module_globals[PLURAL_FORM_FOR_NUMBER_NAME] = plural_form_for_number
    known_return_types[PLURAL_FORM_FOR_NUMBER_NAME] = text_type

    def get_name_properties(name):
        properties = {}
        if name in known_return_types:
            properties[codegen.PROPERTY_RETURN_TYPE] = known_return_types[name]
        return properties

    module = codegen.Module()
    for k in module_globals:
        name = module.scope.reserve_name(
            k,
            properties=get_name_properties(k),
            is_builtin=k in six.moves.builtins.__dict__
        )
        # We should have chosen all our module_globals to avoid name conflicts:
        assert name == k, "Expected {0}=={1}".format(name, k)

    # Reserve names for escapers
    if compiler_env.escapers is not None:
        for escaper in compiler_env.escapers:
            for name, func, properties in escaper.get_reserved_names_with_properties():
                assigned_name = module.scope.reserve_name(name, properties=properties)
                # We've chosen the names to not clash with anything that
                # we've already set up.
                assert assigned_name == name
                assert assigned_name not in module_globals
                module_globals[assigned_name] = func

    # Reserve names for function arguments, so that we always
    # know the name of these arguments without needing to do
    # lookups etc.
    for arg in MESSAGE_FUNCTION_ARGS:
        module.scope.reserve_function_arg_name(arg)

    # -- User defined names
    # functions from context
    for name, func in functions.items():
        # These might clash, because we can't control what the user passed in,
        # so we make a record in 'function_renames'
        assigned_name = module.scope.reserve_name(name, properties=get_name_properties(name))
        compiler_env.function_renames[name] = assigned_name
        module_globals[assigned_name] = func

    # Pass one, find all the names, so that we can populate message_mapping,
    # which is needed for compilation.
    for msg_id, msg in message_ids_to_ast.items():
        escaper = compiler_env.escaper_for_message(message_id=msg_id)
        function_name = module.scope.reserve_name(
            message_function_name_for_msg_id(msg_id),
            properties={codegen.PROPERTY_RETURN_TYPE: escaper.output_type}
        )
        compiler_env.message_mapping[msg_id] = function_name

    # Pass 2, actual compilation
    for msg_id, msg in message_ids_to_ast.items():
        with compiler_env.modified(message_id=msg_id,
                                   escaper=compiler_env.escaper_for_message(message_id=msg_id)):
            function_name = compiler_env.message_mapping[msg_id]
            function = compile_message(msg, msg_id, function_name, module, compiler_env)
            module.add_function(function_name, function)

    module = codegen.simplify(module, Simplifier(compiler_env))
    return (module, compiler_env.message_mapping, module_globals, compiler_env.errors)


def get_message_function_ast(message_dict):
    for msg_id, msg in message_dict.items():
        if isinstance(msg, Term):
            continue
        if msg.value is not None:  # has a body
            yield (msg_id, msg)
        for attribute in msg.attributes:
            yield (attribute_ast_to_id(attribute, msg), attribute)


def get_term_ast(message_dict):
    for term_id, term in message_dict.items():
        if isinstance(term, Message):
            pass
        if term.value is not None:  # has a body
            yield (term_id, term)

        for attribute in term.attributes:
            yield (attribute_ast_to_id(attribute, term), attribute)


def message_function_name_for_msg_id(msg_id):
    # Scope.reserve_name does further sanitising of name, which we don't need to
    # worry about.
    return msg_id.replace(ATTRIBUTE_SEPARATOR, '__').replace('-', '_')


def compile_message(msg, msg_id, function_name, module, compiler_env):
    msg_func = codegen.Function(parent_scope=module.scope,
                                name=function_name,
                                args=MESSAGE_FUNCTION_ARGS)
    function_block = msg_func.body
    if contains_reference_cycle(msg, compiler_env):
        error = FluentCyclicReferenceError("Cyclic reference in {0}".format(msg_id))
        add_static_msg_error(function_block, error)
        compiler_env.add_current_message_error(error)
        return_expression = finalize_expr_as_output_type(
            make_fluent_none(None, module.scope), function_block, compiler_env)
    else:
        return_expression = compile_expr(msg, function_block, compiler_env)
    # > return $return_expression
    msg_func.add_return(return_expression)
    return msg_func


def traverse_ast(node, fun, exclude_attributes=None):
    """
    Postorder-traverse this node and apply `fun` to all child nodes.

    exclude_attributes is a list of (node type, attribute name) tuples
    that should not be recursed into.
    """

    def visit(value):
        """Call `fun` on `value` and its descendants."""
        if isinstance(value, BaseNode):
            return traverse_ast(value, fun, exclude_attributes=exclude_attributes)
        if isinstance(value, list):
            return fun(list(map(visit, value)))
        return fun(value)

    # Use all attributes found on the node
    parts = vars(node).items()
    for name, value in parts:
        if exclude_attributes is not None and (type(node), name) in exclude_attributes:
            continue
        visit(value)

    return fun(node)


def contains_reference_cycle(msg, compiler_env):
    """
    Returns True if the message 'msg' contains a cyclic reference,
    in the context of the other messages provided in compiler_env
    """
    # We traverse the AST starting from message, jumping to other messages and
    # terms as necessary, and seeing if a path through the AST loops back to
    # previously visited nodes at any point.

    # This algorithm has some bugs compared to the runtime method in resolver.py
    # For example, a pair of conditionally mutually recursive messages:

    # foo = Foo { $arg ->
    #      [left]    { bar }
    #     *[right]   End
    #  }

    # bar = Bar { $arg ->
    #     *[left]    End
    #      [right]   { foo }
    #  }

    # These messages are rejected as containing cycles by this checker, when in
    # fact they cannot go into an infinite loop, and the resolver correctly
    # executes them.

    # It is pretty difficult to come up with a compelling use case
    # for this kind of thing though... so we are not too worried
    # about fixing this bug, since we are erring on the conservative side.

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

    # We need to keep track of visited nodes. If we use just a single set for
    # each top level message, then things like this would be rejected:
    #
    #     message = { -term } { -term }
    #
    # because we would visit the term twice.
    #
    # So we have a stack of sets:
    visited_node_stack = [set([])]
    # The top of this stack represents the set of nodes in the current path of
    # visited nodes. We push a copy of the top set onto the stack when we
    # traverse into a sub-node, and pop it off when we come back.

    checks = []

    def checker(node):
        if isinstance(node, BaseNode):
            node_id = id(node)
            if node_id in visited_node_stack[-1]:
                checks.append(True)
                return
            visited_node_stack[-1].add(node_id)
        else:
            return

        # The logic below duplicates the logic that is used for 'jumping' to
        # different nodes (messages via a runtime function call, terms via
        # inlining), including the fallback strategies that are used.
        sub_node = None
        if isinstance(node, (MessageReference, TermReference, AttributeExpression)):
            ref_id = reference_to_id(node)
            if ref_id in message_ids_to_ast:
                sub_node = message_ids_to_ast[ref_id]
            elif ref_id in term_ids_to_ast:
                sub_node = term_ids_to_ast[ref_id]
            elif isinstance(node, AttributeExpression):
                # No match for attribute, but compiler falls back to parent ref
                # in this situation, so we have to as well.
                parent_ref_id = reference_to_id(node.ref)
                if parent_ref_id in message_ids_to_ast:
                    sub_node = message_ids_to_ast[parent_ref_id]
                elif parent_ref_id in term_ids_to_ast:
                    sub_node = term_ids_to_ast[parent_ref_id]

        if sub_node is not None:
            visited_node_stack.append(visited_node_stack[-1].copy())
            traverse_ast(sub_node, checker, exclude_attributes=exclude_attributes)
            if any(checks):
                return
            visited_node_stack.pop()

        return

    traverse_ast(msg, checker, exclude_attributes=exclude_attributes)
    return any(checks)


# Begin 'compile_expr' implementation

@singledispatch
def compile_expr(element, block, compiler_env):
    """
    Compiles a Fluent expression into a Python one, return
    an object of type codegen.Expression.

    This may also add statements into block, which is assumed
    to be a function that returns a message, or a branch of that
    function.
    """
    raise NotImplementedError("Cannot handle object of type {0}"
                              .format(type(element).__name__))


@compile_expr.register(Message)
def compile_expr_message(message, block, compiler_env):
    return compile_expr(message.value, block, compiler_env)


@compile_expr.register(Term)
def compile_expr_term(term, block, compiler_env):
    return compile_expr(term.value, block, compiler_env)


@compile_expr.register(Attribute)
def compile_expr_attribute(attribute, block, compiler_env):
    return compile_expr(attribute.value, block, compiler_env)


@compile_expr.register(Pattern)
def compile_expr_pattern(pattern, block, compiler_env):
    parts = []
    subelements = pattern.elements

    escaper = compiler_env.current.escaper
    use_isolating = ((escaper.use_isolating
                      if escaper.use_isolating is not None
                      else compiler_env.use_isolating) and
                     len(subelements) > 1)

    for element in pattern.elements:
        wrap_this_with_isolating = use_isolating and not isinstance(element, TextElement)
        if wrap_this_with_isolating:
            parts.append(wrap_with_escaper(codegen.String(FSI), block, compiler_env))
        parts.append(compile_expr(element, block, compiler_env))
        if wrap_this_with_isolating:
            parts.append(wrap_with_escaper(codegen.String(PDI), block, compiler_env))

    # > ''.join($[p for p in parts])
    return EscaperJoin([finalize_expr_as_output_type(p, block, compiler_env) for p in parts],
                       escaper, block.scope)


@compile_expr.register(TextElement)
def compile_expr_text(text, block, compiler_env):
    return wrap_with_mark_escaped(codegen.String(text.value), block, compiler_env)


@compile_expr.register(StringLiteral)
def compile_expr_string_expression(expr, block, compiler_env):
    return codegen.String(expr.value)


@compile_expr.register(NumberLiteral)
def compile_expr_number_expression(expr, block, compiler_env):
    number_expr = codegen.Number(numeric_to_native(expr.value))
    # > NUMBER($number_expr)
    return codegen.FunctionCall(BUILTIN_NUMBER,
                                [number_expr],
                                {},
                                block.scope)


@compile_expr.register(Placeable)
def compile_expr_placeable(placeable, block, compiler_env):
    return compile_expr(placeable.expression, block, compiler_env)


@compile_expr.register(MessageReference)
def compile_expr_message_reference(reference, block, compiler_env):
    return handle_message_reference(reference, block, compiler_env)


def compile_term(term, block, compiler_env, new_escaper, term_args=None):
    current_escaper = compiler_env.current.escaper
    if not escapers_compatible(current_escaper, new_escaper):
        term_id = ast_to_id(term)
        error = TypeError("Escaper {0} for term {1} cannot be used from calling context with {2} escaper"
                          .format(new_escaper.name, term_id, current_escaper.name))
        add_static_msg_error(block, error)
        compiler_env.add_current_message_error(error)
        return make_fluent_none(term_id, block.scope)
    else:
        with compiler_env.modified(escaper=new_escaper):
            with compiler_env.modified_for_term_reference(term_args=term_args):
                return compile_expr(term.value, block, compiler_env)


@compile_expr.register(TermReference)
def compile_expr_term_reference(reference, block, compiler_env):
    term, new_escaper, err_obj = lookup_term_reference(reference, block, compiler_env)
    if term is None:
        return err_obj
    return compile_term(term, block, compiler_env, new_escaper)


@compile_expr.register(AttributeExpression)
def compile_expr_attribute_expression(attr_expr, block, compiler_env):
    if isinstance(attr_expr.ref, TermReference):
        term, new_escaper, err_obj = lookup_term_reference(attr_expr, block, compiler_env)
        if term is None:
            return err_obj
        return compile_term(term, block, compiler_env, new_escaper)

    # Message
    return handle_message_reference(attr_expr, block, compiler_env)


@compile_expr.register(VariantList)
def compile_expr_variant_list(variant_list, block, compiler_env,
                              selected_key=None, term=None):
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
                                         .format(ast_to_id(term),
                                                 selected_key.name))
            add_static_msg_error(block, error)
            compiler_env.add_current_message_error(error)
    return compile_expr(found.value, block, compiler_env)


@compile_expr.register(SelectExpression)
def compile_expr_select_expression(select_expr, block, compiler_env):
    with compiler_env.modified(in_select_expression=True):
        key_value = compile_expr(select_expr.selector, block, compiler_env)
    static_retval = resolve_select_expression_statically(select_expr, key_value, block, compiler_env)
    if static_retval is not None:
        return static_retval

    if_statement = codegen.If(block.scope)
    key_tmp_name = reserve_and_assign_name(block, '_key', key_value)

    return_tmp_name = block.scope.reserve_name('_ret')

    need_plural_form = any(is_cldr_plural_form_key(variant.key)
                           for variant in select_expr.variants)
    if need_plural_form:
        plural_form_value = codegen.FunctionCall(PLURAL_FORM_FOR_NUMBER_NAME,
                                                 [block.scope.variable(key_tmp_name)],
                                                 {},
                                                 block.scope)
        # > $plural_form_tmp_name = plural_form_for_number($key_tmp_name)
        plural_form_tmp_name = reserve_and_assign_name(block, '_plural_form', plural_form_value)

    assigned_types = []
    first = True
    for variant in select_expr.variants:
        if variant.default:
            # This is the default, so gets chosen if nothing else matches, or
            # there was no requested variant. Therefore we use the final 'else'
            # block with no condition.
            cur_block = if_statement.else_block
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
            condition1 = codegen.Equals(block.scope.variable(key_tmp_name),
                                        compile_expr(variant.key, block, compiler_env))

            if is_cldr_plural_form_key(variant.key):
                # > $plural_form_tmp_name == $variant.key
                condition2 = codegen.Equals(block.scope.variable(plural_form_tmp_name),
                                            compile_expr(variant.key, block, compiler_env))
                condition = codegen.Or(condition1, condition2)
            else:
                condition = condition1
            cur_block = if_statement.add_if(condition)
        assigned_value = compile_expr(variant.value, cur_block, compiler_env)
        cur_block.add_assignment(return_tmp_name, assigned_value, allow_multiple=not first)
        first = False
        assigned_types.append(assigned_value.type)

    if assigned_types:
        first_type = assigned_types[0]
        if all(t == first_type for t in assigned_types):
            block.scope.set_name_properties(return_tmp_name, {codegen.PROPERTY_TYPE: first_type})

    block.statements.append(if_statement)
    return block.scope.variable(return_tmp_name)


@compile_expr.register(Identifier)
def compile_expr_variant_name(name, block, compiler_env):
    # TODO - handle numeric literals here?
    return codegen.String(name.name)


@compile_expr.register(VariantExpression)
def compile_expr_variant_expression(variant_expr, block, compiler_env):
    term, new_escaper, err_obj = lookup_term_reference(variant_expr.ref, block, compiler_env)
    if term is None:
        return err_obj

    term_val = term.value
    if isinstance(term_val, VariantList):
        current_escaper = compiler_env.current.escaper
        if not escapers_compatible(current_escaper, new_escaper):
            term_id = ast_to_id(term)
            error = TypeError("Escaper {0} for term {1} cannot be used from calling context with {2} escaper"
                              .format(new_escaper.name, term_id, current_escaper.name))
            add_static_msg_error(block, error)
            compiler_env.add_current_message_error(error)
            return make_fluent_none(term_id, block.scope)

        with compiler_env.modified(escaper=new_escaper):
            value = compile_expr_variant_list(term_val, block, compiler_env,
                                              selected_key=variant_expr.key,
                                              term=term)
        return wrap_with_escaper(value, block, compiler_env)

    error = FluentReferenceError('Unknown variant: {0}[{1}]'.format(
            reference_to_id(variant_expr.ref), variant_expr.key.name))
    add_static_msg_error(block, error)
    compiler_env.add_current_message_error(error)
    return compile_expr(term_val, block, compiler_env)


@compile_expr.register(VariableReference)
def compile_expr_variable_reference(argument, block, compiler_env):
    name = argument.id.name
    if compiler_env.current.term_args is not None:
        # We are in a term, all args are passed explicitly, not inherited from
        # external args.
        if name in compiler_env.current.term_args:
            return compiler_env.current.term_args[name]
        return make_fluent_none(name, block.scope)

    # Otherwise we are in a message, lookup at runtime.

    # We might have already looked it up:
    existing = block.scope.find_names_by_property(PROPERTY_EXTERNAL_ARG, name)
    if existing:
        arg_tmp_name = existing[0]
    else:
        arg_tmp_name = block.scope.reserve_name('_arg', properties={PROPERTY_EXTERNAL_ARG: name})

    # Arguments we get out of the args dictionary should be wrapped
    # into 'native' Fluent types using `handle_argument`.
    # Except, in a select expression, we only care about matching against a selector, so
    # don't need to do this wrapping
    wrap_with_handle_argument = not compiler_env.current.in_select_expression
    if wrap_with_handle_argument:
        arg_handled_tmp_name = block.scope.reserve_name('_arg_h')

        # > $tmp_name = handle_argument_with_escaper($tmp_name, "$name", output_type, locale, errors)
        # or
        # > $tmp_name = handle_argument($tmp_name, "$name", locale, errors)
        escaper = compiler_env.current.escaper
        if escaper is null_escaper:
            handle_argument_func_call = codegen.FunctionCall(
                "handle_argument",
                [block.scope.variable(arg_tmp_name),
                 codegen.String(name),
                 block.scope.variable(LOCALE_NAME),
                 block.scope.variable(ERRORS_NAME)],
                {},
                block.scope)
        else:
            handle_argument_func_call = codegen.FunctionCall(
                "handle_argument_with_escaper",
                [block.scope.variable(arg_tmp_name),
                 codegen.String(name),
                 block.scope.variable(escaper.output_type_name()),
                 block.scope.variable(LOCALE_NAME),
                 block.scope.variable(ERRORS_NAME)],
                {},
                block.scope)

    if block.scope.has_assignment(arg_tmp_name):  # already assigned to this, can re-use
        if not wrap_with_handle_argument:
            return block.variable(arg_tmp_name)

        block.add_assignment(
            arg_handled_tmp_name,
            handle_argument_func_call)
        return block.scope.variable(arg_handled_tmp_name)

    # Add try/except/else to lookup variable.
    try_except = codegen.Try([block.scope.variable("LookupError"),
                              block.scope.variable("TypeError")  # for when args=None
                              ],
                             block.scope)
    block.statements.append(try_except)

    # Try block
    # > $arg_tmp_name = message_args[$name]
    try_except.try_block.add_assignment(
        arg_tmp_name,
        codegen.DictLookup(block.scope.variable(MESSAGE_ARGS_NAME),
                           codegen.String(name)))
    # Except block
    add_static_msg_error(try_except.except_block,
                         FluentReferenceError("Unknown external: {0}".format(name)))
    # > $arg_tmp_name = FluentNone("$name")
    try_except.except_block.add_assignment(
        arg_tmp_name,
        make_fluent_none(name, block.scope),
        allow_multiple=True)

    if not wrap_with_handle_argument:
        return block.scope.variable(arg_tmp_name)

    # We can use except/else blocks to do wrapping.
    # Except block:
    # We don't want to add 'handle_argument' round FluentNone instances,
    # it does the wrong thing.
    # > $arg_handled_tmp_name = $arg_tmp_name
    try_except.except_block.add_assignment(
        arg_handled_tmp_name,
        block.scope.variable(arg_tmp_name))

    # else block:
    # > $handled_tmp_name = handle_argument($arg_tmp_name, "$name", locale, errors)
    try_except.else_block.add_assignment(
        arg_handled_tmp_name,
        handle_argument_func_call,
        allow_multiple=True)

    return block.scope.variable(arg_handled_tmp_name)


@compile_expr.register(CallExpression)
def compile_expr_call_expression(expr, block, compiler_env):
    args = [compile_expr(arg, block, compiler_env) for arg in expr.positional]
    kwargs = {kwarg.name.name: compile_expr(kwarg.value, block, compiler_env) for kwarg in expr.named}

    if isinstance(expr.callee, (TermReference, AttributeExpression)):
        if args:
            args_err = FluentFormatError("Ignored positional arguments passed to term '{0}'"
                                         .format(reference_to_id(expr.callee)))
            add_static_msg_error(block, args_err)
            compiler_env.add_current_message_error(args_err)

        term, new_escaper, err = lookup_term_reference(expr.callee, block, compiler_env)
        if term is None:
            return err
        return compile_term(term, block, compiler_env, new_escaper, term_args=kwargs)

    # builtin or custom function
    function_name = expr.callee.id.name

    if function_name in compiler_env.functions:
        match, sanitized_args, sanitized_kwargs, errors = args_match(function_name, args, kwargs,
                                                                     compiler_env.functions_arg_spec[function_name])
        for error in errors:
            add_static_msg_error(block, error)
            compiler_env.add_current_message_error(error)

        if match:
            function_name_in_module = compiler_env.function_renames[function_name]
            return codegen.FunctionCall(function_name_in_module, sanitized_args, sanitized_kwargs, block.scope)
        return make_fluent_none(function_name + "()", block.scope)

    error = FluentReferenceError("Unknown function: {0}"
                                 .format(function_name))
    add_static_msg_error(block, error)
    compiler_env.add_current_message_error(error)
    return make_fluent_none(function_name + "()", block.scope)


# End compile_expr implementations

# Compiler utilities and common code:

def add_msg_error_with_expr(block, exception_expr):
    block.statements.append(
        codegen.MethodCall(
            block.scope.variable(ERRORS_NAME),
            "append",
            [exception_expr]))


def add_static_msg_error(block, exception):
    """
    Given a block and an exception object, inspect the object and add the code
    to the scope needed to create and add that exception to the returned errors
    list.

    """
    return add_msg_error_with_expr(
        block,
        codegen.ObjectCreation(exception.__class__.__name__,
                               [codegen.String(exception.args[0])],
                               {},
                               block.scope))


def do_message_call(msg_id, block, compiler_env):
    current_escaper = compiler_env.current.escaper
    new_escaper = compiler_env.escaper_for_message(msg_id)
    if not escapers_compatible(current_escaper, new_escaper):
        error = TypeError("Escaper {0} for message {1} cannot be used from calling context with {2} escaper"
                          .format(new_escaper.name, msg_id, current_escaper.name))
        add_static_msg_error(block, error)
        compiler_env.add_current_message_error(error)
        return make_fluent_none(msg_id, block.scope)

    msg_func_name = compiler_env.message_mapping[msg_id]
    if compiler_env.current.term_args is not None:
        # Message call from inside a term.
        # We pass term args to message function, not external args.
        term_arg_dict = codegen.Dict([(codegen.String(k), v)
                                      for k, v in sorted(compiler_env.current.term_args.items())])
        call_args = [term_arg_dict, block.scope.variable(ERRORS_NAME)]
    else:
        call_args = [block.scope.variable(a) for a in MESSAGE_FUNCTION_ARGS]

    func_call = codegen.FunctionCall(msg_func_name,
                                     call_args,
                                     {},
                                     block.scope)
    return wrap_with_escaper(func_call, block, compiler_env)


def finalize_expr_as_output_type(codegen_ast, block, compiler_env):
    """
    Wrap an outputted Python expression with code to ensure that it will return
    a string (or the correct output type for the escaper)
    """
    escaper = compiler_env.current.escaper
    if codegen_ast.type is escaper.output_type:
        return codegen_ast
    if issubclass(codegen_ast.type, six.text_type):
        return wrap_with_escaper(codegen_ast, block, compiler_env)
    if issubclass(codegen_ast.type, FluentType):
        # > $escaper.escape($codegen_ast.format(locale))
        return wrap_with_escaper(
            codegen.MethodCall(codegen_ast,
                               'format',
                               [block.scope.variable(LOCALE_NAME)],
                               expr_type=text_type),
            block, compiler_env)
    if escaper is null_escaper:
        # > handle_output($python_expr, locale, errors)
        return codegen.FunctionCall('handle_output',
                                    [codegen_ast,
                                     block.scope.variable(LOCALE_NAME),
                                     block.scope.variable(ERRORS_NAME)],
                                    {},
                                    block.scope,
                                    expr_type=text_type)

    # > handle_output_with_escaper($codegen_ast, $escaper.output_type, $escaper.escape, locale, errors)
    return codegen.FunctionCall('handle_output_with_escaper',
                                [codegen_ast,
                                 block.scope.variable(escaper.output_type_name()),
                                 block.scope.variable(escaper.escape_name()),
                                 block.scope.variable(LOCALE_NAME),
                                 block.scope.variable(ERRORS_NAME)],
                                {},
                                block.scope,
                                expr_type=escaper.output_type)


def is_cldr_plural_form_key(key_expr):
    return (isinstance(key_expr, Identifier) and
            key_expr.name in CLDR_PLURAL_FORMS)


def is_NUMBER_call_expr(expr):
    """
    Returns True if the object is a FTL ast.CallExpression representing a call to NUMBER
    """
    return (isinstance(expr, CallExpression) and
            expr.callee.id.name == 'NUMBER')


def lookup_term_reference(ref, block, compiler_env):
    # This could be turned into 'handle_term_reference', (similar to
    # 'handle_message_reference' below) once VariantList and VariantExpression
    # go away.
    term_id = reference_to_id(ref)
    if term_id in compiler_env.term_ids_to_ast:
        return compiler_env.term_ids_to_ast[term_id], compiler_env.escaper_for_message(term_id), None
    if isinstance(ref, AttributeExpression):
        # Fallback to parent
        parent_id = reference_to_id(ref.ref)
        if parent_id in compiler_env.term_ids_to_ast:
            error = unknown_reference_error_obj(term_id)
            add_static_msg_error(block, error)
            compiler_env.add_current_message_error(error)
            return compiler_env.term_ids_to_ast[parent_id], compiler_env.escaper_for_message(parent_id), None
    return None, None, unknown_reference(term_id, block, compiler_env)


def handle_message_reference(ref, block, compiler_env):
    msg_id = reference_to_id(ref)
    if msg_id in compiler_env.message_ids_to_ast:
        return do_message_call(msg_id, block, compiler_env)
    if isinstance(ref, AttributeExpression):
        # Fallback to parent
        parent_id = reference_to_id(ref.ref)
        if parent_id in compiler_env.message_ids_to_ast:
            error = unknown_reference_error_obj(msg_id)
            add_static_msg_error(block, error)
            compiler_env.add_current_message_error(error)
            return do_message_call(parent_id, block, compiler_env)
    return unknown_reference(msg_id, block, compiler_env)


def make_fluent_none(name, scope):
    # > FluentNone(name)
    # OR
    # > FluentNone()
    return codegen.ObjectCreation('FluentNone',
                                  [codegen.String(name)] if name else [],
                                  {},
                                  scope)


def numeric_to_native(val):
    """
    Given a numeric string (as defined by fluent spec),
    return an int or float
     """
    # val matches this EBNF:
    #  '-'? [0-9]+ ('.' [0-9]+)?
    if '.' in val:
        return float(val)
    return int(val)


def reserve_and_assign_name(block, suggested_name, value):
    """
    Reserves a name for the value in the scope block and adds assignment if
    necessary, returning the name reserved.

    May skip the assignment if not necessary.
    """
    if isinstance(value, codegen.VariableReference):
        # We don't need a new name, we can re-use this one.
        return value.name

    name = block.scope.reserve_name(suggested_name)
    block.add_assignment(name, value)
    return name


def resolve_select_expression_statically(select_expr, key_ast, block, compiler_env):
    """
    Resolve a select expression statically, given a codegen.PythonAst object
    `key_ast` representing the key value, or return None if not possible.
    """
    # We need to 'peek' inside what we've produced so far to see if it is something
    # static. To do that reliably we must simplify at this point:
    key_ast = codegen.simplify(key_ast)
    key_is_fluent_none = is_fluent_none(key_ast)
    key_is_number = (isinstance(key_ast, codegen.Number) or
                     (is_NUMBER_function_call(key_ast) and isinstance(key_ast.args[0], codegen.Number)))
    key_is_string = isinstance(key_ast, codegen.String)
    if not (key_is_string or key_is_number or key_is_fluent_none):
        return None

    if key_is_number:
        if isinstance(key_ast, codegen.Number):
            key_number_value = key_ast.number
        else:
            # peek into the number literal inside the `NUMBER` call.
            key_number_value = key_ast.args[0].number

    default_variant = None
    found = None
    for variant in select_expr.variants:
        if variant.default:
            default_variant = variant
            if key_is_fluent_none:
                found = variant
                break
        if key_is_string:
            if (isinstance(variant.key, Identifier) and
                    key_ast.string_value == variant.key.name):
                found = variant
                break
        elif key_is_number:
            if (isinstance(variant.key, NumberLiteral) and
                    key_number_value == numeric_to_native(variant.key.value)):
                found = variant
                break
            elif (isinstance(variant.key, Identifier) and
                    compiler_env.plural_form_function(key_number_value) == variant.key.name):
                found = variant
                break
    if found is None:
        found = default_variant

    return compile_expr(found.value, block, compiler_env)


def unknown_reference(name, block, compiler_env):
    error = unknown_reference_error_obj(name)
    add_static_msg_error(block, error)
    compiler_env.add_current_message_error(error)
    return make_fluent_none(name, block.scope)


def wrap_with_escaper(codegen_ast, block, compiler_env):
    escaper = compiler_env.current.escaper
    if escaper is null_escaper or escaper.escape is identity:
        return codegen_ast
    if escaper.output_type is codegen_ast.type:
        return codegen_ast
    return codegen.FunctionCall(escaper.escape_name(),
                                [codegen_ast],
                                {},
                                block.scope)


def wrap_with_mark_escaped(codegen_ast, block, compiler_env):
    escaper = compiler_env.current.escaper
    if escaper is null_escaper or escaper.mark_escaped is identity:
        return codegen_ast
    if escaper.output_type is codegen_ast.type:
        return codegen_ast
    return codegen.FunctionCall(escaper.mark_escaped_name(),
                                [codegen_ast],
                                {},
                                block.scope)

# AST checking and simplification

def is_DATETIME_function_call(codegen_ast):
    return (isinstance(codegen_ast, codegen.FunctionCall) and
            codegen_ast.function_name == BUILTIN_DATETIME)


def is_fluent_none(codegen_ast):
    return (isinstance(codegen_ast, codegen.ObjectCreation) and
            codegen_ast.function_name == 'FluentNone' and
            (len(codegen_ast.args) == 0 or
             isinstance(codegen_ast.args[0], codegen.String)))


def is_NUMBER_function_call(codegen_ast):
    return (isinstance(codegen_ast, codegen.FunctionCall) and
            codegen_ast.function_name == BUILTIN_NUMBER)


class Simplifier(object):
    def __init__(self, compiler_env):
        self.compiler_env = compiler_env

    def __call__(self, codegen_ast, changes):
        # Simplifications we can do on the AST tree. This function works
        # similarly to the PythonAst.simplify() methods i.e. we append to
        # changes if we made a change, and either mutate codegen_ast or
        # return a new/different object.

        # The logic here wouldn't be appropriate to put into codegen simplify()
        # methods because it is higher level and contains more logic specific to
        # Fluent.

        # We match against a number of patterns:

        # NUMBER(NUMBER(...)) -> NUMBER(...)     (i.e. no keyword args)
        if (is_NUMBER_function_call(codegen_ast) and not codegen_ast.kwargs and
                is_NUMBER_function_call(codegen_ast.args[0])):
            changes.append(True)
            return codegen_ast.args[0]

        # NUMBER(NUMBER(x), kwargs=...) -> NUMBER(x, kwargs=...)
        if (is_NUMBER_function_call(codegen_ast) and is_NUMBER_function_call(codegen_ast.args[0]) and
                not codegen_ast.args[0].kwargs):
            changes.append(True)
            codegen_ast.args[0] = codegen_ast.args[0].args[0]

        # Numeric literals in some function call keyword arguments don't need to be
        # wrapper in NUMBER
        # e.g. NUMBER(x, minimumIntegerDigits=NUMBER(1)) -> NUMBER(x, minimumIntegerDigits=1)
        #      DATETIME(x, hour12=NUMBER(1)) -> DATETIME(x, hour12=1)
        # We can't be sure for other custom functions, it depends how the args are used.
        if (is_DATETIME_function_call(codegen_ast) or is_NUMBER_function_call(codegen_ast)) and codegen_ast.kwargs:
            for kwarg_name, kwarg_value in list(codegen_ast.kwargs.items()):
                if is_NUMBER_function_call(kwarg_value) and not kwarg_value.kwargs:
                    codegen_ast.kwargs[kwarg_name] = kwarg_value.args[0]
                    changes.append(True)

        # Numeric literals used in comparisons (select expressions) don't need to be wrapped
        # in NUMBER(), because FluentNumber and int/float compare in the same way.
        # x == NUMBER(y)  -> x == y
        if (isinstance(codegen_ast, codegen.Equals) and
            is_NUMBER_function_call(codegen_ast.left) and
                not codegen_ast.left.kwargs):
            codegen_ast.left = codegen_ast.left.args[0]
            changes.append(True)
        # NUMBER(y) == x  -> y == x
        if (isinstance(codegen_ast, codegen.Equals) and
            is_NUMBER_function_call(codegen_ast.right) and
                not codegen_ast.right.kwargs):
            codegen_ast.right = codegen_ast.right.args[0]
            changes.append(True)

        # FluentNone('x').format(locale) -> 'x'
        if (isinstance(codegen_ast, codegen.MethodCall) and
            is_fluent_none(codegen_ast.obj) and
            codegen_ast.method_name == 'format' and
            isinstance(codegen_ast.args[0], codegen.VariableReference) and
                codegen_ast.args[0].name == LOCALE_NAME):
            make_fluent_none_call = codegen_ast.obj

            # We can make the FluentNone object now, call its format method
            if len(make_fluent_none_call.args) == 0:
                none_object = FluentNone()
            elif isinstance(make_fluent_none_call.args[0], codegen.String):
                none_object = FluentNone(make_fluent_none_call.args[0].string_value)
            else:
                none_object = None

            if none_object is not None:
                changes.append(True)
                return codegen.String(none_object.format(self.compiler_env.locale))

        return codegen_ast
