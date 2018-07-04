#!/usr/bin/env python

# This should be run using pytest
from __future__ import unicode_literals

import os
import subprocess
import sys
from gettext import translation

import pytest
import six

from fluent.context import CompilingMessageContext, InterpretingMessageContext

this_file = os.path.abspath(__file__)
this_dir = os.path.dirname(this_file)
locale_dir = os.path.join(this_dir, "locale")
messages_dir = os.path.join(locale_dir, "en", "LC_MESSAGES")
ftl_file = os.path.join(this_dir, "benchmark.ftl")


@pytest.fixture(scope="module")
def gettext_translations():
    pot_file = os.path.join(this_dir, "benchmark.pot")
    po_file = os.path.join(messages_dir, "benchmark.po")
    subprocess.check_call(["pybabel", "extract", "-o", pot_file, this_file])
    do_dummy_translation(pot_file, po_file)

    mo_file = os.path.join(messages_dir, "benchmark.mo")
    subprocess.check_call(["pybabel", "compile", "-f", "-i", po_file, "-o", mo_file])
    translation_obj = translation("benchmark", localedir=locale_dir, languages=['en'])
    return translation_obj


def do_dummy_translation(pot_file, po_file):
    # Copy and fill in some default translations
    with open(pot_file, "r") as f:
        contents = f.read()
    output = []
    for line in contents.split("\n"):
        if not line.startswith("msgstr "):
            output.append(line)
        if line.startswith("msgid \""):
            output.append(line.replace("msgid \"", "msgstr \"Translated "))
    with open(po_file, "w") as f:
        f.write("\n".join(output))


@pytest.fixture
def interpreting_message_context():
    return build_message_context(InterpretingMessageContext)


@pytest.fixture
def compiling_message_context():
    ctx = build_message_context(CompilingMessageContext)
    ctx._compile()
    return ctx


def build_message_context(cls):
    # We choose 'use_isolating=False' for feature parity with gettext
    ctx = cls(['en'], use_isolating=False)
    with open(ftl_file, "r") as f:
        ctx.add_messages(f.read())
    return ctx


def unicode_gettext_method(gettext_translations):
    if hasattr(gettext_translations, 'ugettext'):
        return gettext_translations.ugettext
    else:
        return gettext_translations.gettext


def test_single_string_gettext(gettext_translations, benchmark):
    gettext_translations.gettext("Hello I am a single string literal")  # for extract process
    result = benchmark(unicode_gettext_method(gettext_translations), "Hello I am a single string literal")
    assert result == "Translated Hello I am a single string literal"
    assert type(result) is six.text_type


def test_single_string_fluent_interpreter(interpreting_message_context, benchmark):
    result = benchmark(interpreting_message_context.format, 'single-string-literal')
    assert result[0] == "Translated Hello I am a single string literal"
    assert type(result[0]) is six.text_type


def test_single_string_fluent_compiler(compiling_message_context, benchmark):
    result = benchmark(compiling_message_context.format, 'single-string-literal')
    assert result[0] == "Translated Hello I am a single string literal"
    assert type(result[0]) is six.text_type


def test_single_interpolation_gettext(gettext_translations, benchmark):
    gettext_translations.gettext("Hello %(username)s, welcome to our website!")  # for extract process
    t = unicode_gettext_method(gettext_translations)
    args = {'username': 'Mary'}
    result = benchmark(lambda: t("Hello %(username)s, welcome to our website!") % args)
    assert result == "Translated Hello Mary, welcome to our website!"
    assert type(result) is six.text_type


def test_single_interpolation_fluent_interpreter(interpreting_message_context, benchmark):
    args = {'username': 'Mary'}
    result = benchmark(interpreting_message_context.format, 'single-interpolation', args)
    assert result[0] == "Translated Hello Mary, welcome to our website!"
    assert type(result[0]) is six.text_type


def test_single_interpolation_fluent_compiler(compiling_message_context, benchmark):
    args = {'username': 'Mary'}
    result = benchmark(compiling_message_context.format, 'single-interpolation', args)
    assert result[0] == "Translated Hello Mary, welcome to our website!"
    assert type(result[0]) is six.text_type


if __name__ == '__main__':
    subprocess.check_call(["py.test", "--benchmark-warmup=on", "--benchmark-sort=name", this_file] + sys.argv[1:])
