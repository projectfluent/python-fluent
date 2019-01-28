from __future__ import absolute_import, unicode_literals

import unittest

from fluent.runtime import FluentBundle
from fluent.runtime.errors import FluentFormatError, FluentReferenceError

from ..utils import dedent_ftl


class TestParameterizedTerms(unittest.TestCase):

    def setUp(self):
        self.ctx = FluentBundle(['en-US'], use_isolating=False)
        self.ctx.add_messages(dedent_ftl("""
            -thing = { $article ->
                  *[definite] the thing
                   [indefinite] a thing
            }
            thing-no-arg = { -thing }
            thing-no-arg-alt = { -thing() }
            thing-with-arg = { -thing(article: "indefinite") }
            thing-positional-arg = { -thing("foo") }
            thing-fallback = { -thing(article: "somethingelse") }
            bad-term = { -missing() }
        """))

    def test_argument_omitted(self):
        val, errs = self.ctx.format('thing-no-arg', {})
        self.assertEqual(val, 'the thing')
        self.assertEqual(errs, [])

    def test_argument_omitted_alt(self):
        val, errs = self.ctx.format('thing-no-arg-alt', {})
        self.assertEqual(val, 'the thing')
        self.assertEqual(errs, [])

    def test_with_argument(self):
        val, errs = self.ctx.format('thing-with-arg', {})
        self.assertEqual(val, 'a thing')
        self.assertEqual(errs, [])

    def test_positional_arg(self):
        val, errs = self.ctx.format('thing-positional-arg', {})
        self.assertEqual(val, 'the thing')
        self.assertEqual(errs, [FluentFormatError("Ignored positional arguments passed to term '-thing'")])

    def test_fallback(self):
        val, errs = self.ctx.format('thing-fallback', {})
        self.assertEqual(val, 'the thing')
        self.assertEqual(errs, [])

    def test_no_implicit_access_to_external_args(self):
        # The '-thing' term should not get passed article="indefinite"
        val, errs = self.ctx.format('thing-no-arg', {'article': 'indefinite'})
        self.assertEqual(val, 'the thing')
        self.assertEqual(errs, [])

    def test_bad_term(self):
        val, errs = self.ctx.format('bad-term', {})
        self.assertEqual(val, '-missing')
        self.assertEqual(errs, [FluentReferenceError('Unknown term: -missing')])


class TestParameterizedTermAttributes(unittest.TestCase):

    def setUp(self):
        self.ctx = FluentBundle(['en-US'], use_isolating=False)
        self.ctx.add_messages(dedent_ftl("""
            -brand = Cool Thing
                .status = { $version ->
                    [v2]     available
                   *[v1]     deprecated
                }

            attr-with-arg = { -brand } is { -brand.status(version: "v2") ->
                 [available]   available, yay!
                *[deprecated]  deprecated, sorry
            }

            -other = { $arg ->
                        [a]  ABC
                       *[d]  DEF
                     }

            missing-attr-ref = { -other.missing(arg: "a") ->
                 [ABC]  ABC option
                *[DEF]  DEF option
            }
        """))

    def test_with_argument(self):
        val, errs = self.ctx.format('attr-with-arg', {})
        self.assertEqual(val, 'Cool Thing is available, yay!')
        self.assertEqual(errs, [])

    def test_missing_attr(self):
        # We should fall back to the parent, and still pass the args.
        val, errs = self.ctx.format('missing-attr-ref', {})
        self.assertEqual(val, 'ABC option')
        self.assertEqual(errs, [FluentReferenceError('Unknown attribute: -other.missing')])


class TestNestedParameterizedTerms(unittest.TestCase):

    def setUp(self):
        self.ctx = FluentBundle(['en-US'], use_isolating=False)
        self.ctx.add_messages(dedent_ftl("""
            -thing = { $article ->
                *[definite] { $first-letter ->
                    *[lower] the thing
                     [upper] The thing
                 }
                 [indefinite] { $first-letter ->
                    *[lower] a thing
                     [upper] A thing
                 }
             }

            both-args = { -thing(first-letter: "upper", article: "indefinite") }.
            outer-arg = This is { -thing(article: "indefinite") }.
            inner-arg = { -thing(first-letter: "upper") }.
            neither-arg = { -thing() }.
        """))

    def test_both_args(self):
        val, errs = self.ctx.format('both-args', {})
        self.assertEqual(val, 'A thing.')
        self.assertEqual(errs, [])

    def test_outer_arg(self):
        val, errs = self.ctx.format('outer-arg', {})
        self.assertEqual(val, 'This is a thing.')
        self.assertEqual(errs, [])

    def test_inner_arg(self):
        val, errs = self.ctx.format('inner-arg', {})
        self.assertEqual(val, 'The thing.')
        self.assertEqual(errs, [])

    def test_neither_arg(self):
        val, errs = self.ctx.format('neither-arg', {})
        self.assertEqual(val, 'the thing.')
        self.assertEqual(errs, [])
