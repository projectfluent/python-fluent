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

    def test_max_expansions_protection(self, bundle):
        # Without protection, emptylolz will take a really long time to
        # evaluate, although it generates an empty message.
        val, errs = bundle.format_pattern(bundle.get_message("emptylolz").value)
        assert val == "{???}"
        assert len(errs) == 1
        assert "Too many parts" in str(errs[-1])
