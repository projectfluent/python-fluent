from __future__ import absolute_import, unicode_literals

import unittest

from fluent.exceptions import FluentReferenceError

from .. import all_message_context_implementations
from ..syntax import dedent_ftl


@all_message_context_implementations
class TestVariants(unittest.TestCase):

    def setUp(self):
        self.ctx = self.message_context_cls(['en-US'], use_isolating=False)
        self.ctx.add_messages(dedent_ftl("""
            variant = {
                [a] A
               *[b] B
             }
            foo = { variant }
            bar = { variant[a] }
            baz = { variant[b] }
            qux = { variant[c] }
        """))

    def test_format_directly_returns_the_default_variant(self):
        val, errs = self.ctx.format('variant', {})
        self.assertEqual(val, 'B')
        self.assertEqual(len(errs), 0)

    def test_returns_the_default_variant(self):
        val, errs = self.ctx.format('foo', {})
        self.assertEqual(val, 'B')
        self.assertEqual(len(errs), 0)

    def test_choose_other_variant(self):
        val, errs = self.ctx.format('bar', {})
        self.assertEqual(val, 'A')
        self.assertEqual(len(errs), 0)

    def test_choose_default_variant(self):
        val, errs = self.ctx.format('baz', {})
        self.assertEqual(val, 'B')
        self.assertEqual(len(errs), 0)

    def test_choose_missing_variant(self):
        val, errs = self.ctx.format('qux', {})
        self.assertEqual(val, 'B')
        self.assertEqual(len(errs), 1)
        self.assertEqual(
            errs,
            [FluentReferenceError("Unknown variant: c")])