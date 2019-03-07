from __future__ import absolute_import, unicode_literals

import operator
import unittest

import six
from markupsafe import Markup, escape
from bs4 import BeautifulSoup
from markdown import markdown

from .. import all_fluent_bundle_implementations
from ..utils import dedent_ftl

if six.PY3:
    from functools import reduce


# An escaper for MarkupSafe with instrumentation so we can check behaviour
class HtmlEscaper(object):
    name = 'HtmlEscaper'
    output_type = Markup
    use_isolating = False

    def __init__(self, test_case):
        self.test_case = test_case

    def select(self, message_id=None, **hints):
        return message_id.endswith('-html')

    def mark_escaped(self, escaped):
        self.test_case.assertEqual(type(escaped), six.text_type)
        return Markup(escaped)

    def escape(self, unescaped):
        return escape(unescaped)

    def join(self, parts):
        for p in parts:
            self.test_case.assertEqual(type(p), Markup)
        return Markup('').join(parts)


# A very basic Markdown 'escaper'. The main point of this implementation is
# that, unlike HtmlEscaper above, the output type is not a subclass of
# str/unicode, in order to test the implementation handles this properly.

# We also test whether the implementation can handle subclasses
class Markdown(object):
    def __init__(self, text):
        if isinstance(text, Markdown):
            self.text = text.text
        else:
            self.text = text

    def __eq__(self, other):
        return isinstance(other, Markdown) and self.text == other.text

    def __add__(self, other):
        assert isinstance(other, Markdown)
        return Markdown(self.text + other.text)

    def __repr__(self):
        return 'Markdown({0})'.format(repr(self.text))


class LiteralMarkdown(Markdown):
    pass


class StrippedMarkdown(Markdown):
    def __init__(self, text):
        if isinstance(text, StrippedMarkdown):
            self.text = text.text
        else:
            super(StrippedMarkdown, self).__init__(text)
            self.text = BeautifulSoup(markdown(self.text), "html.parser").get_text()


empty_markdown = Markdown('')


class MarkdownEscaper(object):
    name = 'MarkdownEscaper'
    output_type = Markdown
    use_isolating = True

    def __init__(self, test_case):
        self.test_case = test_case

    def select(self, message_id=None, **hints):
        return message_id.endswith('-md')

    def mark_escaped(self, escaped):
        self.test_case.assertEqual(type(escaped), six.text_type)
        return LiteralMarkdown(escaped)

    def escape(self, unescaped):
        # We don't do escaping, just stripping
        if isinstance(unescaped, Markdown):
            return unescaped
        return StrippedMarkdown(unescaped)

    def join(self, parts):
        for p in parts:
            self.test_case.assertTrue(isinstance(p, Markdown))
        return reduce(operator.add, parts, empty_markdown)


