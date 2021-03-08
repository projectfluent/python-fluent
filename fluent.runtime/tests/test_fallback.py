import unittest
from unittest import mock
import io
import os

from fluent.runtime import (
    FluentLocalization,
    FluentResourceLoader,
)


ISFILE = os.path.isfile


class TestLocalization(unittest.TestCase):
    def test_init(self):
        l10n = FluentLocalization(
            ['en'], ['file.ftl'], FluentResourceLoader('{locale}')
        )
        self.assertTrue(callable(l10n.format_value))

    @mock.patch('os.path.isfile')
    @mock.patch('codecs.open')
    def test_bundles(self, codecs_open, isfile):
        data = {
            'de/one.ftl': 'one = in German',
            'de/two.ftl': 'two = in German',
            'fr/two.ftl': 'three = in French',
            'en/one.ftl': 'four = exists',
            'en/two.ftl': 'five = exists',
        }
        isfile.side_effect = lambda p: p in data or ISFILE(p)
        codecs_open.side_effect = lambda p, _, __: io.StringIO(data[p])
        l10n = FluentLocalization(
            ['de', 'fr', 'en'],
            ['one.ftl', 'two.ftl'],
            FluentResourceLoader('{locale}')
        )
        bundles_gen = l10n._bundles()
        bundle_de = next(bundles_gen)
        self.assertEqual(bundle_de.locales[0], 'de')
        self.assertTrue(bundle_de.has_message('one'))
        self.assertTrue(bundle_de.has_message('two'))
        bundle_fr = next(bundles_gen)
        self.assertEqual(bundle_fr.locales[0], 'fr')
        self.assertFalse(bundle_fr.has_message('one'))
        self.assertTrue(bundle_fr.has_message('three'))
        self.assertListEqual(list(l10n._bundles())[:2], [bundle_de, bundle_fr])
        bundle_en = next(bundles_gen)
        self.assertEqual(bundle_en.locales[0], 'en')
        self.assertEqual(l10n.format_value('one'), 'in German')
        self.assertEqual(l10n.format_value('two'), 'in German')
        self.assertEqual(l10n.format_value('three'), 'in French')
        self.assertEqual(l10n.format_value('four'), 'exists')
        self.assertEqual(l10n.format_value('five'), 'exists')


@mock.patch('os.path.isfile')
@mock.patch('codecs.open')
class TestResourceLoader(unittest.TestCase):
    def test_all_exist(self, codecs_open, isfile):
        data = {
            'en/one.ftl': 'one = exists',
            'en/two.ftl': 'two = exists',
        }
        isfile.side_effect = lambda p: p in data
        codecs_open.side_effect = lambda p, _, __: io.StringIO(data[p])
        loader = FluentResourceLoader('{locale}')
        resources_list = list(loader.resources('en', ['one.ftl', 'two.ftl']))
        self.assertEqual(len(resources_list), 1)
        resources = resources_list[0]
        self.assertEqual(len(resources), 2)

    def test_one_exists(self, codecs_open, isfile):
        data = {
            'en/two.ftl': 'two = exists',
        }
        isfile.side_effect = lambda p: p in data
        codecs_open.side_effect = lambda p, _, __: io.StringIO(data[p])
        loader = FluentResourceLoader('{locale}')
        resources_list = list(loader.resources('en', ['one.ftl', 'two.ftl']))
        self.assertEqual(len(resources_list), 1)
        resources = resources_list[0]
        self.assertEqual(len(resources), 1)

    def test_none_exist(self, codecs_open, isfile):
        data = {}
        isfile.side_effect = lambda p: p in data
        codecs_open.side_effect = lambda p, _, __: io.StringIO(data[p])
        loader = FluentResourceLoader('{locale}')
        resources_list = list(loader.resources('en', ['one.ftl', 'two.ftl']))
        self.assertEqual(len(resources_list), 0)
