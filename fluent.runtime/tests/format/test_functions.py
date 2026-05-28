import pytest
from fluent.runtime import FluentBundle, FluentResource
from fluent.runtime.errors import FluentReferenceError
from fluent.runtime.types import FluentNone

from ..utils import dedent_ftl


class TestFunctionCalls:
    @pytest.fixture
    def bundle(self):
        bundle = FluentBundle(
            ["en-US"], use_isolating=False, functions={"IDENTITY": lambda x: x}
        )
        bundle.add_resource(
            FluentResource(
                dedent_ftl(
                    """
                    foo = Foo
                        .attr = Attribute
                    pass-nothing       = { IDENTITY() }
                    pass-string        = { IDENTITY("a") }
                    pass-number        = { IDENTITY(1) }
                    pass-message       = { IDENTITY(foo) }
                    pass-attr          = { IDENTITY(foo.attr) }
                    pass-external      = { IDENTITY($ext) }
                    pass-function-call = { IDENTITY(IDENTITY(1)) }
                    """
                )
            )
        )
        return bundle

    def test_accepts_strings(self, bundle):
        val, errs = bundle.format_pattern(bundle.get_message("pass-string").value, {})
        assert val == "a"
        assert len(errs) == 0

    def test_accepts_numbers(self, bundle):
        val, errs = bundle.format_pattern(bundle.get_message("pass-number").value, {})
        assert val == "1"
        assert len(errs) == 0

    def test_accepts_entities(self, bundle):
        val, errs = bundle.format_pattern(bundle.get_message("pass-message").value, {})
        assert val == "Foo"
        assert len(errs) == 0

    def test_accepts_attributes(self, bundle):
        val, errs = bundle.format_pattern(bundle.get_message("pass-attr").value, {})
        assert val == "Attribute"
        assert len(errs) == 0

    def test_accepts_externals(self, bundle):
        val, errs = bundle.format_pattern(
            bundle.get_message("pass-external").value, {"ext": "Ext"}
        )
        assert val == "Ext"
        assert len(errs) == 0

    def test_accepts_function_calls(self, bundle):
        val, errs = bundle.format_pattern(
            bundle.get_message("pass-function-call").value, {}
        )
        assert val == "1"
        assert len(errs) == 0

    def test_wrong_arity(self, bundle):
        val, errs = bundle.format_pattern(bundle.get_message("pass-nothing").value, {})
        assert val == "IDENTITY()"
        assert len(errs) == 1
        assert isinstance(errs[0], TypeError)


class TestMissing:
    def test_falls_back_to_name_of_function(self):
        bundle = FluentBundle(["en-US"], use_isolating=False)
        bundle.add_resource(FluentResource("missing = { MISSING(1) }"))

        val, errs = bundle.format_pattern(bundle.get_message("missing").value, {})
        assert val == "MISSING()"
        assert errs == [FluentReferenceError("Unknown function: MISSING")]


class TestResolving:
    @pytest.fixture
    def args_passed(self):
        return []

    @pytest.fixture
    def bundle(self, args_passed):
        def number_processor(number):
            args_passed.append(number)
            return number

        bundle = FluentBundle(
            ["en-US"],
            use_isolating=False,
            functions={"NUMBER_PROCESSOR": number_processor},
        )
        bundle.add_resource(
            FluentResource(
                "pass-number = { NUMBER_PROCESSOR(1) }\n"
                + "pass-arg = { NUMBER_PROCESSOR($arg) }\n"
            )
        )
        return bundle

    def test_args_passed_as_numbers(self, args_passed, bundle):
        val, errs = bundle.format_pattern(
            bundle.get_message("pass-arg").value, {"arg": 1}
        )
        assert val == "1"
        assert len(errs) == 0
        assert args_passed == [1]

    def test_literals_passed_as_numbers(self, args_passed, bundle):
        val, errs = bundle.format_pattern(bundle.get_message("pass-number").value, {})
        assert val == "1"
        assert len(errs) == 0
        assert args_passed == [1]


class TestKeywordArgs:
    @pytest.fixture
    def args_passed(self):
        return []

    @pytest.fixture
    def bundle(self, args_passed):
        def my_function(arg, kwarg1=None, kwarg2="default"):
            args_passed.append((arg, kwarg1, kwarg2))
            return arg

        bundle = FluentBundle(
            ["en-US"], use_isolating=False, functions={"MYFUNC": my_function}
        )
        bundle.add_resource(
            FluentResource(
                dedent_ftl(
                    """
                    pass-arg        = { MYFUNC("a") }
                    pass-kwarg1     = { MYFUNC("a", kwarg1: 1) }
                    pass-kwarg2     = { MYFUNC("a", kwarg2: "other") }
                    pass-kwargs     = { MYFUNC("a", kwarg1: 1, kwarg2: "other") }
                    pass-user-arg   = { MYFUNC($arg) }
                    """
                )
            )
        )
        return bundle

    def test_defaults(self, args_passed, bundle):
        val, errs = bundle.format_pattern(bundle.get_message("pass-arg").value, {})
        assert args_passed == [("a", None, "default")]
        assert len(errs) == 0

    def test_pass_kwarg1(self, args_passed, bundle):
        val, errs = bundle.format_pattern(bundle.get_message("pass-kwarg1").value, {})
        assert args_passed == [("a", 1, "default")]
        assert len(errs) == 0

    def test_pass_kwarg2(self, args_passed, bundle):
        val, errs = bundle.format_pattern(bundle.get_message("pass-kwarg2").value, {})
        assert args_passed == [("a", None, "other")]
        assert len(errs) == 0

    def test_pass_kwargs(self, args_passed, bundle):
        val, errs = bundle.format_pattern(bundle.get_message("pass-kwargs").value, {})
        assert args_passed == [("a", 1, "other")]
        assert len(errs) == 0

    def test_missing_arg(self, args_passed, bundle):
        val, errs = bundle.format_pattern(bundle.get_message("pass-user-arg").value, {})
        assert args_passed == [(FluentNone("arg"), None, "default")]
        assert len(errs) == 1
