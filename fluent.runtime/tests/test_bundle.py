import pytest
from fluent.runtime import FluentBundle, FluentResource

from .utils import dedent_ftl


@pytest.fixture
def bundle():
    return FluentBundle(["en-US"])


class TestFluentBundle:
    def test_add_resource(self, bundle):
        bundle.add_resource(
            FluentResource(
                dedent_ftl(
                    """
            foo = Foo
            bar = Bar
            -baz = Baz
        """
                )
            )
        )
        assert "foo" in bundle._messages
        assert "bar" in bundle._messages
        assert "baz" in bundle._terms

    def test_has_message(self, bundle):
        bundle.add_resource(
            FluentResource(
                dedent_ftl(
                    """
            foo = Foo
        """
                )
            )
        )

        assert bundle.has_message("foo")
        assert not bundle.has_message("bar")

    def test_has_message_for_term(self, bundle):
        bundle.add_resource(
            FluentResource(
                dedent_ftl(
                    """
            -foo = Foo
        """
                )
            )
        )

        assert not bundle.has_message("-foo")

    def test_has_message_with_attribute(self, bundle):
        bundle.add_resource(
            FluentResource(
                dedent_ftl(
                    """
            foo = Foo
                .attr = Foo Attribute
        """
                )
            )
        )

        assert bundle.has_message("foo")
        assert not bundle.has_message("foo.attr")
        assert not bundle.has_message("foo.other-attribute")

    def test_plural_form_english_ints(self, bundle):
        assert bundle._plural_form(0) == "other"
        assert bundle._plural_form(1) == "one"
        assert bundle._plural_form(2) == "other"

    def test_plural_form_english_floats(self, bundle):
        assert bundle._plural_form(0.0) == "other"
        assert bundle._plural_form(1.0) == "one"
        assert bundle._plural_form(2.0) == "other"
        assert bundle._plural_form(0.5) == "other"

    def test_plural_form_french(self):
        # Just spot check one other, to ensure that we
        # are not getting the EN locale by accident or
        bundle = FluentBundle(["fr"])
        assert bundle._plural_form(0) == "one"
        assert bundle._plural_form(1) == "one"
        assert bundle._plural_form(2) == "other"

    def test_ordinal_form_english_ints(self, bundle):
        assert bundle._ordinal_form(0) == "other"
        assert bundle._ordinal_form(1) == "one"
        assert bundle._ordinal_form(2) == "two"
        assert bundle._ordinal_form(3) == "few"
        assert bundle._ordinal_form(11) == "other"
        assert bundle._ordinal_form(21) == "one"

    def test_format_args(self, bundle):
        bundle.add_resource(FluentResource("foo = Foo"))
        val, errs = bundle.format_pattern(bundle.get_message("foo").value)
        assert val == "Foo"

        val, errs = bundle.format_pattern(bundle.get_message("foo").value, {})
        assert val == "Foo"

    def test_format_missing(self, bundle):
        with pytest.raises(LookupError):
            bundle.get_message("a-missing-message")

    def test_format_term(self, bundle):
        bundle.add_resource(
            FluentResource(
                dedent_ftl(
                    """
            -foo = Foo
        """
                )
            )
        )
        with pytest.raises(LookupError):
            bundle.get_message("-foo")
        with pytest.raises(LookupError):
            bundle.get_message("foo")

    def test_message_and_term_separate(self, bundle):
        bundle.add_resource(
            FluentResource(
                dedent_ftl(
                    """
            foo = Refers to { -foo }
            -foo = Foo
        """
                )
            )
        )
        val, errs = bundle.format_pattern(bundle.get_message("foo").value, {})
        assert val == "Refers to \u2068Foo\u2069"
        assert errs == []
