#!/usr/bin/env python
# This should be run using pytest

from __future__ import unicode_literals

import sys
import pytest

from fluent.runtime import FluentBundle, FluentResource


FTL_CONTENT = """
one = One
two = Two
three = Three
four = Four
five = Five
six = Six
seven = Seven ways to { $destination }
eight = Eight
nine = Nine
ten = Ten
"""


@pytest.fixture
def fluent_bundle():
    bundle = FluentBundle(['pl'], use_isolating=False)
    bundle.add_resource(FluentResource(FTL_CONTENT))
    return bundle


def fluent_template(bundle):
    return (
        "preface" +
        bundle.format_pattern(bundle.get_message('one').value)[0] +
        bundle.format_pattern(bundle.get_message('two').value)[0] +
        bundle.format_pattern(bundle.get_message('three').value)[0] +
        bundle.format_pattern(bundle.get_message('four').value)[0] +
        bundle.format_pattern(bundle.get_message('five').value)[0] +
        bundle.format_pattern(bundle.get_message('six').value)[0] +
        bundle.format_pattern(bundle.get_message('seven').value, {"destination": "Mars"})[0] +
        bundle.format_pattern(bundle.get_message('eight').value)[0] +
        bundle.format_pattern(bundle.get_message('nine').value)[0] +
        bundle.format_pattern(bundle.get_message('ten').value)[0] +
        "tail"
    )


class TestBenchmark(object):
    def test_template(self, fluent_bundle, benchmark):
        benchmark(lambda: fluent_template(fluent_bundle))

    def test_bundle(self, benchmark):
        def test_bundles():
            FluentBundle(['pl'], use_isolating=False)
            FluentBundle(['fr'], use_isolating=False)
        benchmark(test_bundles)

    def test_import(self, benchmark):
        def test_imports():
            # prune cached imports
            fluent_deps = [
                k for k in sys.modules.keys()
                if k.split('.', 1)[0] in ('babel', 'fluent', 'pytz')
            ]
            for k in fluent_deps:
                del sys.modules[k]
            from fluent.runtime import FluentBundle  # noqa
        benchmark(test_imports)
