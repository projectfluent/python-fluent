import unittest
from .utils import patch_files

from fluent.runtime import FluentLocalization, FluentResourceLoader


class TestLocalization(unittest.TestCase):
    def test_init(self):
        l10n = FluentLocalization(
            ["en"], ["file.ftl"], FluentResourceLoader("{locale}")
        )
        self.assertTrue(callable(l10n.format_value))

    @patch_files({
        "de/one.ftl": """one = in German
            .foo = one in German
        """,
        "de/two.ftl": """two = in German
            .foo = two in German
        """,
        "fr/two.ftl": """three = in French
            .foo = three in French
        """,
        "en/one.ftl": """four = exists
            .foo = four in English
        """,
        "en/two.ftl": """
five = exists
    .foo = five in English
bar =
    .foo = bar in English
baz = baz in English
        """,
    })
    def test_bundles(self):
        l10n = FluentLocalization(
            ["de", "fr", "en"], ["one.ftl", "two.ftl"], FluentResourceLoader("{locale}")
        )
        bundles_gen = l10n._bundles()
        bundle_de = next(bundles_gen)
        self.assertEqual(bundle_de.locales[0], "de")
        self.assertTrue(bundle_de.has_message("one"))
        self.assertTrue(bundle_de.has_message("two"))
        bundle_fr = next(bundles_gen)
        self.assertEqual(bundle_fr.locales[0], "fr")
        self.assertFalse(bundle_fr.has_message("one"))
        self.assertTrue(bundle_fr.has_message("three"))
        self.assertListEqual(list(l10n._bundles())[:2], [bundle_de, bundle_fr])
        bundle_en = next(bundles_gen)
        self.assertEqual(bundle_en.locales[0], "en")
        self.assertEqual(l10n.format_value("one"), "in German")
        self.assertEqual(l10n.format_value("two"), "in German")
        self.assertEqual(l10n.format_value("three"), "in French")
        self.assertEqual(l10n.format_value("four"), "exists")
        self.assertEqual(l10n.format_value("five"), "exists")
        self.assertEqual(l10n.format_value("bar"), "bar")
        self.assertEqual(l10n.format_value("baz"), "baz in English")
        self.assertEqual(l10n.format_value("not-exists"), "not-exists")
        self.assertEqual(
            tuple(l10n.format_message("one")),
            ("in German", {"foo": "one in German"}),
        )
        self.assertEqual(
            tuple(l10n.format_message("two")),
            ("in German", {"foo": "two in German"}),
        )
        self.assertEqual(
            tuple(l10n.format_message("three")),
            ("in French", {"foo": "three in French"}),
        )
        self.assertEqual(
            tuple(l10n.format_message("four")),
            ("exists", {"foo": "four in English"}),
        )
        self.assertEqual(
            tuple(l10n.format_message("five")),
            ("exists", {"foo": "five in English"}),
        )
        self.assertEqual(
            tuple(l10n.format_message("bar")),
            (None, {"foo": "bar in English"}),
        )
        self.assertEqual(
            tuple(l10n.format_message("baz")),
            ("baz in English", {}),
        )
        self.assertEqual(
            tuple(l10n.format_message("not-exists")),
            ("not-exists", {}),
        )


class TestResourceLoader(unittest.TestCase):
    @patch_files({
        "en/one.ftl": "one = exists",
        "en/two.ftl": "two = exists",
    })
    def test_all_exist(self):
        loader = FluentResourceLoader("{locale}")
        resources_list = list(loader.resources("en", ["one.ftl", "two.ftl"]))
        self.assertEqual(len(resources_list), 1)
        resources = resources_list[0]
        self.assertEqual(len(resources), 2)

    @patch_files({
        "en/two.ftl": "two = exists",
    })
    def test_one_exists(self):
        loader = FluentResourceLoader("{locale}")
        resources_list = list(loader.resources("en", ["one.ftl", "two.ftl"]))
        self.assertEqual(len(resources_list), 1)
        resources = resources_list[0]
        self.assertEqual(len(resources), 1)

    @patch_files({})
    def test_none_exist(self):
        loader = FluentResourceLoader("{locale}")
        resources_list = list(loader.resources("en", ["one.ftl", "two.ftl"]))
        self.assertEqual(len(resources_list), 0)
