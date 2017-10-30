# coding=utf8
from __future__ import unicode_literals

import os
import logging
import unittest

import fluent.syntax.ast as FTL

from fluent.migrate.errors import NotSupportedError, UnreadableReferenceError
from fluent.migrate.util import ftl, ftl_resource_to_json, to_json
from fluent.migrate.context import MergeContext
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

        try:
            self.ctx.maybe_add_localization('aboutDownloads.dtd')
            self.ctx.maybe_add_localization('aboutDownloads.properties')
        except RuntimeError:
            self.skipTest('compare-locales required')

    def test_hardcoded_node(self):
        self.ctx.add_transforms('aboutDownloads.ftl', 'aboutDownloads.ftl', [
            FTL.Message(
                id=FTL.Identifier('about'),
                value=FTL.Pattern([
                    FTL.TextElement('Hardcoded Value')
                ])
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
        self.ctx.add_transforms('aboutDownloads.ftl', 'aboutDownloads.ftl', [
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
        with self.assertRaises(UnreadableReferenceError):
            self.ctx.add_transforms('some.ftl', 'missing.ftl', [])


class TestIncompleteLocalization(unittest.TestCase):
    def setUp(self):
        # Silence all logging.
        logging.disable(logging.CRITICAL)

        self.ctx = MergeContext(
            lang='pl',
            reference_dir=here('fixtures/en-US'),
            localization_dir=here('fixtures/pl')
        )

        try:
            self.ctx.maybe_add_localization('browser.dtd')
        except RuntimeError:
            self.skipTest('compare-locales required')

        self.ctx.add_transforms('toolbar.ftl', 'toolbar.ftl', [
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


class TestExistingTarget(unittest.TestCase):
    def setUp(self):
        # Silence all logging.
        logging.disable(logging.CRITICAL)

        self.ctx = MergeContext(
            lang='pl',
            reference_dir=here('fixtures/en-US'),
            localization_dir=here('fixtures/pl')
        )

        try:
            self.ctx.maybe_add_localization('privacy.dtd')
        except RuntimeError:
            self.skipTest('compare-locales required')

    def tearDown(self):
        # Resume logging.
        logging.disable(logging.NOTSET)

    def test_existing_target_ftl_missing_string(self):
        self.ctx.add_transforms('privacy.ftl', 'privacy.ftl', [
            FTL.Message(
                id=FTL.Identifier('dnt-learn-more'),
                value=COPY(
                    'privacy.dtd',
                    'doNotTrack.learnMore.label'
                )
            ),
        ])

        expected = {
            'privacy.ftl': ftl_resource_to_json('''
        // This Source Code Form is subject to the terms of the Mozilla Public
        // License, v. 2.0. If a copy of the MPL was not distributed with this
        // file, You can obtain one at http://mozilla.org/MPL/2.0/.

        dnt-description = New Description in Polish
        dnt-learn-more = Więcej informacji
            ''')
        }

        self.maxDiff = None
        self.assertDictEqual(
            to_json(self.ctx.merge_changeset()),
            expected
        )

    def test_existing_target_ftl_existing_string(self):
        self.ctx.add_transforms('privacy.ftl', 'privacy.ftl', [
            FTL.Message(
                id=FTL.Identifier('dnt-description'),
                value=COPY(
                    'privacy.dtd',
                    'doNotTrack.description'
                )
            ),

            # Migrate an extra string to populate the iterator returned by
            # ctx.merge_changeset(). Otherwise it won't yield anything if the
            # merged contents are the same as the existing file.
            FTL.Message(
                id=FTL.Identifier('dnt-always'),
                value=COPY(
                    'privacy.dtd',
                    'doNotTrack.always.label'
                )
            ),
        ])

        expected = {
            'privacy.ftl': ftl_resource_to_json('''
        // This Source Code Form is subject to the terms of the Mozilla Public
        // License, v. 2.0. If a copy of the MPL was not distributed with this
        // file, You can obtain one at http://mozilla.org/MPL/2.0/.

        dnt-description = New Description in Polish
        dnt-always = Zawsze
            ''')
        }

        self.maxDiff = None
        self.assertDictEqual(
            to_json(self.ctx.merge_changeset()),
            expected
        )

    def test_existing_target_ftl_with_all_messages(self):
        self.ctx.add_transforms('privacy.ftl', 'privacy.ftl', [
            FTL.Message(
                id=FTL.Identifier('dnt-description'),
                value=COPY(
                    'privacy.dtd',
                    'doNotTrack.description'
                )
            ),
        ])

        # All migrated messages are already in the target FTL and the result of
        # merge_changeset is an empty iterator.
        self.assertDictEqual(
            to_json(self.ctx.merge_changeset()),
            {}
        )


class TestNotSupportedError(unittest.TestCase):
    def test_add_ftl(self):
        pattern = ('Migrating translations from Fluent files is not supported')
        with self.assertRaisesRegexp(NotSupportedError, pattern):
            ctx = MergeContext(
                lang='pl',
                reference_dir=here('fixtures/en-US'),
                localization_dir=here('fixtures/pl')
            )

            ctx.maybe_add_localization('privacy.ftl')
