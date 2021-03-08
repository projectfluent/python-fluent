import unittest

from fluent.runtime import FluentBundle, FluentResource

from .utils import dedent_ftl


class TestBillionLaughs(unittest.TestCase):

    def setUp(self):
        self.ctx = FluentBundle(['en-US'], use_isolating=False)
        self.ctx.add_resource(FluentResource(dedent_ftl("""
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

        """)))

    def test_max_length_protection(self):
        val, errs = self.ctx.format_pattern(self.ctx.get_message('lolz').value)
        self.assertEqual(val, '{???}')
        self.assertNotEqual(len(errs), 0)
        self.assertIn('Too many characters', str(errs[-1]))

    def test_max_expansions_protection(self):
        # Without protection, emptylolz will take a really long time to
        # evaluate, although it generates an empty message.
        val, errs = self.ctx.format_pattern(self.ctx.get_message('emptylolz').value)
        self.assertEqual(val, '{???}')
        self.assertEqual(len(errs), 1)
        self.assertIn('Too many parts', str(errs[-1]))
