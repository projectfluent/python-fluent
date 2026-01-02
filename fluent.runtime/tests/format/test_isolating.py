import pytest

from fluent.runtime import FluentBundle, FluentResource

from ..utils import dedent_ftl

# Unicode bidi isolation characters.
FSI = "\u2068"
PDI = "\u2069"


class TestUseIsolating:
    @pytest.fixture
    def bundle(self):
        bundle = FluentBundle(["en-US"])
        bundle.add_resource(
            FluentResource(
                dedent_ftl(
                    """
                    foo = Foo
                    bar = { foo } Bar
                    baz = { $arg } Baz
                    qux = { bar } { baz }
                    """
                )
            )
        )
        return bundle

    def test_isolates_interpolated_message_references(self, bundle):
        val, errs = bundle.format_pattern(bundle.get_message("bar").value, {})
        assert val == FSI + "Foo" + PDI + " Bar"
        assert len(errs) == 0

    def test_isolates_interpolated_string_typed_variable_references(self, bundle):
        val, errs = bundle.format_pattern(
            bundle.get_message("baz").value, {"arg": "Arg"}
        )
        assert val == FSI + "Arg" + PDI + " Baz"
        assert len(errs) == 0

    def test_isolates_interpolated_number_typed_variable_references(self, bundle):
        val, errs = bundle.format_pattern(bundle.get_message("baz").value, {"arg": 1})
        assert val == FSI + "1" + PDI + " Baz"
        assert len(errs) == 0

    def test_isolates_complex_interpolations(self, bundle):
        val, errs = bundle.format_pattern(
            bundle.get_message("qux").value, {"arg": "Arg"}
        )
        expected_bar = FSI + FSI + "Foo" + PDI + " Bar" + PDI
        expected_baz = FSI + FSI + "Arg" + PDI + " Baz" + PDI
        assert val == expected_bar + " " + expected_baz
        assert len(errs) == 0


class TestSkipIsolating:
    @pytest.fixture
    def bundle(self):
        bundle = FluentBundle(["en-US"])
        bundle.add_resource(
            FluentResource(
                dedent_ftl(
                    """
                    -brand-short-name = Amaya
                    foo = { -brand-short-name }
                    with-arg = { $arg }
                    """
                )
            )
        )
        return bundle

    def test_skip_isolating_chars_if_just_one_message_ref(self, bundle):
        val, errs = bundle.format_pattern(bundle.get_message("foo").value, {})
        assert val == "Amaya"
        assert len(errs) == 0

    def test_skip_isolating_chars_if_just_one_placeable_arg(self, bundle):
        val, errs = bundle.format_pattern(
            bundle.get_message("with-arg").value, {"arg": "Arg"}
        )
        assert val == "Arg"
        assert len(errs) == 0
