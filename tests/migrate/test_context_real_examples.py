# coding=utf8
from __future__ import unicode_literals

import os
import unittest

try:
    import compare_locales
except ImportError:
    compare_locales = None

import fluent.syntax.ast as FTL

from fluent.migrate.util import ftl_resource_to_json, to_json
from fluent.migrate.context import MergeContext
from fluent.migrate.helpers import EXTERNAL_ARGUMENT, MESSAGE_REFERENCE
from fluent.migrate.transforms import (
    CONCAT, COPY, PLURALS, REPLACE_IN_TEXT, REPLACE
)


def here(*parts):
    dirname = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(dirname, *parts)


@unittest.skipUnless(compare_locales, 'compare-locales requried')
class TestMergeAboutDownloads(unittest.TestCase):
    def setUp(self):
        self.ctx = MergeContext(
            lang='pl',
            reference_dir=here('fixtures/en-US'),
            localization_dir=here('fixtures/pl')
        )

        self.ctx.add_transforms('aboutDownloads.ftl', 'aboutDownloads.ftl', [
            FTL.Message(
                id=FTL.Identifier('title'),
                value=COPY(
                    'aboutDownloads.dtd',
                    'aboutDownloads.title'
                )
            ),
            FTL.Message(
                id=FTL.Identifier('header'),
                value=COPY(
                    'aboutDownloads.dtd',
                    'aboutDownloads.header'
                )
            ),
            FTL.Message(
                id=FTL.Identifier('empty'),
                value=COPY(
                    'aboutDownloads.dtd',
                    'aboutDownloads.empty'
                )
            ),
            FTL.Message(
                id=FTL.Identifier('open-menuitem'),
                attributes=[
                    FTL.Attribute(
                        FTL.Identifier('label'),
                        COPY(
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
                        COPY(
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
                        COPY(
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
                        COPY(
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
                        COPY(
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
                        COPY(
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
                        COPY(
                            'aboutDownloads.dtd',
                            'aboutDownloads.removeAll'
                        )
                    )
                ]
            ),
            FTL.Message(
                id=FTL.Identifier('delete-all-title'),
                value=COPY(
                    'aboutDownloads.properties',
                    'downloadAction.deleteAll'
                )
            ),
            FTL.Message(
                id=FTL.Identifier('delete-all-message'),
                value=PLURALS(
                    'aboutDownloads.properties',
                    'downloadMessage.deleteAll',
                    EXTERNAL_ARGUMENT('num'),
                    lambda text: REPLACE_IN_TEXT(
                        text,
                        {
                            '#1': EXTERNAL_ARGUMENT('num')
                        }
                    )
                )
            ),
            FTL.Message(
                id=FTL.Identifier('download-state-downloading'),
                value=COPY(
                    'aboutDownloads.properties',
                    'downloadState.downloading'
                )
            ),
            FTL.Message(
                id=FTL.Identifier('download-state-canceled'),
                value=COPY(
                    'aboutDownloads.properties',
                    'downloadState.canceled'
                )
            ),
            FTL.Message(
                id=FTL.Identifier('download-state-failed'),
                value=COPY(
                    'aboutDownloads.properties',
                    'downloadState.failed'
                )
            ),
            FTL.Message(
                id=FTL.Identifier('download-state-paused'),
                value=COPY(
                    'aboutDownloads.properties',
                    'downloadState.paused'
                )
            ),
            FTL.Message(
                id=FTL.Identifier('download-state-starting'),
                value=COPY(
                    'aboutDownloads.properties',
                    'downloadState.starting'
                )
            ),
            FTL.Message(
                id=FTL.Identifier('download-size-unknown'),
                value=COPY(
                    'aboutDownloads.properties',
                    'downloadState.unknownSize'
                )
            ),
        ])

    def test_merge_context_all_messages(self):
        expected = {
            'aboutDownloads.ftl': ftl_resource_to_json('''
        # This Source Code Form is subject to the terms of the Mozilla Public
        # License, v. 2.0. If a copy of the MPL was not distributed with this
        # file, You can obtain one at http://mozilla.org/MPL/2.0/.

        title  = Pobrane pliki
        header = Twoje pobrane pliki
        empty  = Brak pobranych plików

        open-menuitem =
            .label = Otwórz
        retry-menuitem =
            .label = Spróbuj ponownie
        remove-menuitem =
            .label = Usuń
        pause-menuitem =
            .label = Wstrzymaj
        resume-menuitem =
            .label = Wznów
        cancel-menuitem =
            .label = Anuluj
        remove-all-menuitem =
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
        # This Source Code Form is subject to the terms of the Mozilla Public
        # License, v. 2.0. If a copy of the MPL was not distributed with this
        # file, You can obtain one at http://mozilla.org/MPL/2.0/.

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


@unittest.skipUnless(compare_locales, 'compare-locales requried')
class TestMergeAboutDialog(unittest.TestCase):
    def setUp(self):
        self.ctx = MergeContext(
            lang='pl',
            reference_dir=here('fixtures/en-US'),
            localization_dir=here('fixtures/pl')
        )

        self.ctx.add_transforms('aboutDialog.ftl', 'aboutDialog.ftl', [
            FTL.Message(
                id=FTL.Identifier('update-failed'),
                value=CONCAT(
                    COPY('aboutDialog.dtd', 'update.failed.start'),
                    FTL.TextElement('<a>'),
                    COPY('aboutDialog.dtd', 'update.failed.linkText'),
                    FTL.TextElement('</a>'),
                    COPY('aboutDialog.dtd', 'update.failed.end'),
                )
            ),
            FTL.Message(
                id=FTL.Identifier('channel-desc'),
                value=CONCAT(
                    COPY(
                        'aboutDialog.dtd', 'channel.description.start'
                    ),
                    EXTERNAL_ARGUMENT('channelname'),
                    COPY('aboutDialog.dtd', 'channel.description.end'),
                )
            ),
            FTL.Message(
                id=FTL.Identifier('community'),
                value=CONCAT(
                    REPLACE(
                        'aboutDialog.dtd',
                        'community.start',
                        {
                            '&brandShortName;': MESSAGE_REFERENCE(
                                'brand-short-name'
                            )
                        }
                    ),
                    FTL.TextElement('<a>'),
                    REPLACE(
                        'aboutDialog.dtd',
                        'community.mozillaLink',
                        {
                            '&vendorBrandShortName;': MESSAGE_REFERENCE(
                                'vendor-short-name'
                            )
                        }
                    ),
                    FTL.TextElement('</a>'),
                    COPY('aboutDialog.dtd', 'community.middle'),
                    FTL.TextElement('<a>'),
                    COPY('aboutDialog.dtd', 'community.creditsLink'),
                    FTL.TextElement('</a>'),
                    COPY('aboutDialog.dtd', 'community.end')
                )
            ),
        ])

    @unittest.skip('Parser/Serializer trim whitespace')
    def test_merge_context_all_messages(self):
        expected = {
            'aboutDialog.ftl': ftl_resource_to_json('''
        # This Source Code Form is subject to the terms of the Mozilla Public
        # License, v. 2.0. If a copy of the MPL was not distributed with this
        # file, You can obtain one at http://mozilla.org/MPL/2.0/.

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
        # This Source Code Form is subject to the terms of the Mozilla Public
        # License, v. 2.0. If a copy of the MPL was not distributed with this
        # file, You can obtain one at http://mozilla.org/MPL/2.0/.

        update-failed = Aktualizacja się nie powiodła. <a>Pobierz</a>.
            ''')
        }

        self.assertDictEqual(
            to_json(self.ctx.merge_changeset(changeset)),
            expected
        )
