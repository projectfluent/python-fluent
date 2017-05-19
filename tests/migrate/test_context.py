# coding=utf8
from __future__ import unicode_literals

import os
import logging
import unittest

import fluent.syntax.ast as FTL

from fluent.migrate.util import ftl, ftl_resource_to_json, to_json
from fluent.migrate.context import MergeContext
from fluent.migrate.helpers import LITERAL
from fluent.migrate.transforms import COPY


def here(*parts):
    dirname = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(dirname, *parts)


class TestMergeContext(unittest.TestCase):
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

    def test_hardcoded_node(self):
        self.ctx.add_transforms('aboutDownloads.ftl', [
            FTL.Message(
                id=FTL.Identifier('about'),
                value=LITERAL('Hardcoded Value')
            ),
        ])

        expected = {
            'aboutDownloads.ftl': ftl_resource_to_json('''
        // This Source Code Form is subject to the terms of the Mozilla Public
        // License, v. 2.0. If a copy of the MPL was not distributed with this
        // file, You can obtain one at http://mozilla.org/MPL/2.0/.

        about = Hardcoded Value
            ''')
        }

        self.assertDictEqual(
            to_json(self.ctx.merge_changeset()),
            expected
        )

    def test_merge_single_message(self):
        self.ctx.add_transforms('aboutDownloads.ftl', [
            FTL.Message(
                id=FTL.Identifier('title'),
                value=COPY(
                    'aboutDownloads.dtd',
                    'aboutDownloads.title'
                )
            ),
        ])

        expected = {
            'aboutDownloads.ftl': ftl_resource_to_json('''
        // This Source Code Form is subject to the terms of the Mozilla Public
        // License, v. 2.0. If a copy of the MPL was not distributed with this
        // file, You can obtain one at http://mozilla.org/MPL/2.0/.

        title = Pobrane pliki
            ''')
        }

        self.assertDictEqual(
            to_json(self.ctx.merge_changeset()),
            expected
        )

    def test_merge_one_changeset(self):
        self.ctx.add_transforms('aboutDownloads.ftl', [
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
        ])

        changeset = {
            ('aboutDownloads.dtd', 'aboutDownloads.title'),
            ('aboutDownloads.dtd', 'aboutDownloads.header')
        }

        expected = {
            'aboutDownloads.ftl': ftl_resource_to_json('''
        // This Source Code Form is subject to the terms of the Mozilla Public
        // License, v. 2.0. If a copy of the MPL was not distributed with this
        // file, You can obtain one at http://mozilla.org/MPL/2.0/.

        title = Pobrane pliki
        header = Twoje pobrane pliki
            ''')
        }

        self.assertDictEqual(
            to_json(self.ctx.merge_changeset(changeset)),
            expected
        )

    def test_merge_two_changesets(self):
        self.ctx.add_transforms('aboutDownloads.ftl', [
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
        ])

        changeset_a = {
            ('aboutDownloads.dtd', 'aboutDownloads.title'),
        }

        changeset_b = {
            ('aboutDownloads.dtd', 'aboutDownloads.header')
        }

        expected_a = {
            'aboutDownloads.ftl': ftl_resource_to_json('''
        // This Source Code Form is subject to the terms of the Mozilla Public
        // License, v. 2.0. If a copy of the MPL was not distributed with this
        // file, You can obtain one at http://mozilla.org/MPL/2.0/.

        title = Pobrane pliki
            ''')
        }

        expected_b = {
            'aboutDownloads.ftl': ftl_resource_to_json('''
        // This Source Code Form is subject to the terms of the Mozilla Public
        // License, v. 2.0. If a copy of the MPL was not distributed with this
        // file, You can obtain one at http://mozilla.org/MPL/2.0/.

        title = Pobrane pliki
        header = Twoje pobrane pliki
            ''')
        }

        merged_a = to_json(self.ctx.merge_changeset(changeset_a))
        self.assertDictEqual(merged_a, expected_a)

        merged_b = to_json(self.ctx.merge_changeset(changeset_b))
        self.assertDictEqual(merged_b, expected_b)

    def test_serialize_changeset(self):
        self.ctx.add_transforms('aboutDownloads.ftl', [
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
        ])

        changesets = [
            {
                ('aboutDownloads.dtd', 'aboutDownloads.title'),
            },
            {
                ('aboutDownloads.dtd', 'aboutDownloads.header')
            }
        ]

        expected = iter([
            {
                'aboutDownloads.ftl': ftl('''
        // This Source Code Form is subject to the terms of the Mozilla Public
        // License, v. 2.0. If a copy of the MPL was not distributed with this
        // file, You can obtain one at http://mozilla.org/MPL/2.0/.

        title = Pobrane pliki
                ''')
            },
            {
                'aboutDownloads.ftl': ftl('''
        // This Source Code Form is subject to the terms of the Mozilla Public
        // License, v. 2.0. If a copy of the MPL was not distributed with this
        // file, You can obtain one at http://mozilla.org/MPL/2.0/.

        title = Pobrane pliki
        header = Twoje pobrane pliki
                ''')
            }
        ])

        for changeset in changesets:
            serialized = self.ctx.serialize_changeset(changeset)
            self.assertEqual(serialized, next(expected))


class TestIncompleteReference(unittest.TestCase):
    def setUp(self):
        # Silence all logging.
        logging.disable(logging.CRITICAL)

        self.ctx = MergeContext(
            lang='pl',
            reference_dir=here('fixtures/en-US'),
            localization_dir=here('fixtures/pl')
        )

    def tearDown(self):
        # Resume logging.
        logging.disable(logging.NOTSET)

    def test_missing_reference_file(self):
        with self.assertRaises(IOError):
            self.ctx.add_reference('missing.ftl')


class TestIncompleteLocalization(unittest.TestCase):
    def setUp(self):
        # Silence all logging.
        logging.disable(logging.CRITICAL)

        self.ctx = MergeContext(
            lang='pl',
            reference_dir=here('fixtures/en-US'),
            localization_dir=here('fixtures/pl')
        )

        self.ctx.add_reference('toolbar.ftl')
        try:
            self.ctx.add_localization('browser.dtd')
        except RuntimeError:
            self.skipTest('compare-locales required')

        self.ctx.add_transforms('toolbar.ftl', [
            FTL.Message(
                id=FTL.Identifier('urlbar-textbox'),
                attributes=[
                    FTL.Attribute(
                        id=FTL.Identifier('placeholder'),
                        value=COPY(
                            'browser.dtd',
                            'urlbar.placeholder2'
                        )
                    ),
                    FTL.Attribute(
                        id=FTL.Identifier('accesskey'),
                        value=COPY(
                            'browser.dtd',
                            'urlbar.accesskey'
                        )
                    ),
                ]
            ),
        ])

    def tearDown(self):
        # Resume logging.
        logging.disable(logging.NOTSET)

    def test_missing_localization_file(self):
        expected = {
            'toolbar.ftl': ftl_resource_to_json('''
        // This Source Code Form is subject to the terms of the Mozilla Public
        // License, v. 2.0. If a copy of the MPL was not distributed with this
        // file, You can obtain one at http://mozilla.org/MPL/2.0/.


        [[ Toolbar items ]]
            ''')
        }

        self.maxDiff = None
        self.assertDictEqual(
            to_json(self.ctx.merge_changeset()),
            expected
        )
