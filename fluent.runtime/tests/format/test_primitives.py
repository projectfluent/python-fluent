import pytest
from fluent.runtime import FluentBundle, FluentResource

from ..utils import dedent_ftl


class TestSimpleStringValue:
    @pytest.fixture
    def bundle(self):
        bundle = FluentBundle(["en-US"], use_isolating=False)
        bundle.add_resource(
            FluentResource(
                dedent_ftl(
                    r"""
                    foo               = Foo
                    placeable-literal = { "Foo" } Bar
                    placeable-message = { foo } Bar
                    selector-literal = { "Foo" ->
                        [Foo] Member 1
                       *[Bar] Member 2
                     }
                    bar =
                        .attr = Bar Attribute
                    placeable-attr   = { bar.attr }
                    -baz = Baz
                        .attr = BazAttribute
                    selector-attr    = { -baz.attr ->
                        [BazAttribute] Member 3
                       *[other]        Member 4
                     }
                    escapes = {"    "}stuff{"\u0258}\"\\end"}
                    """
                )
            )
        )
        return bundle

    def test_can_be_used_as_a_value(self, bundle):
        val, errs = bundle.format_pattern(bundle.get_message("foo").value, {})
        assert val == "Foo"
        assert len(errs) == 0

    def test_can_be_used_in_a_placeable(self, bundle):
        val, errs = bundle.format_pattern(
            bundle.get_message("placeable-literal").value, {}
        )
        assert val == "Foo Bar"
        assert len(errs) == 0

    def test_can_be_a_value_of_a_message_referenced_in_a_placeable(self, bundle):
        val, errs = bundle.format_pattern(
            bundle.get_message("placeable-message").value, {}
        )
        assert val == "Foo Bar"
        assert len(errs) == 0

    def test_can_be_a_selector(self, bundle):
        val, errs = bundle.format_pattern(
            bundle.get_message("selector-literal").value, {}
        )
        assert val == "Member 1"
        assert len(errs) == 0

    def test_can_be_used_as_an_attribute_value(self, bundle):
        val, errs = bundle.format_pattern(
            bundle.get_message("bar").attributes["attr"], {}
        )
        assert val == "Bar Attribute"
        assert len(errs) == 0

    def test_can_be_a_value_of_an_attribute_used_in_a_placeable(self, bundle):
        val, errs = bundle.format_pattern(
            bundle.get_message("placeable-attr").value, {}
        )
        assert val == "Bar Attribute"
        assert len(errs) == 0

    def test_can_be_a_value_of_an_attribute_used_as_a_selector(self, bundle):
        val, errs = bundle.format_pattern(bundle.get_message("selector-attr").value, {})
        assert val == "Member 3"
        assert len(errs) == 0

    def test_escapes(self, bundle):
        val, errs = bundle.format_pattern(bundle.get_message("escapes").value, {})
        assert val == r'    stuffɘ}"\end'
        assert len(errs) == 0


class TestComplexStringValue:
    @pytest.fixture
    def bundle(self):
        bundle = FluentBundle(["en-US"], use_isolating=False)
        bundle.add_resource(
            FluentResource(
                dedent_ftl(
                    """
                    foo               = Foo
                    bar               = { foo }Bar

                    placeable-message = { bar }Baz

                    baz =
                        .attr = { bar }BazAttribute

                    -qux = Qux
                        .attr = { bar }QuxAttribute

                    placeable-attr = { baz.attr }

                    selector-attr = { -qux.attr ->
                        [FooBarQuxAttribute] FooBarQux
                       *[other] Other
                     }
                    """
                )
            )
        )
        return bundle

    def test_can_be_used_as_a_value(self, bundle):
        val, errs = bundle.format_pattern(bundle.get_message("bar").value, {})
        assert val == "FooBar"
        assert len(errs) == 0

    def test_can_be_value_of_a_message_referenced_in_a_placeable(self, bundle):
        val, errs = bundle.format_pattern(
            bundle.get_message("placeable-message").value, {}
        )
        assert val == "FooBarBaz"
        assert len(errs) == 0

    def test_can_be_used_as_an_attribute_value(self, bundle):
        val, errs = bundle.format_pattern(
            bundle.get_message("baz").attributes["attr"], {}
        )
        assert val == "FooBarBazAttribute"
        assert len(errs) == 0

    def test_can_be_a_value_of_an_attribute_used_in_a_placeable(self, bundle):
        val, errs = bundle.format_pattern(
            bundle.get_message("placeable-attr").value, {}
        )
        assert val == "FooBarBazAttribute"
        assert len(errs) == 0

    def test_can_be_a_value_of_an_attribute_used_as_a_selector(self, bundle):
        val, errs = bundle.format_pattern(bundle.get_message("selector-attr").value, {})
        assert val == "FooBarQux"
        assert len(errs) == 0


class TestNumbers:
    @pytest.fixture
    def bundle(self):
        bundle = FluentBundle(["en-US"], use_isolating=False)
        bundle.add_resource(
            FluentResource(
                dedent_ftl(
                    """
                    one           =  { 1 }
                    one_point_two =  { 1.2 }
                    select        =  { 1 ->
                       *[0] Zero
                        [1] One
                     }
                    position      =  { NUMBER(1, type: "ordinal") ->
                       *[other] Zero
                        [one] ${1}st
                     }
                    """
                )
            )
        )
        return bundle

    def test_int_number_used_in_placeable(self, bundle):
        val, errs = bundle.format_pattern(bundle.get_message("one").value, {})
        assert val == "1"
        assert len(errs) == 0

    def test_float_number_used_in_placeable(self, bundle):
        val, errs = bundle.format_pattern(bundle.get_message("one_point_two").value, {})
        assert val == "1.2"
        assert len(errs) == 0

    def test_can_be_used_as_a_selector(self, bundle):
        val, errs = bundle.format_pattern(bundle.get_message("select").value, {})
        assert val == "One"
        assert len(errs) == 0
