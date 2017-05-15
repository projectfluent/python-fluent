# coding=utf8
from __future__ import unicode_literals

import os
import unittest

import fluent.syntax.ast as FTL

from fluent.migrate.util import ftl_resource_to_json, to_json
from fluent.migrate.context import MergeContext
from fluent.migrate.transforms import (
    CONCAT, EXTERNAL, LITERAL, LITERAL_FROM, PLURALS_FROM, REPLACE,
    REPLACE_FROM
)


def here(*parts):
    dirname = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(dirname, *parts)


class TestMergeAboutDownloads(unittest.TestCase):
    def setUp(self):
        self.ctx = MergeContext(
            lang='pl',
            reference_dir=here('fixtures/en-US'),
            localization_dir=here('fixtures/pl')
        )

        self.ctx.add_reference('aboutDownloads.ftl')
        try:
            self.ctx.add_localization('aboutDownloads.dtd')
            self.ctx.add_localization('aboutDownloads.properties')
        except RuntimeError:
            self.skipTest('compare-locales required')

        self.ctx.add_transforms('aboutDownloads.ftl', [
            FTL.Message(
                id=FTL.Identifier('title'),
                value=LITERAL_FROM(
                    'aboutDownloads.dtd',
                    'aboutDownloads.title'
                )
            ),
            FTL.Message(
                id=FTL.Identifier('header'),
                value=LITERAL_FROM(
                    'aboutDownloads.dtd',
                    'aboutDownloads.header'
                )
            ),
            FTL.Message(
                id=FTL.Identifier('empty'),
                value=LITERAL_FROM(
                    'aboutDownloads.dtd',
                    'aboutDownloads.empty'
                )
            ),
            FTL.Message(
                id=FTL.Identifier('open-menuitem'),
                attributes=[
                    FTL.Attribute(
                        FTL.Identifier('label'),
                        LITERAL_FROM(
                            'aboutDownloads.dtd',
                            'aboutDownloads.open'
                        )
                    )
                ]
            ),
            FTL.Message(
                id=FTL.Identifier('retry-menuitem'),
                attributes=[
                    FTL.Attribute(
                        FTL.Identifier('label'),
                        LITERAL_FROM(
                            'aboutDownloads.dtd',
                            'aboutDownloads.retry'
                        )
                    )
                ]
            ),
            FTL.Message(
                id=FTL.Identifier('remove-menuitem'),
                attributes=[
                    FTL.Attribute(
                        FTL.Identifier('label'),
                        LITERAL_FROM(
                            'aboutDownloads.dtd',
                            'aboutDownloads.remove'
                        )
                    )
                ]
            ),
            FTL.Message(
                id=FTL.Identifier('pause-menuitem'),
                attributes=[
                    FTL.Attribute(
                        FTL.Identifier('label'),
                        LITERAL_FROM(
                            'aboutDownloads.dtd',
                            'aboutDownloads.pause'
                        )
                    )
                ]
            ),
            FTL.Message(
                id=FTL.Identifier('resume-menuitem'),
                attributes=[
                    FTL.Attribute(
                        FTL.Identifier('label'),
                        LITERAL_FROM(
                            'aboutDownloads.dtd',
                            'aboutDownloads.resume'
                        )
                    )
                ]
            ),
            FTL.Message(
                id=FTL.Identifier('cancel-menuitem'),
                attributes=[
                    FTL.Attribute(
                        FTL.Identifier('label'),
                        LITERAL_FROM(
                            'aboutDownloads.dtd',
                            'aboutDownloads.cancel'
                        )
                    )
                ]
            ),
            FTL.Message(
                id=FTL.Identifier('remove-all-menuitem'),
                attributes=[
                    FTL.Attribute(
                        FTL.Identifier('label'),
                        LITERAL_FROM(
                            'aboutDownloads.dtd',
                            'aboutDownloads.removeAll'
                        )
                    )
                ]
            ),
            FTL.Message(
                id=FTL.Identifier('delete-all-title'),
                value=LITERAL_FROM(
                    'aboutDownloads.properties',
                    'downloadAction.deleteAll'
                )
            ),
            FTL.Message(
                id=FTL.Identifier('delete-all-message'),
                value=PLURALS_FROM(
                    'aboutDownloads.properties',
                    'downloadMessage.deleteAll',
                    FTL.ExternalArgument(
                        id=FTL.Identifier('num')
                    ),
                    lambda var: REPLACE(
                        var,
                        {
                            '#1': FTL.ExternalArgument(
                                id=FTL.Identifier('num')
                            )
                        }
                    )
                )
            ),
            FTL.Message(
                id=FTL.Identifier('download-state-downloading'),
                value=LITERAL_FROM(
                    'aboutDownloads.properties',
                    'downloadState.downloading'
                )
            ),
            FTL.Message(
                id=FTL.Identifier('download-state-canceled'),
                value=LITERAL_FROM(
                    'aboutDownloads.properties',
                    'downloadState.canceled'
                )
            ),
            FTL.Message(
                id=FTL.Identifier('download-state-failed'),
                value=LITERAL_FROM(
                    'aboutDownloads.properties',
                    'downloadState.failed'
                )
            ),
            FTL.Message(
                id=FTL.Identifier('download-state-paused'),
                value=LITERAL_FROM(
                    'aboutDownloads.properties',
                    'downloadState.paused'
                )
            ),
            FTL.Message(
                id=FTL.Identifier('download-state-starting'),
                value=LITERAL_FROM(
                    'aboutDownloads.properties',
                    'downloadState.starting'
                )
            ),
            FTL.Message(
                id=FTL.Identifier('download-size-unknown'),
                value=LITERAL_FROM(
                    'aboutDownloads.properties',
                    'downloadState.unknownSize'
                )
            ),
        ])

    def test_merge_context_all_messages(self):
        expected = {
            'aboutDownloads.ftl': ftl_resource_to_json('''
        // This Source Code Form is subject to the terms of the Mozilla Public
        // License, v. 2.0. If a copy of the MPL was not distributed with this
        // file, You can obtain one at http://mozilla.org/MPL/2.0/.

        title  = Pobrane pliki
        header = Twoje pobrane pliki
        empty  = Brak pobranych plików

        open-menuitem
            .label = Otwórz
        retry-menuitem
            .label = Spróbuj ponownie
        remove-menuitem
            .label = Usuń
        pause-menuitem
            .label = Wstrzymaj
        resume-menuitem
            .label = Wznów
        cancel-menuitem
            .label = Anuluj
        remove-all-menuitem
            .label = Usuń wszystko

        delete-all-title   = Usuń wszystko
        delete-all-message =
            { $num ->
                [one] Usunąć pobrany plik?
                [few] Usunąć { $num } pobrane pliki?
               *[many] Usunąć { $num } pobranych plików?
            }

        download-state-downloading = Pobieranie…
        download-state-canceled = Anulowane
        download-state-failed = Nieudane
        download-state-paused = Wstrzymane
        download-state-starting = Rozpoczynanie…
        download-size-unknown = Nieznany rozmiar
            ''')
        }

        self.assertDictEqual(
            to_json(self.ctx.merge_changeset()),
            expected
        )

    def test_merge_context_some_messages(self):
        changeset = {
            ('aboutDownloads.dtd', 'aboutDownloads.title'),
            ('aboutDownloads.dtd', 'aboutDownloads.header'),
            ('aboutDownloads.properties', 'downloadState.downloading'),
            ('aboutDownloads.properties', 'downloadState.canceled'),
        }

        expected = {
            'aboutDownloads.ftl': ftl_resource_to_json('''
        // This Source Code Form is subject to the terms of the Mozilla Public
        // License, v. 2.0. If a copy of the MPL was not distributed with this
        // file, You can obtain one at http://mozilla.org/MPL/2.0/.

        title = Pobrane pliki
        header = Twoje pobrane pliki
        download-state-downloading = Pobieranie…
        download-state-canceled = Anulowane
            ''')
        }

        self.assertDictEqual(
            to_json(self.ctx.merge_changeset(changeset)),
            expected
        )


