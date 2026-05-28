from os.path import join

from fluent.runtime import FluentLocalization, FluentResourceLoader

from .utils import build_file_tree


class TestLocalization:
    def test_init(self):
        l10n = FluentLocalization(
            ["en"], ["file.ftl"], FluentResourceLoader("{locale}")
        )
        assert callable(l10n.format_value)

    def test_bundles(self, tmp_path):
        build_file_tree(
            tmp_path,
            {
                "de": {
                    "one.ftl": "one = in German\n  .foo = one in German\n",
                    "two.ftl": "two = in German\n  .foo = two in German\n",
                },
                "fr": {"two.ftl": "three = in French\n  .foo = three in French\n"},
                "en": {
                    "one.ftl": "four = exists\n  .foo = four in English\n",
                    "two.ftl": "five = exists\n  .foo = five in English\n"
                    + "bar =\n  .foo = bar in English\n"
                    + "baz = baz in English\n",
                },
            },
        )
        l10n = FluentLocalization(
            ["de", "fr", "en"],
            ["one.ftl", "two.ftl"],
            FluentResourceLoader(join(tmp_path, "{locale}")),
        )
        bundles_gen = l10n._bundles()
        bundle_de = next(bundles_gen)
        assert bundle_de.locales[0] == "de"
        assert bundle_de.has_message("one")
        assert bundle_de.has_message("two")
        bundle_fr = next(bundles_gen)
        assert bundle_fr.locales[0] == "fr"
        assert not bundle_fr.has_message("one")
        assert bundle_fr.has_message("three")
        assert list(l10n._bundles())[:2] == [bundle_de, bundle_fr]
        bundle_en = next(bundles_gen)
        assert bundle_en.locales[0] == "en"
        assert l10n.format_value("one") == "in German"
        assert l10n.format_value("two") == "in German"
        assert l10n.format_value("three") == "in French"
        assert l10n.format_value("four") == "exists"
        assert l10n.format_value("five") == "exists"
        assert l10n.format_value("bar") == "bar"
        assert l10n.format_value("baz") == "baz in English"
        assert l10n.format_value("not-exists") == "not-exists"
        assert tuple(l10n.format_message("one")) == (
            "in German",
            {"foo": "one in German"},
        )
        assert tuple(l10n.format_message("two")) == (
            "in German",
            {"foo": "two in German"},
        )
        assert tuple(l10n.format_message("three")) == (
            "in French",
            {"foo": "three in French"},
        )
        assert tuple(l10n.format_message("four")) == (
            "exists",
            {"foo": "four in English"},
        )
        assert tuple(l10n.format_message("five")) == (
            "exists",
            {"foo": "five in English"},
        )
        assert tuple(l10n.format_message("bar")) == (None, {"foo": "bar in English"})
        assert tuple(l10n.format_message("baz")) == ("baz in English", {})
        assert tuple(l10n.format_message("not-exists")) == ("not-exists", {})


class TestResourceLoader:
    def test_all_exist(self, tmp_path):
        build_file_tree(
            tmp_path,
            {
                "en": {
                    "one.ftl": "one = exists",
                    "two.ftl": "two = exists",
                }
            },
        )
        loader = FluentResourceLoader(join(tmp_path, "{locale}"))
        resources_list = list(loader.resources("en", ["one.ftl", "two.ftl"]))
        assert len(resources_list) == 1
        resources = resources_list[0]
        assert len(resources) == 2

    def test_one_exists(self, tmp_path):
        build_file_tree(tmp_path, {"en": {"two.ftl": "two = exists"}})
        loader = FluentResourceLoader(join(tmp_path, "{locale}"))
        resources_list = list(loader.resources("en", ["one.ftl", "two.ftl"]))
        assert len(resources_list) == 1
        resources = resources_list[0]
        assert len(resources) == 1

    def test_none_exist(self, tmp_path):
        loader = FluentResourceLoader(join(tmp_path, "{locale}"))
        resources_list = list(loader.resources("en", ["one.ftl", "two.ftl"]))
        assert len(resources_list) == 0
