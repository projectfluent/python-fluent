from __future__ import absolute_import, unicode_literals

import unittest

from fluent.runtime import InterpretingFluentBundle

from .utils import dedent_ftl


# Only InterpretingFluentBundle has protection, for compiler it is too much of
# a (relative) performance hit and an increase in complexity to track this issue.

class TestBillionLaughs(unittest.TestCase):

    fluent_bundle_cls = InterpretingFluentBundle

    def setUp(self):
        self.ctx = self.fluent_bundle_cls(['en-US'], use_isolating=False)
        self.ctx.add_messages(dedent_ftl("""
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

        """))

    def test_max_length_protection(self):
        val, errs = self.ctx.format('lolz')
        self.assertEqual(val, ('0123456789' * 1000)[0:2500])
        self.assertNotEqual(len(errs), 0)

    def test_max_expansions_protection(self):
        # Without protection, emptylolz will take a really long time to
        # evaluate, although it generates an empty message.
        val, errs = self.ctx.format('emptylolz')
        self.assertEqual(val, '')
        self.assertEqual(len(errs), 1)
