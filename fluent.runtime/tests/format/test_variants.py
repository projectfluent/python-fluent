from __future__ import absolute_import, unicode_literals

import unittest

from fluent.runtime.errors import FluentReferenceError

from .. import all_fluent_bundle_implementations
from ..utils import dedent_ftl


@all_fluent_bundle_implementations
class TestVariants(unittest.TestCase):

    def setUp(self):
        self.ctx = self.fluent_bundle_cls(['en-US'], use_isolating=False)
        self.ctx.add_messages(dedent_ftl("""
            -variant = {
                [a] A
               *[b] B
             }
            foo = { -variant }
            bar = { -variant[a] }
            baz = { -variant[b] }
            qux = { -variant[c] }
            goo = { -missing[a] }
        """))

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
        self.assertIn(
            errs[0],
            [FluentReferenceError("Unknown variant: c"),
             FluentReferenceError("Unknown variant: -variant[c]")]
        )

    def test_choose_missing_term(self):
        val, errs = self.ctx.format('goo', {})
        self.assertEqual(val, '-missing')
        self.assertEqual(len(errs), 1)
        self.assertEqual(
            errs,
            [FluentReferenceError("Unknown term: -missing")])
