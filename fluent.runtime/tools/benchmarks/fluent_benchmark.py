#!/usr/bin/env python
# This should be run using pytest

from __future__ import unicode_literals

import sys
import pytest
import six

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
        bundle.format("one")[0] +
        bundle.format("two")[0] +
        bundle.format("three")[0] +
        bundle.format("four")[0] +
        bundle.format("five")[0] +
        bundle.format("six")[0] +
        bundle.format("seven", {"destination": "Mars"})[0] +
        bundle.format("eight")[0] +
        bundle.format("nine")[0] +
        bundle.format("ten")[0] +
        "tail"
    )


class TestBenchmark(object):
    def test_template(self, fluent_bundle, benchmark):
        result = benchmark(lambda: fluent_template(fluent_bundle))

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
                if k.split('.', 1)[0] in ('babel','fluent','pytz')
            ]
            for k in fluent_deps:
                del sys.modules[k]
            from fluent.runtime import FluentBundle  # noqa
        benchmark(test_imports)