@all_fluent_bundle_implementations
class TestHtmlEscaping(unittest.TestCase):
    def setUp(self):
        escaper = HtmlEscaper(self)

        # A function that outputs '> ' that needs to be escaped. Part of the
        # point of this is to ensure that escaping is being done at the correct
        # point - it is no good to escape string input when it enters, it has to
        # be done at the end of the formatting process.
        def QUOTE(arg):
            return "\n" + "\n".join("> {0}".format(l) for l in arg.split("\n"))

        self.ctx = self.fluent_bundle_cls(['en-US'], use_isolating=True,
                                          functions={'QUOTE': QUOTE},
                                          escapers=[escaper])

        self.ctx.add_messages(dedent_ftl("""
            not-html-message = x < y

            simple-html =  This is <b>great</b>.

            argument-html = This <b>thing</b> is called { $arg }.

            -term-html = <b>Jack &amp; Jill</b>

            -term-plain = Jack & Jill

            references-html-term-html = { -term-html } are <b>great!</b>

            references-plain-term-html = { -term-plain } are <b>great!</b>

            references-html-term-plain = { -term-html } are great!

            attribute-argument-html = A <a href="{ $url }">link to { $place }</a>

            compound-message-html = A message about { $arg }. { argument-html }

            function-html = You said: { QUOTE($text) }

            parent-plain = Some stuff
                 .attr-html = Some <b>HTML</b> stuff
                 .attr-plain = This & That

            references-html-message-plain = Plain. { simple-html }

            references-html-message-attr-plain = Plain. { parent-plain.attr-html }

            references-html-message-attr-html = <b>HTML</b>. { parent-plain.attr-html }

            references-plain-message-attr-html = <b>HTML</b>. { parent-plain.attr-plain }

            -brand-plain = {
                 [short] A&B
                *[long]  A & B
             }

            -brand-html = {
                 [superscript] CoolBrand<sup>2</sup>
                *[normal]      CoolBrand2
             }

            references-html-variant-plain = { -brand-html[superscript] } is cool

            references-html-variant-html = { -brand-html[superscript] } is cool

            references-plain-variant-plain = { -brand-plain[short] } is awesome

            references-plain-variant-html = { -brand-plain[short] } is awesome
        """))

    def assertTypeAndValueEqual(self, val1, val2):
        self.assertEqual(val1, val2)
        self.assertEqual(type(val1), type(val2))

    def test_select_false(self):
        val, errs = self.ctx.format('not-html-message')
        self.assertTypeAndValueEqual(val, 'x < y')

    def test_simple(self):
        val, errs = self.ctx.format('simple-html')
        self.assertTypeAndValueEqual(val, Markup('This is <b>great</b>.'))
        self.assertEqual(errs, [])

    def test_argument_is_escaped(self):
        val, errs = self.ctx.format('argument-html', {'arg': 'Jack & Jill'})
        self.assertTypeAndValueEqual(val, Markup('This <b>thing</b> is called Jack &amp; Jill.'))
        self.assertEqual(errs, [])

    def test_argument_already_escaped(self):
        val, errs = self.ctx.format('argument-html', {'arg': Markup('<b>Jack</b>')})
        self.assertTypeAndValueEqual(val, Markup('This <b>thing</b> is called <b>Jack</b>.'))
        self.assertEqual(errs, [])

    def test_included_html_term(self):
        val, errs = self.ctx.format('references-html-term-html')
        self.assertTypeAndValueEqual(val, Markup('<b>Jack &amp; Jill</b> are <b>great!</b>'))
        self.assertEqual(errs, [])

    def test_included_plain_term(self):
        val, errs = self.ctx.format('references-plain-term-html')
        self.assertTypeAndValueEqual(val, Markup('Jack &amp; Jill are <b>great!</b>'))
        self.assertEqual(errs, [])

    def test_included_html_term_from_plain(self):
        val, errs = self.ctx.format('references-html-term-plain')
        self.assertTypeAndValueEqual(val, "\u2068-term-html\u2069 are great!")
        self.assertEqual(type(errs[0]), TypeError)

    def test_compound_message(self):
        val, errs = self.ctx.format('compound-message-html', {'arg': 'Jack & Jill'})
        self.assertTypeAndValueEqual(val, Markup('A message about Jack &amp; Jill. '
                                                 'This <b>thing</b> is called Jack &amp; Jill.'))
        self.assertEqual(errs, [])

    def test_function(self):
        val, errs = self.ctx.format('function-html', {'text': 'Jack & Jill'})
        self.assertTypeAndValueEqual(val, Markup('You said: \n&gt; Jack &amp; Jill'))
        self.assertEqual(errs, [])

    def test_plain_parent(self):
        val, errs = self.ctx.format('parent-plain')
        self.assertTypeAndValueEqual(val, 'Some stuff')
        self.assertEqual(errs, [])

    def test_html_attribute(self):
        val, errs = self.ctx.format('parent-plain.attr-html')
        self.assertTypeAndValueEqual(val, Markup("Some <b>HTML</b> stuff"))
        self.assertEqual(errs, [])

    def test_html_message_reference_from_plain(self):
        val, errs = self.ctx.format('references-html-message-plain')
        self.assertTypeAndValueEqual(val, "Plain. \u2068simple-html\u2069")
        self.assertEqual(len(errs), 1)
        self.assertEqual(type(errs[0]), TypeError)

    # Message attr references
    def test_html_message_attr_reference_from_plain(self):
        val, errs = self.ctx.format('references-html-message-attr-plain')
        self.assertTypeAndValueEqual(val, "Plain. \u2068parent-plain.attr-html\u2069")
        self.assertEqual(len(errs), 1)
        self.assertEqual(type(errs[0]), TypeError)

    def test_html_message_attr_reference_from_html(self):
        val, errs = self.ctx.format('references-html-message-attr-html')
        self.assertTypeAndValueEqual(val, Markup("<b>HTML</b>. Some <b>HTML</b> stuff"))
        self.assertEqual(errs, [])

    def test_plain_message_attr_reference_from_html(self):
        val, errs = self.ctx.format('references-plain-message-attr-html')
        self.assertTypeAndValueEqual(val, Markup("<b>HTML</b>. This &amp; That"))
        self.assertEqual(errs, [])

    # Term variant references
    def test_html_variant_from_plain(self):
        val, errs = self.ctx.format('references-html-variant-plain')
        self.assertTypeAndValueEqual(val, "\u2068-brand-html\u2069 is cool")
        self.assertEqual(len(errs), 1)
        self.assertEqual(type(errs[0]), TypeError)

    def test_html_variant_from_html(self):
        val, errs = self.ctx.format('references-html-variant-html')
        self.assertTypeAndValueEqual(val, Markup("CoolBrand<sup>2</sup> is cool"))
        self.assertEqual(errs, [])

    def test_plain_variant_from_plain(self):
        val, errs = self.ctx.format('references-plain-variant-plain')
        self.assertTypeAndValueEqual(val, "\u2068A&B\u2069 is awesome")
        self.assertEqual(errs, [])

    def test_plain_variant_from_html(self):
        val, errs = self.ctx.format('references-plain-variant-html')
        self.assertTypeAndValueEqual(val, Markup("A&amp;B is awesome"))
        self.assertEqual(errs, [])


