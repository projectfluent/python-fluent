import pytest
from fluent.runtime import FluentBundle, FluentResource
from fluent.runtime.errors import FluentCyclicReferenceError, FluentReferenceError

from ..utils import dedent_ftl


class TestPlaceables:
    @pytest.fixture
    def bundle(self):
        bundle = FluentBundle(["en-US"], use_isolating=False)
        bundle.add_resource(
            FluentResource(
                dedent_ftl(
                    """
                    message = Message
                            .attr = Message Attribute
                    -term = Term
                          .attr = Term Attribute
                    -term2 = {
                       *[variant1] Term Variant 1
                        [variant2] Term Variant 2
                     }

                    uses-message = { message }
                    uses-message-attr = { message.attr }
                    uses-term = { -term }

                    bad-message-ref = Text { not-a-message }
                    bad-message-attr-ref = Text { message.not-an-attr }
                    bad-term-ref = Text { -not-a-term }

                    self-referencing-message = Text { self-referencing-message }
                    cyclic-msg1 = Text1 { cyclic-msg2 }
                    cyclic-msg2 = Text2 { cyclic-msg1 }
                    self-cyclic-message = Parent { self-cyclic-message.attr }
                                        .attr = Attribute { self-cyclic-message }

                    self-attribute-ref-ok = Parent { self-attribute-ref-ok.attr }
                                          .attr = Attribute
                    self-parent-ref-ok = Parent
                                       .attr =  Attribute { self-parent-ref-ok }
                    """
                )
            )
        )
        return bundle

    def test_placeable_message(self, bundle):
        val, errs = bundle.format_pattern(bundle.get_message("uses-message").value, {})
        assert val == "Message"
        assert len(errs) == 0

    def test_placeable_message_attr(self, bundle):
        val, errs = bundle.format_pattern(
            bundle.get_message("uses-message-attr").value, {}
        )
        assert val == "Message Attribute"
        assert len(errs) == 0

    def test_placeable_term(self, bundle):
        val, errs = bundle.format_pattern(bundle.get_message("uses-term").value, {})
        assert val == "Term"
        assert len(errs) == 0

    def test_placeable_bad_message(self, bundle):
        val, errs = bundle.format_pattern(
            bundle.get_message("bad-message-ref").value, {}
        )
        assert val == "Text {not-a-message}"
        assert len(errs) == 1
        assert errs == [FluentReferenceError("Unknown message: not-a-message")]

    def test_placeable_bad_message_attr(self, bundle):
        val, errs = bundle.format_pattern(
            bundle.get_message("bad-message-attr-ref").value, {}
        )
        assert val == "Text {message.not-an-attr}"
        assert len(errs) == 1
        assert errs == [FluentReferenceError("Unknown attribute: message.not-an-attr")]

    def test_placeable_bad_term(self, bundle):
        val, errs = bundle.format_pattern(bundle.get_message("bad-term-ref").value, {})
        assert val == "Text {-not-a-term}"
        assert len(errs) == 1
        assert errs == [FluentReferenceError("Unknown term: -not-a-term")]

    def test_cycle_detection(self, bundle):
        val, errs = bundle.format_pattern(
            bundle.get_message("self-referencing-message").value, {}
        )
        assert val == "Text ???"
        assert len(errs) == 1
        assert errs == [FluentCyclicReferenceError("Cyclic reference")]

    def test_mutual_cycle_detection(self, bundle):
        val, errs = bundle.format_pattern(bundle.get_message("cyclic-msg1").value, {})
        assert val == "Text1 Text2 ???"
        assert len(errs) == 1
        assert errs == [FluentCyclicReferenceError("Cyclic reference")]

    def test_allowed_self_reference(self, bundle):
        val, errs = bundle.format_pattern(
            bundle.get_message("self-attribute-ref-ok").value, {}
        )
        assert val == "Parent Attribute"
        assert len(errs) == 0
        val, errs = bundle.format_pattern(
            bundle.get_message("self-parent-ref-ok").attributes["attr"], {}
        )
        assert val == "Attribute Parent"
        assert len(errs) == 0


class TestSingleElementPattern:
    def test_single_literal_number_isolating(self):
        bundle = FluentBundle(["en-US"], use_isolating=True)
        bundle.add_resource(FluentResource("foo = { 1 }"))
        val, errs = bundle.format_pattern(bundle.get_message("foo").value)
        assert val == "1"
        assert errs == []

    def test_single_literal_number_non_isolating(self):
        bundle = FluentBundle(["en-US"], use_isolating=False)
        bundle.add_resource(FluentResource("foo = { 1 }"))
        val, errs = bundle.format_pattern(bundle.get_message("foo").value)
        assert val == "1"
        assert errs == []

    def test_single_arg_number_isolating(self):
        bundle = FluentBundle(["en-US"], use_isolating=True)
        bundle.add_resource(FluentResource("foo = { $arg }"))
        val, errs = bundle.format_pattern(bundle.get_message("foo").value, {"arg": 1})
        assert val == "1"
        assert errs == []

    def test_single_arg_number_non_isolating(self):
        bundle = FluentBundle(["en-US"], use_isolating=False)
        bundle.add_resource(FluentResource("foo = { $arg }"))
        val, errs = bundle.format_pattern(bundle.get_message("foo").value, {"arg": 1})
        assert val == "1"
        assert errs == []

    def test_single_arg_missing_isolating(self):
        bundle = FluentBundle(["en-US"], use_isolating=True)
        bundle.add_resource(FluentResource("foo = { $arg }"))
        val, errs = bundle.format_pattern(bundle.get_message("foo").value)
        assert val == "arg"
        assert len(errs) == 1

    def test_single_arg_missing_non_isolating(self):
        bundle = FluentBundle(["en-US"], use_isolating=False)
        bundle.add_resource(FluentResource("foo = { $arg }"))
        val, errs = bundle.format_pattern(bundle.get_message("foo").value)
        assert val == "arg"
        assert len(errs) == 1
