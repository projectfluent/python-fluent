import pytest
from fluent.runtime import FluentBundle, FluentResource
from fluent.runtime.errors import FluentReferenceError

from ..utils import dedent_ftl


class TestSelectExpressionWithStrings:
    @pytest.fixture
    def bundle(self):
        return FluentBundle(["en-US"], use_isolating=False)

    def test_with_a_matching_selector(self, bundle):
        bundle.add_resource(
            FluentResource(
                dedent_ftl(
                    """
                    foo = { "a" ->
                        [a] A
                       *[b] B
                     }
                    """
                )
            )
        )
        val, errs = bundle.format_pattern(bundle.get_message("foo").value, {})
        assert val == "A"
        assert len(errs) == 0

    def test_with_a_non_matching_selector(self, bundle):
        bundle.add_resource(
            FluentResource(
                dedent_ftl(
                    """
                    foo = { "c" ->
                        [a] A
                       *[b] B
                     }
                    """
                )
            )
        )
        val, errs = bundle.format_pattern(bundle.get_message("foo").value, {})
        assert val == "B"
        assert len(errs) == 0

    def test_with_a_missing_selector(self, bundle):
        bundle.add_resource(
            FluentResource(
                dedent_ftl(
                    """
                    foo = { $none ->
                        [a] A
                       *[b] B
                     }
                    """
                )
            )
        )
        val, errs = bundle.format_pattern(bundle.get_message("foo").value, {})
        assert val == "B"
        assert errs == [FluentReferenceError("Unknown external: none")]

    def test_with_argument_expression(self, bundle):
        bundle.add_resource(
            FluentResource(
                dedent_ftl(
                    """
                    foo = { $arg ->
                        [a] A
                       *[b] B
                     }
                    """
                )
            )
        )
        val, errs = bundle.format_pattern(bundle.get_message("foo").value, {"arg": "a"})
        assert val == "A"


class TestSelectExpressionWithNumbers:
    @pytest.fixture
    def bundle(self):
        bundle = FluentBundle(["en-US"], use_isolating=False)
        bundle.add_resource(
            FluentResource(
                dedent_ftl(
                    """
                    foo = { 1 ->
                       *[0] A
                        [1] B
                     }

                    bar = { 2 ->
                       *[0] A
                        [1] B
                     }

                    baz = { $num ->
                       *[0] A
                        [1] B
                     }

                    qux = { 1.0 ->
                       *[0] A
                        [1] B
                     }
                    """
                )
            )
        )
        return bundle

    def test_selects_the_right_variant(self, bundle):
        val, errs = bundle.format_pattern(bundle.get_message("foo").value, {})
        assert val == "B"
        assert len(errs) == 0

    def test_with_a_non_matching_selector(self, bundle):
        val, errs = bundle.format_pattern(bundle.get_message("bar").value, {})
        assert val == "A"
        assert len(errs) == 0

    def test_with_a_missing_selector(self, bundle):
        val, errs = bundle.format_pattern(bundle.get_message("baz").value, {})
        assert val == "A"
        assert errs == [FluentReferenceError("Unknown external: num")]

    def test_with_argument_int(self, bundle):
        val, errs = bundle.format_pattern(bundle.get_message("baz").value, {"num": 1})
        assert val == "B"

    def test_with_argument_float(self, bundle):
        val, errs = bundle.format_pattern(bundle.get_message("baz").value, {"num": 1.0})
        assert val == "B"

    def test_with_float(self, bundle):
        val, errs = bundle.format_pattern(bundle.get_message("qux").value, {})
        assert val == "B"


