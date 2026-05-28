import pytest

from fluent.runtime import FluentBundle, FluentResource

from ..utils import dedent_ftl


class TestNumbersInValues:
    @pytest.fixture
    def bundle(self):
        bundle = FluentBundle(["en-US"], use_isolating=False)
        bundle.add_resource(
            FluentResource(
                dedent_ftl(
                    """
                    foo = Foo { $num }
                    bar = { foo }
                    baz =
                        .attr = Baz Attribute { $num }
                    qux = { "a" ->
                       *[a]     Baz Variant A { $num }
                     }
                    """
                )
            )
        )
        return bundle

    def test_can_be_used_in_the_message_value(self, bundle):
        val, errs = bundle.format_pattern(bundle.get_message("foo").value, {"num": 3})
        assert val == "Foo 3"
        assert len(errs) == 0

    def test_can_be_used_in_the_message_value_which_is_referenced(self, bundle):
        val, errs = bundle.format_pattern(bundle.get_message("bar").value, {"num": 3})
        assert val == "Foo 3"
        assert len(errs) == 0

    def test_can_be_used_in_an_attribute(self, bundle):
        val, errs = bundle.format_pattern(
            bundle.get_message("baz").attributes["attr"], {"num": 3}
        )
        assert val == "Baz Attribute 3"
        assert len(errs) == 0

    def test_can_be_used_in_a_variant(self, bundle):
        val, errs = bundle.format_pattern(bundle.get_message("qux").value, {"num": 3})
        assert val == "Baz Variant A 3"
        assert len(errs) == 0


class TestStrings:
    def test_can_be_a_string(self):
        bundle = FluentBundle(["en-US"], use_isolating=False)
        bundle.add_resource(FluentResource("foo = { $arg }"))

        val, errs = bundle.format_pattern(
            bundle.get_message("foo").value, {"arg": "Argument"}
        )
        assert val == "Argument"
        assert len(errs) == 0
