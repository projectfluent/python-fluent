from __future__ import absolute_import, unicode_literals

import unittest

from fluent.context import MessageContext

from .syntax import dedent_ftl


class TestBillionLaughs(unittest.TestCase):

    def setUp(self):
        self.ctx = MessageContext(['en-US'], use_isolating=False)
        self.ctx.add_messages(dedent_ftl("""
            lol0 = 01234567890123456789012345678901234567890123456789
            lol1 = {lol0}{lol0}{lol0}{lol0}{lol0}{lol0}{lol0}{lol0}{lol0}{lol0}
            lol2 = {lol1}{lol1}{lol1}{lol1}{lol1}{lol1}{lol1}{lol1}{lol1}{lol1}
            lol3 = {lol2}{lol2}{lol2}{lol2}{lol2}{lol2}{lol2}{lol2}{lol2}{lol2}
            lol4 = {lol3}{lol3}{lol3}{lol3}{lol3}{lol3}{lol3}{lol3}{lol3}{lol3}
            lolz = {lol4}

            emptylol0 = { "" }
            emptylol1 = {emptylol0}{emptylol0}{emptylol0}{emptylol0}{emptylol0}{emptylol0}{emptylol0}{emptylol0}{emptylol0}{emptylol0}
            emptylol2 = {emptylol1}{emptylol1}{emptylol1}{emptylol1}{emptylol1}{emptylol1}{emptylol1}{emptylol1}{emptylol1}{emptylol1}
            emptylol3 = {emptylol2}{emptylol2}{emptylol2}{emptylol2}{emptylol2}{emptylol2}{emptylol2}{emptylol2}{emptylol2}{emptylol2}
            emptylol4 = {emptylol3}{emptylol3}{emptylol3}{emptylol3}{emptylol3}{emptylol3}{emptylol3}{emptylol3}{emptylol3}{emptylol3}
            emptylol5 = {emptylol4}{emptylol4}{emptylol4}{emptylol4}{emptylol4}{emptylol4}{emptylol4}{emptylol4}{emptylol4}{emptylol4}
            emptylol6 = {emptylol5}{emptylol5}{emptylol5}{emptylol5}{emptylol5}{emptylol5}{emptylol5}{emptylol5}{emptylol5}{emptylol5}
            emptylolz = {emptylol6}

        """))

    def test_max_length_protection(self):
        val, errs = self.ctx.format('lolz')
        self.assertEqual(val, ('0123456789' * 1000)[0:2500])
        self.assertNotEqual(len(errs), 0)

    def test_max_expansions_protection(self):
        # Without protection, emptylolz will take a really long time to
        # evaluate, although it generates an empty message.
        val, errs = self.ctx.format('emptylolz')
        self.assertEqual(val, '???')
        self.assertEqual(len(errs), 1)