class TestSelectExpressionWithPluralCategories:
    @pytest.fixture
    def bundle(self):
        bundle = FluentBundle(["en-US"], use_isolating=False)
        bundle.add_resource(
            FluentResource(
                dedent_ftl(
                    """
                    foo = { 1 ->
                        [one] A
                       *[other] B
                     }

                    bar = { 1 ->
                        [1] A
                       *[other] B
                     }

                    baz = { "not a number" ->
                        [one] A
                       *[other] B
                     }

                    qux = { $num ->
                        [one] A
                       *[other] B
                     }

                    count =  { NUMBER($num, type: "cardinal") ->
                       *[other] B
                        [one] A
                     }

                    order =  { NUMBER($num, type: "ordinal") ->
                       *[other] {$num}th
                        [one] {$num}st
                        [two] {$num}nd
                        [few] {$num}rd
                     }
                    """
                )
            )
        )
        return bundle

    def test_selects_the_right_category(self, bundle):
        val, errs = bundle.format_pattern(bundle.get_message("foo").value, {})
        assert val == "A"
        assert len(errs) == 0

    def test_selects_exact_match(self, bundle):
        val, errs = bundle.format_pattern(bundle.get_message("bar").value, {})
        assert val == "A"
        assert len(errs) == 0

    def test_selects_default_with_invalid_selector(self, bundle):
        val, errs = bundle.format_pattern(bundle.get_message("baz").value, {})
        assert val == "B"
        assert len(errs) == 0

    def test_with_a_missing_selector(self, bundle):
        val, errs = bundle.format_pattern(bundle.get_message("qux").value, {})
        assert val == "B"
        assert errs == [FluentReferenceError("Unknown external: num")]

    def test_with_argument_integer(self, bundle):
        val, errs = bundle.format_pattern(bundle.get_message("qux").value, {"num": 1})
        assert val == "A"
        assert len(errs) == 0

        val, errs = bundle.format_pattern(bundle.get_message("qux").value, {"num": 2})
        assert val == "B"
        assert len(errs) == 0

    def test_with_argument_float(self, bundle):
        val, errs = bundle.format_pattern(bundle.get_message("qux").value, {"num": 1.0})
        assert val == "A"
        assert len(errs) == 0

    def test_with_cardinal_integer(self, bundle):
        val, errs = bundle.format_pattern(bundle.get_message("count").value, {"num": 1})
        assert val == "A"
        assert len(errs) == 0

        val, errs = bundle.format_pattern(bundle.get_message("count").value, {"num": 2})
        assert val == "B"
        assert len(errs) == 0

    def test_with_cardinal_float(self, bundle):
        val, errs = bundle.format_pattern(
            bundle.get_message("count").value, {"num": 1.0}
        )
        assert val == "A"
        assert len(errs) == 0

    def test_with_ordinal_integer(self, bundle):
        val, errs = bundle.format_pattern(bundle.get_message("order").value, {"num": 1})
        assert val == "1st"
        assert len(errs) == 0

        val, errs = bundle.format_pattern(bundle.get_message("order").value, {"num": 2})
        assert val == "2nd"
        assert len(errs) == 0

        val, errs = bundle.format_pattern(
            bundle.get_message("order").value, {"num": 11}
        )
        assert val == "11th"
        assert len(errs) == 0

        val, errs = bundle.format_pattern(
            bundle.get_message("order").value, {"num": 21}
        )
        assert val == "21st"
        assert len(errs) == 0

    def test_with_ordinal_float(self, bundle):
        val, errs = bundle.format_pattern(
            bundle.get_message("order").value, {"num": 1.0}
        )
        assert val == "1st"
        assert len(errs) == 0


class TestSelectExpressionWithTerms:
    @pytest.fixture
    def bundle(self):
        bundle = FluentBundle(["en-US"], use_isolating=False)
        bundle.add_resource(
            FluentResource(
                dedent_ftl(
                    """
                    -my-term = term
                         .attr = termattribute

                    ref-term-attr = { -my-term.attr ->
                            [termattribute]   Term Attribute
                           *[other]           Other
                    }

                    ref-term-attr-other = { -my-term.attr ->
                            [x]      Term Attribute
                           *[other]  Other
                    }

                    ref-term-attr-missing = { -my-term.missing ->
                            [x]      Term Attribute
                           *[other]  Other
                    }
                    """
                )
            )
        )
        return bundle

    def test_ref_term_attribute(self, bundle):
        val, errs = bundle.format_pattern(bundle.get_message("ref-term-attr").value)
        assert val == "Term Attribute"
        assert len(errs) == 0

    def test_ref_term_attribute_fallback(self, bundle):
        val, errs = bundle.format_pattern(
            bundle.get_message("ref-term-attr-other").value
        )
        assert val == "Other"
        assert len(errs) == 0

    def test_ref_term_attribute_missing(self, bundle):
        val, errs = bundle.format_pattern(
            bundle.get_message("ref-term-attr-missing").value
        )
        assert val == "Other"
        assert len(errs) == 1
        assert errs == [FluentReferenceError("Unknown attribute: -my-term.missing")]
