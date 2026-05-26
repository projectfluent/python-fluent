import pytest
from fluent.runtime import FluentBundle, FluentResource
from fluent.runtime.errors import FluentFormatError, FluentReferenceError

from ..utils import dedent_ftl


class TestParameterizedTerms:
    @pytest.fixture
    def bundle(self):
        bundle = FluentBundle(["en-US"], use_isolating=False)
        bundle.add_resource(
            FluentResource(
                dedent_ftl(
                    """
                    -thing = { $article ->
                          *[definite] the thing
                           [indefinite] a thing
                           [none] thing
                    }
                    thing-no-arg = { -thing }
                    thing-no-arg-alt = { -thing() }
                    thing-with-arg = { -thing(article: "indefinite") }
                    thing-positional-arg = { -thing("foo") }
                    thing-fallback = { -thing(article: "somethingelse") }
                    bad-term = { -missing() }
                    """
                )
            )
        )
        return bundle

    def test_argument_omitted(self, bundle):
        val, errs = bundle.format_pattern(bundle.get_message("thing-no-arg").value, {})
        assert val == "the thing"
        assert errs == []

    def test_argument_omitted_alt(self, bundle):
        val, errs = bundle.format_pattern(
            bundle.get_message("thing-no-arg-alt").value, {}
        )
        assert val == "the thing"
        assert errs == []

    def test_with_argument(self, bundle):
        val, errs = bundle.format_pattern(
            bundle.get_message("thing-with-arg").value, {}
        )
        assert val == "a thing"
        assert errs == []

    def test_positional_arg(self, bundle):
        val, errs = bundle.format_pattern(
            bundle.get_message("thing-positional-arg").value, {}
        )
        assert val == "the thing"
        assert errs == [
            FluentFormatError("Ignored positional arguments passed to term '-thing'")
        ]

    def test_fallback(self, bundle):
        val, errs = bundle.format_pattern(
            bundle.get_message("thing-fallback").value, {}
        )
        assert val == "the thing"
        assert errs == []

    def test_no_implicit_access_to_external_args(self, bundle):
        # The '-thing' term should not get passed article="indefinite"
        val, errs = bundle.format_pattern(
            bundle.get_message("thing-no-arg").value, {"article": "indefinite"}
        )
        assert val == "the thing"
        assert errs == []

    def test_no_implicit_access_to_external_args_but_term_args_still_passed(
        self, bundle
    ):
        val, errs = bundle.format_pattern(
            bundle.get_message("thing-with-arg").value, {"article": "none"}
        )
        assert val == "a thing"
        assert errs == []

    def test_bad_term(self, bundle):
        val, errs = bundle.format_pattern(bundle.get_message("bad-term").value, {})
        assert val == "{-missing}"
        assert errs == [FluentReferenceError("Unknown term: -missing")]


class TestParameterizedTermAttributes:
    @pytest.fixture
    def bundle(self):
        bundle = FluentBundle(["en-US"], use_isolating=False)
        bundle.add_resource(
            FluentResource(
                dedent_ftl(
                    """
                    -brand = Cool Thing
                        .status = { $version ->
                            [v2]     available
                           *[v1]     deprecated
                        }

                    attr-with-arg = { -brand } is { -brand.status(version: "v2") ->
                         [available]   available, yay!
                        *[deprecated]  deprecated, sorry
                    }

                    -other = { $arg ->
                                [a]  ABC
                               *[d]  DEF
                             }

                    missing-attr-ref = { -other.missing(arg: "a") ->
                         [ABC]  ABC option
                        *[DEF]  DEF option
                    }
                    """
                )
            )
        )
        return bundle

    def test_with_argument(self, bundle):
        val, errs = bundle.format_pattern(bundle.get_message("attr-with-arg").value, {})
        assert val == "Cool Thing is available, yay!"
        assert errs == []

    def test_missing_attr(self, bundle):
        # We don't fall back from attributes, get default.
        val, errs = bundle.format_pattern(
            bundle.get_message("missing-attr-ref").value, {}
        )
        assert val == "DEF option"
        assert errs == [FluentReferenceError("Unknown attribute: -other.missing")]


class TestNestedParameterizedTerms:
    @pytest.fixture
    def bundle(self):
        bundle = FluentBundle(["en-US"], use_isolating=False)
        bundle.add_resource(
            FluentResource(
                dedent_ftl(
                    """
                    -thing = { $article ->
                        *[definite] { $first-letter ->
                            *[lower] the thing
                             [upper] The thing
                         }
                         [indefinite] { $first-letter ->
                            *[lower] a thing
                             [upper] A thing
                         }
                     }

                    both-args = { -thing(first-letter: "upper", article: "indefinite") }.
                    outer-arg = This is { -thing(article: "indefinite") }.
                    inner-arg = { -thing(first-letter: "upper") }.
                    neither-arg = { -thing() }.
                    """
                )
            )
        )
        return bundle

    def test_both_args(self, bundle):
        val, errs = bundle.format_pattern(bundle.get_message("both-args").value, {})
        assert val == "A thing."
        assert errs == []

    def test_outer_arg(self, bundle):
        val, errs = bundle.format_pattern(bundle.get_message("outer-arg").value, {})
        assert val == "This is a thing."
        assert errs == []

    def test_inner_arg(self, bundle):
        val, errs = bundle.format_pattern(bundle.get_message("inner-arg").value, {})
        assert val == "The thing."
        assert errs == []

    def test_inner_arg_with_external_args(self, bundle):
        val, errs = bundle.format_pattern(
            bundle.get_message("inner-arg").value, {"article": "indefinite"}
        )
        assert val == "The thing."
        assert errs == []

    def test_neither_arg(self, bundle):
        val, errs = bundle.format_pattern(bundle.get_message("neither-arg").value, {})
        assert val == "the thing."
        assert errs == []


class TestTermsCalledFromTerms:
    @pytest.fixture
    def bundle(self):
        bundle = FluentBundle(["en-US"], use_isolating=False)
        bundle.add_resource(
            FluentResource(
                dedent_ftl(
                    """
                    -foo = {$a} {$b}
                    -bar = {-foo(b: 2)}
                    -baz = {-foo}
                    ref-bar = {-bar(a: 1)}
                    ref-baz = {-baz(a: 1)}
                    """
                )
            )
        )
        return bundle

    def test_term_args_isolated_with_call_syntax(self, bundle):
        val, errs = bundle.format_pattern(bundle.get_message("ref-bar").value, {})
        assert val == "a 2"
        assert errs == []

    def test_term_args_isolated_without_call_syntax(self, bundle):
        val, errs = bundle.format_pattern(bundle.get_message("ref-baz").value, {})
        assert val == "a b"
        assert errs == []


class TestMessagesCalledFromTerms:
    def test_messages_inherit_term_args(self):
        bundle = FluentBundle(["en-US"], use_isolating=False)
        bundle.add_resource(
            FluentResource(
                dedent_ftl(
                    """
                    msg = Msg is {$arg}
                    -foo = {msg}
                    ref-foo = {-foo(arg: 1)}
                    """
                )
            )
        )

        # This behaviour may change in future, message calls might be
        # disallowed from inside terms
        val, errs = bundle.format_pattern(
            bundle.get_message("ref-foo").value, {"arg": 2}
        )
        assert val == "Msg is 1"
        assert errs == []
