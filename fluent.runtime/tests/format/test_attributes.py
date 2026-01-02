import pytest
from fluent.runtime import FluentBundle, FluentResource
from fluent.runtime.errors import FluentReferenceError

from ..utils import dedent_ftl


class TestAttributesWithStringValues:
    @pytest.fixture
    def bundle(self):
        bundle = FluentBundle(["en-US"], use_isolating=False)
        bundle.add_resource(
            FluentResource(
                dedent_ftl(
                    """
                    foo = Foo
                        .attr = Foo Attribute
                    bar = { foo } Bar
                        .attr = Bar Attribute
                    ref-foo = { foo.attr }
                    ref-bar = { bar.attr }
                    """
                )
            )
        )
        return bundle

    def test_can_be_referenced_for_entities_with_string_values(self, bundle):
        val, errs = bundle.format_pattern(bundle.get_message("ref-foo").value, {})
        assert val == "Foo Attribute"
        assert len(errs) == 0

    def test_can_be_referenced_for_entities_with_pattern_values(self, bundle):
        val, errs = bundle.format_pattern(bundle.get_message("ref-bar").value, {})
        assert val == "Bar Attribute"
        assert len(errs) == 0

    def test_can_be_formatted_directly_for_entities_with_string_values(self, bundle):
        val, errs = bundle.format_pattern(
            bundle.get_message("foo").attributes["attr"], {}
        )
        assert val == "Foo Attribute"
        assert len(errs) == 0

    def test_can_be_formatted_directly_for_entities_with_pattern_values(self, bundle):
        val, errs = bundle.format_pattern(
            bundle.get_message("bar").attributes["attr"], {}
        )
        assert val == "Bar Attribute"
        assert len(errs) == 0


class TestAttributesWithSimplePatternValues:
    @pytest.fixture
    def bundle(self):
        bundle = FluentBundle(["en-US"], use_isolating=False)
        bundle.add_resource(
            FluentResource(
                dedent_ftl(
                    """
                    foo = Foo
                    bar = Bar
                        .attr = { foo } Attribute
                    baz = { foo } Baz
                        .attr = { foo } Attribute
                    qux = Qux
                        .attr = { qux } Attribute
                    ref-bar = { bar.attr }
                    ref-baz = { baz.attr }
                    ref-qux = { qux.attr }
                    """
                )
            )
        )
        return bundle

    def test_can_be_referenced_for_entities_with_string_values(self, bundle):
        val, errs = bundle.format_pattern(bundle.get_message("ref-bar").value, {})
        assert val == "Foo Attribute"
        assert len(errs) == 0

    def test_can_be_formatted_directly_for_entities_with_string_values(self, bundle):
        val, errs = bundle.format_pattern(
            bundle.get_message("bar").attributes["attr"], {}
        )
        assert val == "Foo Attribute"
        assert len(errs) == 0

    def test_can_be_referenced_for_entities_with_pattern_values(self, bundle):
        val, errs = bundle.format_pattern(bundle.get_message("ref-baz").value, {})
        assert val == "Foo Attribute"
        assert len(errs) == 0

    def test_can_be_formatted_directly_for_entities_with_pattern_values(self, bundle):
        val, errs = bundle.format_pattern(
            bundle.get_message("baz").attributes["attr"], {}
        )
        assert val == "Foo Attribute"
        assert len(errs) == 0

    def test_works_with_self_references(self, bundle):
        val, errs = bundle.format_pattern(bundle.get_message("ref-qux").value, {})
        assert val == "Qux Attribute"
        assert len(errs) == 0

    def test_works_with_self_references_direct(self, bundle):
        val, errs = bundle.format_pattern(
            bundle.get_message("qux").attributes["attr"], {}
        )
        assert val == "Qux Attribute"
        assert len(errs) == 0


class TestMissing:
    @pytest.fixture
    def bundle(self):
        bundle = FluentBundle(["en-US"], use_isolating=False)
        bundle.add_resource(
            FluentResource(
                dedent_ftl(
                    """
                    foo = Foo
                    bar = Bar
                        .attr = Bar Attribute
                    baz = { foo } Baz
                    qux = { foo } Qux
                        .attr = Qux Attribute
                    ref-foo = { foo.missing }
                    ref-bar = { bar.missing }
                    ref-baz = { baz.missing }
                    ref-qux = { qux.missing }
                    attr-only =
                             .attr  = Attr Only Attribute
                    ref-double-missing = { missing.attr }
                    """
                )
            )
        )
        return bundle

    def test_msg_with_string_value_and_no_attributes(self, bundle):
        val, errs = bundle.format_pattern(bundle.get_message("ref-foo").value, {})
        assert val == "{foo.missing}"
        assert errs == [FluentReferenceError("Unknown attribute: foo.missing")]

    def test_msg_with_string_value_and_other_attributes(self, bundle):
        val, errs = bundle.format_pattern(bundle.get_message("ref-bar").value, {})
        assert val == "{bar.missing}"
        assert errs == [FluentReferenceError("Unknown attribute: bar.missing")]

    def test_msg_with_pattern_value_and_no_attributes(self, bundle):
        val, errs = bundle.format_pattern(bundle.get_message("ref-baz").value, {})
        assert val == "{baz.missing}"
        assert errs == [FluentReferenceError("Unknown attribute: baz.missing")]

    def test_msg_with_pattern_value_and_other_attributes(self, bundle):
        val, errs = bundle.format_pattern(bundle.get_message("ref-qux").value, {})
        assert val == "{qux.missing}"
        assert errs == [FluentReferenceError("Unknown attribute: qux.missing")]

    def test_attr_only_attribute(self, bundle):
        val, errs = bundle.format_pattern(
            bundle.get_message("attr-only").attributes["attr"], {}
        )
        assert val == "Attr Only Attribute"
        assert len(errs) == 0

    def test_missing_message_and_attribute(self, bundle):
        val, errs = bundle.format_pattern(
            bundle.get_message("ref-double-missing").value, {}
        )
        assert val == "{missing.attr}"
        assert errs == [FluentReferenceError("Unknown attribute: missing.attr")]