@all_fluent_bundle_implementations
class TestMarkdownEscaping(unittest.TestCase):
    maxDiff = None

    def setUp(self):
        escaper = MarkdownEscaper(self)

        # This QUOTE function outputs Markdown that should not be removed.
        def QUOTE(arg):
            return Markdown("\n" + "\n".join("> {0}".format(l) for l in arg.split("\n")))

        self.ctx = self.fluent_bundle_cls(['en-US'], use_isolating=True,
                                          functions={'QUOTE': QUOTE},
                                          escapers=[escaper])

        self.ctx.add_messages(dedent_ftl("""
            not-md-message = **some text**

            simple-md =  This is **great**

            argument-md = This **thing** is called { $arg }.

            -term-md = **Jack** & __Jill__

            -term-plain = **Jack & Jill**

            term-md-ref-md = { -term-md } are **great!**

            term-plain-ref-md = { -term-plain } are **great!**

            embedded-argument-md = A [link to { $place }]({ $url })

            compound-message-md = A message about { $arg }. { argument-md }

            function-md = You said: { QUOTE($text) }

            parent-plain = Some stuff
                 .attr-md = Some **Markdown** stuff
                 .attr-plain = This and **That**

            references-md-message-plain = Plain. { simple-md }

            references-md-attr-plain = Plain. { parent-plain.attr-md }

            references-md-attr-md = **Markdown**. { parent-plain.attr-md }

            references-plain-attr-md = **Markdown**. { parent-plain.attr-plain }

            -brand-plain = {
                 [short] *A&B*
                *[long]  *A & B*
             }

            -brand-md = {
                 [bolded]  CoolBrand **2**
                *[normal]  CoolBrand2
             }

            references-md-variant-plain = { -brand-md[bolded] } is cool

            references-md-variant-md = { -brand-md[bolded] } is cool

            references-plain-variant-plain = { -brand-plain[short] } is awesome

            references-plain-variant-md = { -brand-plain[short] } is awesome
        """))

    def test_strip_markdown(self):
        self.assertEqual(StrippedMarkdown('**Some bolded** and __italic__ text'),
                         Markdown('Some bolded and italic text'))
        self.assertEqual(StrippedMarkdown("""

> A quotation
> about something
        """),
                         Markdown('\nA quotation\nabout something\n'))

    def test_select_false(self):
        val, errs = self.ctx.format('not-md-message')
        self.assertEqual(val, '**some text**')

    def test_simple(self):
        val, errs = self.ctx.format('simple-md')
        self.assertEqual(val, Markdown('This is **great**'))
        self.assertEqual(errs, [])

    def test_argument_is_escaped(self):
        val, errs = self.ctx.format('argument-md', {'arg': '**Jack**'})
        self.assertEqual(val, Markdown('This **thing** is called \u2068Jack\u2069.'))
        self.assertEqual(errs, [])

    def test_argument_already_escaped(self):
        val, errs = self.ctx.format('argument-md', {'arg': Markdown('**Jack**')})
        self.assertEqual(val, Markdown('This **thing** is called \u2068**Jack**\u2069.'))
        self.assertEqual(errs, [])

    def test_included_md(self):
        val, errs = self.ctx.format('term-md-ref-md')
        self.assertEqual(val, Markdown('\u2068**Jack** & __Jill__\u2069 are **great!**'))
        self.assertEqual(errs, [])

    def test_included_plain(self):
        val, errs = self.ctx.format('term-plain-ref-md')
        self.assertEqual(val, Markdown('\u2068Jack & Jill\u2069 are **great!**'))
        self.assertEqual(errs, [])

    def test_compound_message(self):
        val, errs = self.ctx.format('compound-message-md', {'arg': '**Jack & Jill**'})
        self.assertEqual(val, Markdown('A message about \u2068Jack & Jill\u2069. '
                                       '\u2068This **thing** is called \u2068Jack & Jill\u2069.\u2069'))
        self.assertEqual(errs, [])

    def test_function(self):
        val, errs = self.ctx.format('function-md', {'text': 'Jack & Jill'})
        self.assertEqual(val, Markdown('You said: \u2068\n> Jack & Jill\u2069'))
        self.assertEqual(errs, [])

    def test_plain_parent(self):
        val, errs = self.ctx.format('parent-plain')
        self.assertEqual(val, 'Some stuff')
        self.assertEqual(errs, [])

    def test_md_attribute(self):
        val, errs = self.ctx.format('parent-plain.attr-md')
        self.assertEqual(val, Markdown("Some **Markdown** stuff"))
        self.assertEqual(errs, [])

    def test_md_message_reference_from_plain(self):
        val, errs = self.ctx.format('references-md-message-plain')
        self.assertEqual(val, "Plain. \u2068simple-md\u2069")
        self.assertEqual(len(errs), 1)
        self.assertEqual(type(errs[0]), TypeError)

    def test_md_attr_reference_from_plain(self):
        val, errs = self.ctx.format('references-md-attr-plain')
        self.assertEqual(val, "Plain. \u2068parent-plain.attr-md\u2069")
        self.assertEqual(len(errs), 1)
        self.assertEqual(type(errs[0]), TypeError)

    def test_md_reference_from_md(self):
        val, errs = self.ctx.format('references-md-attr-md')
        self.assertEqual(val, Markdown("**Markdown**. \u2068Some **Markdown** stuff\u2069"))
        self.assertEqual(errs, [])

    def test_plain_reference_from_md(self):
        val, errs = self.ctx.format('references-plain-attr-md')
        self.assertEqual(val, Markdown("**Markdown**. \u2068This and That\u2069"))
        self.assertEqual(errs, [])

    def test_md_variant_from_plain(self):
        val, errs = self.ctx.format('references-md-variant-plain')
        self.assertEqual(val, "\u2068-brand-md\u2069 is cool")
        self.assertEqual(len(errs), 1)
        self.assertEqual(type(errs[0]), TypeError)

    def test_md_variant_from_md(self):
        val, errs = self.ctx.format('references-md-variant-md')
        self.assertEqual(val, Markdown("\u2068CoolBrand **2**\u2069 is cool"))
        self.assertEqual(errs, [])

    def test_plain_variant_from_plain(self):
        val, errs = self.ctx.format('references-plain-variant-plain')
        self.assertEqual(val, "\u2068*A&B*\u2069 is awesome")
        self.assertEqual(errs, [])

    def test_plain_variant_from_md(self):
        val, errs = self.ctx.format('references-plain-variant-md')
        self.assertEqual(val, Markdown("\u2068A&B\u2069 is awesome"))
        self.assertEqual(errs, [])
