"""
Compatibility module for generating Python AST.

The interface mocks the stdlib 'ast' module of the most recent Python version we
support, so that the codegen module can be written as if it targets that
version. For older versions we provide shims that adapt to the older AST as and
when necessary.

"""
import ast
import sys

PY2 = sys.version_info < (3, 0)

# We include only the things codegen needs.
Assign = ast.Assign
BoolOp = ast.BoolOp
Compare = ast.Compare
Dict = ast.Dict
Eq = ast.Eq
ExceptHandler = ast.ExceptHandler
Expr = ast.Expr
If = ast.If
Index = ast.Index
List = ast.List
Load = ast.Load
Module = ast.Module
Num = ast.Num
Or = ast.Or
Pass = ast.Pass
Return = ast.Return
Store = ast.Store
Str = ast.Str
Subscript = ast.Subscript
Tuple = ast.Tuple
arguments = ast.arguments

if PY2:
    # Python 2 needs identifiers to be bytestrings, not unicode strings:
    def change_attrs_to_str(ast_class, attr_list):
        def wrapper(**kwargs):
            for attr in attr_list:
                if attr in kwargs and isinstance(kwargs[attr], unicode):
                    kwargs[attr] = str(kwargs[attr])
            return ast_class(**kwargs)
        return wrapper

    Attribute = change_attrs_to_str(ast.Attribute, ['attr'])

    def Call(func=None, args=[], keywords=[], **other_args):
        # For **expr syntax:
        #  - in Python 2 Ast, we have ast.Call(kwargs=expr)
        #  - in Python 3 Ast, we have ast.Call(keywords=keywords) where
        #    `keywords` contains a special item: `keyword(arg=None, value=expr)`.
        # Here we convert Python 3 convention back to Python 2 Ast.
        kwargs = None
        python_2_keywords = []
        for k in keywords:
            if k.arg is None:
                kwargs = k.value
            else:
                python_2_keywords.append(k)
        return ast.Call(func=func,
                        args=args,
                        keywords=python_2_keywords,
                        kwargs=kwargs,
                        **other_args)

    FunctionDef = change_attrs_to_str(ast.FunctionDef, ['name'])
    Name = change_attrs_to_str(ast.Name, ['id'])

    def NameConstant(value=None, **kwargs):
        if value is None:
            return Name(id='None', ctx=ast.Load(), **kwargs)
        else:
            raise AssertionError("Don't know how to translate NameConstant(value={!r})".format(value))

    Try = ast.TryExcept

    def arg(arg=None, annotation=None, **kwargs):
        return Name(id=str(arg), ctx=ast.Param(), **kwargs)

    keyword = change_attrs_to_str(ast.keyword, ['arg'])
else:
    Attribute = ast.Attribute
    Call = ast.Call
    FunctionDef = ast.FunctionDef
    Name = ast.Name
    NameConstant = ast.NameConstant
    Try = ast.Try
    arg = ast.arg
    keyword = ast.keyword
