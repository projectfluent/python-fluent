import pytest
from fluent.runtime import FluentBundle, FluentResource


bomb_source = """\
lol0 = 01234567890123456789012345678901234567890123456789
lol1 = {lol0}{lol0}{lol0}{lol0}{lol0}{lol0}{lol0}{lol0}{lol0}{lol0}
lol2 = {lol1}{lol1}{lol1}{lol1}{lol1}{lol1}{lol1}{lol1}{lol1}{lol1}
lol3 = {lol2}{lol2}{lol2}{lol2}{lol2}{lol2}{lol2}{lol2}{lol2}{lol2}
lol4 = {lol3}{lol3}{lol3}{lol3}{lol3}{lol3}{lol3}{lol3}{lol3}{lol3}
lolz = {lol4}

elol0 = { "" }
elol1 = {elol0}{elol0}{elol0}{elol0}{elol0}{elol0}{elol0}{elol0}{elol0}{elol0}
elol2 = {elol1}{elol1}{elol1}{elol1}{elol1}{elol1}{elol1}{elol1}{elol1}{elol1}
elol3 = {elol2}{elol2}{elol2}{elol2}{elol2}{elol2}{elol2}{elol2}{elol2}{elol2}
elol4 = {elol3}{elol3}{elol3}{elol3}{elol3}{elol3}{elol3}{elol3}{elol3}{elol3}
elol5 = {elol4}{elol4}{elol4}{elol4}{elol4}{elol4}{elol4}{elol4}{elol4}{elol4}
elol6 = {elol5}{elol5}{elol5}{elol5}{elol5}{elol5}{elol5}{elol5}{elol5}{elol5}
emptylolz = {elol6}
"""


@pytest.fixture
def bundle():
    bundle = FluentBundle(["en-US"], use_isolating=False)
    bundle.add_resource(FluentResource(bomb_source))
    return bundle


class TestBillionLaughs:
    def test_max_length_protection(self, bundle):
        val, errs = bundle.format_pattern(bundle.get_message("lolz").value)
        assert val == "{???}"
        assert len(errs) != 0
        assert "Too many characters" in str(errs[-1])
        assert "max allowed is 2500" in str(errs[-1])

    def test_max_expansions_protection(self, bundle):
        # Without protection, emptylolz will take a really long time to
        # evaluate, although it generates an empty message.
        val, errs = bundle.format_pattern(bundle.get_message("emptylolz").value)
        assert val == "{???}"
        assert len(errs) == 1
        assert "Too many parts" in str(errs[-1])


class TestLongText:
    # The length limit protects against expansion of placeables, and
    # should not apply to text written directly in the message.
    @pytest.mark.parametrize("use_isolating", [True, False])
    def test_long_text_with_placeable(self, use_isolating):
        long_text = "x" * 3000
        bundle = FluentBundle(["en-US"], use_isolating=use_isolating)
        bundle.add_resource(FluentResource(f"long = {long_text} {{ $arg }}\n"))
        val, errs = bundle.format_pattern(
            bundle.get_message("long").value, {"arg": "y"}
        )
        y = "\u2068y\u2069" if use_isolating else "y"
        assert val == f"{long_text} {y}"
        assert errs == []

    def test_long_string_literal(self):
        long_text = "x" * 3000
        bundle = FluentBundle(["en-US"], use_isolating=False)
        bundle.add_resource(FluentResource(f'long = {{ "{long_text}" }} {{ $arg }}\n'))
        val, errs = bundle.format_pattern(
            bundle.get_message("long").value, {"arg": "y"}
        )
        assert val == f"{long_text} y"
        assert errs == []

    @pytest.mark.parametrize("n, expected", [(1, "{text}"), (2, "{text} 2")])
    def test_long_text_in_select_variant(self, n, expected):
        long_text = "x" * 3000
        bundle = FluentBundle(["en-US"], use_isolating=False)
        bundle.add_resource(
            FluentResource(
                f"long = {{ $n ->\n"
                f"    [one] {long_text}\n"
                f"   *[other] {long_text} {{ $n }}\n"
                f"}}\n"
            )
        )
        val, errs = bundle.format_pattern(bundle.get_message("long").value, {"n": n})
        assert val == expected.format(text=long_text)
        assert errs == []

    def test_long_select_variant_after_text(self):
        long_text = "x" * 3000
        bundle = FluentBundle(["en-US"], use_isolating=False)
        bundle.add_resource(
            FluentResource(f"long = Hi {{ $n ->\n   *[other] {long_text}\n}}\n")
        )
        val, errs = bundle.format_pattern(bundle.get_message("long").value, {"n": 1})
        assert val == f"Hi {long_text}"
        assert errs == []
