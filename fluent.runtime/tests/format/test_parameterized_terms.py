import unittest

from fluent.runtime import FluentBundle, FluentResource
from fluent.runtime.errors import FluentFormatError, FluentReferenceError

from ..utils import dedent_ftl


class TestParameterizedTerms(unittest.TestCase):

    def setUp(self):
        self.bundle = FluentBundle(['en-US'], use_isolating=False)
        self.bundle.add_resource(FluentResource(dedent_ftl("""
            -thing = { $article ->
                  *[definite] the thing
                   [indefinite] a thing
                   [none] thing
            }
            thing-no-arg = { -thing }
            thing-no-arg-alt = { -thing() }
            thing-with-arg = { -thing(article: "indefinite") }
            thing-positional-arg = { -thing("foo") }
            thing-fallback = { -thing(article: "somethingelse") }
            bad-term = { -missing() }
        """)))

    def test_argument_omitted(self):
        val, errs = self.bundle.format_pattern(self.bundle.get_message('thing-no-arg').value, {})
        self.assertEqual(val, 'the thing')
        self.assertEqual(errs, [])

    def test_argument_omitted_alt(self):
        val, errs = self.bundle.format_pattern(self.bundle.get_message('thing-no-arg-alt').value, {})
        self.assertEqual(val, 'the thing')
        self.assertEqual(errs, [])

    def test_with_argument(self):
        val, errs = self.bundle.format_pattern(self.bundle.get_message('thing-with-arg').value, {})
        self.assertEqual(val, 'a thing')
        self.assertEqual(errs, [])

    def test_positional_arg(self):
        val, errs = self.bundle.format_pattern(self.bundle.get_message('thing-positional-arg').value, {})
        self.assertEqual(val, 'the thing')
        self.assertEqual(errs, [FluentFormatError("Ignored positional arguments passed to term '-thing'")])

    def test_fallback(self):
        val, errs = self.bundle.format_pattern(self.bundle.get_message('thing-fallback').value, {})
        self.assertEqual(val, 'the thing')
        self.assertEqual(errs, [])

    def test_no_implicit_access_to_external_args(self):
        # The '-thing' term should not get passed article="indefinite"
        val, errs = self.bundle.format_pattern(self.bundle.get_message('thing-no-arg').value, {'article': 'indefinite'})
        self.assertEqual(val, 'the thing')
        self.assertEqual(errs, [])

    def test_no_implicit_access_to_external_args_but_term_args_still_passed(self):
        val, errs = self.bundle.format_pattern(self.bundle.get_message('thing-with-arg').value, {'article': 'none'})
        self.assertEqual(val, 'a thing')
        self.assertEqual(errs, [])

    def test_bad_term(self):
        val, errs = self.bundle.format_pattern(self.bundle.get_message('bad-term').value, {})
        self.assertEqual(val, '{-missing}')
        self.assertEqual(errs, [FluentReferenceError('Unknown term: -missing')])


class TestParameterizedTermAttributes(unittest.TestCase):

    def setUp(self):
        self.bundle = FluentBundle(['en-US'], use_isolating=False)
        self.bundle.add_resource(FluentResource(dedent_ftl("""
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
        """)))

    def test_with_argument(self):
        val, errs = self.bundle.format_pattern(self.bundle.get_message('attr-with-arg').value, {})
        self.assertEqual(val, 'Cool Thing is available, yay!')
        self.assertEqual(errs, [])

    def test_missing_attr(self):
        # We don't fall back from attributes, get default.
        val, errs = self.bundle.format_pattern(self.bundle.get_message('missing-attr-ref').value, {})
        self.assertEqual(val, 'DEF option')
        self.assertEqual(errs, [FluentReferenceError('Unknown attribute: -other.missing')])


class TestNestedParameterizedTerms(unittest.TestCase):

    def setUp(self):
        self.bundle = FluentBundle(['en-US'], use_isolating=False)
        self.bundle.add_resource(FluentResource(dedent_ftl("""
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
        """)))

    def test_both_args(self):
        val, errs = self.bundle.format_pattern(self.bundle.get_message('both-args').value, {})
        self.assertEqual(val, 'A thing.')
        self.assertEqual(errs, [])

    def test_outer_arg(self):
        val, errs = self.bundle.format_pattern(self.bundle.get_message('outer-arg').value, {})
        self.assertEqual(val, 'This is a thing.')
        self.assertEqual(errs, [])

    def test_inner_arg(self):
        val, errs = self.bundle.format_pattern(self.bundle.get_message('inner-arg').value, {})
        self.assertEqual(val, 'The thing.')
        self.assertEqual(errs, [])

    def test_inner_arg_with_external_args(self):
        val, errs = self.bundle.format_pattern(self.bundle.get_message('inner-arg').value, {'article': 'indefinite'})
        self.assertEqual(val, 'The thing.')
        self.assertEqual(errs, [])

    def test_neither_arg(self):
        val, errs = self.bundle.format_pattern(self.bundle.get_message('neither-arg').value, {})
        self.assertEqual(val, 'the thing.')
        self.assertEqual(errs, [])


class TestTermsCalledFromTerms(unittest.TestCase):

    def setUp(self):
        self.bundle = FluentBundle(['en-US'], use_isolating=False)
        self.bundle.add_resource(FluentResource(dedent_ftl("""
            -foo = {$a} {$b}
            -bar = {-foo(b: 2)}
            -baz = {-foo}
            ref-bar = {-bar(a: 1)}
            ref-baz = {-baz(a: 1)}
        """)))

    def test_term_args_isolated_with_call_syntax(self):
        val, errs = self.bundle.format_pattern(self.bundle.get_message('ref-bar').value, {})
        self.assertEqual(val, 'a 2')
        self.assertEqual(errs, [])

    def test_term_args_isolated_without_call_syntax(self):
        val, errs = self.bundle.format_pattern(self.bundle.get_message('ref-baz').value, {})
        self.assertEqual(val, 'a b')
        self.assertEqual(errs, [])


class TestMessagesCalledFromTerms(unittest.TestCase):

    def setUp(self):
        self.bundle = FluentBundle(['en-US'], use_isolating=False)
        self.bundle.add_resource(FluentResource(dedent_ftl("""
            msg = Msg is {$arg}
            -foo = {msg}
            ref-foo = {-foo(arg: 1)}
        """)))

    def test_messages_inherit_term_args(self):
        # This behaviour may change in future, message calls might be
        # disallowed from inside terms
        val, errs = self.bundle.format_pattern(self.bundle.get_message('ref-foo').value, {'arg': 2})
        self.assertEqual(val, 'Msg is 1')
        self.assertEqual(errs, [])