class TestMergeAboutDialog(unittest.TestCase):
    def setUp(self):
        self.ctx = MergeContext(
            lang='pl',
            reference_dir=here('fixtures/en-US'),
            localization_dir=here('fixtures/pl')
        )

        try:
            self.ctx.add_reference('aboutDialog.ftl')
            self.ctx.add_localization('aboutDialog.dtd')
        except RuntimeError:
            self.skipTest('compare-locales required')

        self.ctx.add_transforms('aboutDialog.ftl', [
            FTL.Message(
                id=FTL.Identifier('update-failed'),
                value=CONCAT(
                    LITERAL_FROM('aboutDialog.dtd', 'update.failed.start'),
                    LITERAL('<a>'),
                    LITERAL_FROM('aboutDialog.dtd', 'update.failed.linkText'),
                    LITERAL('</a>'),
                    LITERAL_FROM('aboutDialog.dtd', 'update.failed.end'),
                )
            ),
            FTL.Message(
                id=FTL.Identifier('channel-desc'),
                value=CONCAT(
                    LITERAL_FROM(
                        'aboutDialog.dtd', 'channel.description.start'
                    ),
                    EXTERNAL('channelname'),
                    LITERAL_FROM('aboutDialog.dtd', 'channel.description.end'),
                )
            ),
            FTL.Message(
                id=FTL.Identifier('community'),
                value=CONCAT(
                    REPLACE_FROM(
                        'aboutDialog.dtd',
                        'community.start',
                        {
                            '&brandShortName;': FTL.ExternalArgument(
                                id=FTL.Identifier('brand-short-name')
                            )
                        }
                    ),
                    LITERAL('<a>'),
                    REPLACE_FROM(
                        'aboutDialog.dtd',
                        'community.mozillaLink',
                        {
                            '&vendorBrandShortName;': FTL.ExternalArgument(
                                id=FTL.Identifier('vendor-short-name')
                            )
                        }
                    ),
                    LITERAL('</a>'),
                    LITERAL_FROM('aboutDialog.dtd', 'community.middle'),
                    LITERAL('<a>'),
                    LITERAL_FROM('aboutDialog.dtd', 'community.creditsLink'),
                    LITERAL('</a>'),
                    LITERAL_FROM('aboutDialog.dtd', 'community.end')
                )
            ),
        ])

    @unittest.skip('Parser/Serializer trim whitespace')
    def test_merge_context_all_messages(self):
        expected = {
            'aboutDialog.ftl': ftl_resource_to_json('''
        // This Source Code Form is subject to the terms of the Mozilla Public
        // License, v. 2.0. If a copy of the MPL was not distributed with this
        // file, You can obtain one at http://mozilla.org/MPL/2.0/.

        update-failed = Aktualizacja się nie powiodła. <a>Pobierz</a>.
        channel-desc = Obecnie korzystasz z kanału { $channelname }.
        community = Program { $brand-short-name } został opracowany przez <a>organizację { $vendor-short-name }</a>, która jest <a>globalną społecznością</a>, starającą się zapewnić, by…
            ''')
        }

        self.assertDictEqual(
            to_json(self.ctx.merge_changeset()),
            expected
        )

    def test_merge_context_some_messages(self):
        changeset = {
            ('aboutDialog.dtd', 'update.failed.start'),
        }

        expected = {
            'aboutDialog.ftl': ftl_resource_to_json('''
        // This Source Code Form is subject to the terms of the Mozilla Public
        // License, v. 2.0. If a copy of the MPL was not distributed with this
        // file, You can obtain one at http://mozilla.org/MPL/2.0/.

        update-failed = Aktualizacja się nie powiodła. <a>Pobierz</a>.
            ''')
        }

        self.assertDictEqual(
            to_json(self.ctx.merge_changeset(changeset)),
            expected
        )
