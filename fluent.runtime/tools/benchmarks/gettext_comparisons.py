#!/usr/bin/env python

# This should be run using pytest, see end of file
from __future__ import unicode_literals

import os
import subprocess
import sys
from gettext import translation

import pytest
import six

from fluent.runtime import CompilingFluentBundle, InterpretingFluentBundle

this_file = os.path.abspath(__file__)
this_dir = os.path.dirname(this_file)
locale_dir = os.path.join(this_dir, "locale")
messages_dir = os.path.join(locale_dir, "pl", "LC_MESSAGES")
FTL_MESSAGES = """
single-string-literal = Hello I am a single string literal in Polish

single-interpolation = Hello { $username }, welcome to our website! in Polish

# Don't include the count in the output, to test just the speed of the plural
# form lookup, rather than the locale aware number formatting routines.

plural-form-select = { $count ->
    [one] There is one thing, in Polish
    [few] There are few things, in Polish
    [many] There are many things, in Polish
   *[other] There are other things, in Polish
 }
"""


@pytest.fixture(scope="module")
def gettext_translations():
    pot_file = os.path.join(this_dir, "benchmark.pot")
    po_file = os.path.join(messages_dir, "benchmark.po")
    if not os.path.exists(messages_dir):
        os.makedirs(messages_dir)
    subprocess.check_call(["pybabel", "extract", "-o", pot_file, this_file])
    do_dummy_translation(pot_file, po_file)

    mo_file = os.path.join(messages_dir, "benchmark.mo")
    subprocess.check_call(["pybabel", "compile", "-f", "-i", po_file, "-o", mo_file])
    translation_obj = translation("benchmark", localedir=locale_dir, languages=['pl'])
    return translation_obj


dummy_gettext_plural_translations = {
    "There is %(count)d thing":
        ["There is one thing, in Polish",
         "There are few things, in Polish",
         "There are many things, in Polish",
         "There are other things, in Polish",
         ]
}


def do_dummy_translation(pot_file, po_file):
    # Copy and fill in some default translations
    with open(pot_file, "r") as f:
        contents = f.read()
    output = []
    last_id = None
    for line in contents.split("\n"):
        if line.startswith("msgid \""):
            last_id = line.replace("msgid ", "").strip('"')

        if line.startswith("msgstr "):
            # Generate 'translation':
            msgstr = 'msgstr "{0} in Polish"'.format(last_id)
            output.append(msgstr)
        elif line.startswith('msgstr[0]'):
            msgstrs = dummy_gettext_plural_translations[last_id]
            for i, msgstr in enumerate(msgstrs):
                output.append('''msgstr[{0}] "{1}"'''.format(i, msgstr))
        elif line.startswith('msgstr['):
            pass  # ignore, done these already
        else:
            output.append(line)

        if line.startswith('"Generated-By:'):
            # extra header stuff:
            output.append(r'''"Language: pl\n"''')
            output.append(r'''"Plural-Forms: nplurals=4; plural=(n==1 ? 0 : (n%10>=2 && n%10<=4) && (n%100<12 || n%100>=14) ? 1 : n!=1 && (n%10>=0 && n%10<=1) || (n%10>=5 && n%10<=9) || (n%100>=12 && n%100<=14) ? 2 : 3);\n"''')

    with open(po_file, "w") as f:
        f.write("\n".join(output))


@pytest.fixture
def interpreting_fluent_bundle():
    return build_fluent_bundle(InterpretingFluentBundle)


@pytest.fixture
def compiling_fluent_bundle():
    ctx = build_fluent_bundle(CompilingFluentBundle)
    ctx._compile()
    return ctx


def build_fluent_bundle(cls):
    # We choose 'use_isolating=False' for feature parity with gettext
    ctx = cls(['pl'], use_isolating=False)
    ctx.add_messages(FTL_MESSAGES)
    return ctx


def unicode_gettext_method(gettext_translations):
    if hasattr(gettext_translations, 'ugettext'):
        return gettext_translations.ugettext
    else:
        return gettext_translations.gettext


def unicode_ngettext_method(gettext_translations):
    if hasattr(gettext_translations, 'ungettext'):
        return gettext_translations.ungettext
    else:
        return gettext_translations.ngettext


def test_single_string_gettext(gettext_translations, benchmark):
    gettext_translations.gettext("Hello I am a single string literal")  # for extract process
    result = benchmark(unicode_gettext_method(gettext_translations), "Hello I am a single string literal")
    assert result == "Hello I am a single string literal in Polish"
    assert type(result) is six.text_type


def test_single_string_fluent_interpreter(interpreting_fluent_bundle, benchmark):
    result = benchmark(interpreting_fluent_bundle.format, 'single-string-literal')
    assert result[0] == "Hello I am a single string literal in Polish"
    assert type(result[0]) is six.text_type


def test_single_string_fluent_compiler(compiling_fluent_bundle, benchmark):
    result = benchmark(compiling_fluent_bundle.format, 'single-string-literal')
    assert result[0] == "Hello I am a single string literal in Polish"
    assert type(result[0]) is six.text_type


def test_single_interpolation_gettext(gettext_translations, benchmark):
    gettext_translations.gettext("Hello %(username)s, welcome to our website!")  # for extract process
    t = unicode_gettext_method(gettext_translations)
    args = {'username': 'Mary'}
    result = benchmark(lambda: t("Hello %(username)s, welcome to our website!") % args)
    assert result == "Hello Mary, welcome to our website! in Polish"
    assert type(result) is six.text_type


def test_single_interpolation_fluent_interpreter(interpreting_fluent_bundle, benchmark):
    args = {'username': 'Mary'}
    result = benchmark(interpreting_fluent_bundle.format, 'single-interpolation', args)
    assert result[0] == "Hello Mary, welcome to our website! in Polish"
    assert type(result[0]) is six.text_type


def test_single_interpolation_fluent_compiler(compiling_fluent_bundle, benchmark):
    args = {'username': 'Mary'}
    result = benchmark(compiling_fluent_bundle.format, 'single-interpolation', args)
    assert result[0] == "Hello Mary, welcome to our website! in Polish"
    assert type(result[0]) is six.text_type


def test_plural_form_select_gettext(gettext_translations, benchmark):
    gettext_translations.ngettext("There is %(count)d thing", "There are %(count)d things", 1)  # for extract process
    t = unicode_ngettext_method(gettext_translations)

    def f():
        for i in range(0, 10):
            t("There is %(count)d thing", "There are %(count)d things", i)

    benchmark(f)


def test_plural_form_select_fluent_compiler(compiling_fluent_bundle, benchmark):
    return _test_plural_form_select_fluent(compiling_fluent_bundle, benchmark)


def test_plural_form_select_fluent_interpreter(interpreting_fluent_bundle, benchmark):
    return _test_plural_form_select_fluent(interpreting_fluent_bundle, benchmark)


def _test_plural_form_select_fluent(ctx, benchmark):
    def f():
        for i in range(0, 10):
            ctx.format("plural-form-select", {'count': i})[0]

    benchmark(f)


if __name__ == '__main__':
    # You can execute this file directly, and optionally add more py.test args
    # to the command line (e.g. -k for keyword matching certain tests).
    subprocess.check_call(["py.test", "--benchmark-warmup=on", "--benchmark-sort=name", this_file] + sys.argv[1:])
