# coding=utf8
from __future__ import unicode_literals

import unittest
from compare_locales.parser import PropertiesParser, DTDParser

import fluent.syntax.ast as FTL
from fluent.syntax.parser import FluentParser
from fluent.migrate.util import parse, ftl, ftl_resource_to_json
from fluent.migrate.merge import merge_resource
from fluent.migrate.transforms import COPY


class MockContext(unittest.TestCase):
    def get_source(self, path, key):
        # Ignore path (test.properties) and get translations from
        # self.ab_cd_legacy defined in setUp.
        translation = self.ab_cd_legacy.get(key, None)

        if translation is not None:
            return translation.val


class TestMergeMessages(MockContext):
    maxDiff = None

    def setUp(self):
        self.en_us_ftl = parse(FluentParser, ftl('''
            title  = Downloads
            header = Your Downloads
            empty  = No Downloads
            about  = About Downloads

            open-menuitem =
                .label = Open

            download-state-downloading = Downloading…
        '''))

        self.ab_cd_ftl = parse(FluentParser, ftl('''
            empty = Brak pobranych plików
            about = Previously Hardcoded Value
        '''))

        ab_cd_dtd = parse(DTDParser, '''
            <!ENTITY aboutDownloads.title "Pobrane pliki">
            <!ENTITY aboutDownloads.open "Otwórz">
        ''')

        ab_cd_prop = parse(PropertiesParser, '''
            downloadState.downloading=Pobieranie…
        ''')

        self.ab_cd_legacy = {
            key: val
            for strings in (ab_cd_dtd, ab_cd_prop)
            for key, val in strings.items()
        }

        self.transforms = [
            FTL.Message(
                FTL.Identifier('title'),
                value=COPY('test.properties', 'aboutDownloads.title')
            ),
            FTL.Message(
                FTL.Identifier('about'),
                value=FTL.Pattern([
                    FTL.TextElement('Hardcoded Value')
                ])
            ),
            FTL.Message(
                FTL.Identifier('open-menuitem'),
                attributes=[
                    FTL.Attribute(
                        FTL.Identifier('label'),
                        COPY('test.properties', 'aboutDownloads.open')
                    ),
                ]
            ),
            FTL.Message(
                FTL.Identifier('download-state-downloading'),
                value=COPY('test.properties', 'downloadState.downloading')
            )
        ]

    def test_merge_two_way(self):
        resource = merge_resource(
            self, self.en_us_ftl, FTL.Resource(), self.transforms,
            in_changeset=lambda x: True
        )

        self.assertEqual(
            resource.to_json(),
            ftl_resource_to_json('''
                title = Pobrane pliki
                about = Hardcoded Value

                open-menuitem =
                    .label = Otwórz

                download-state-downloading = Pobieranie…
            ''')
        )

    def test_merge_three_way(self):
        resource = merge_resource(
            self, self.en_us_ftl, self.ab_cd_ftl, self.transforms,
            in_changeset=lambda x: True
        )

        self.assertEqual(
            resource.to_json(),
            ftl_resource_to_json('''
                title = Pobrane pliki
                empty = Brak pobranych plików
                about = Previously Hardcoded Value

                open-menuitem =
                    .label = Otwórz

                download-state-downloading = Pobieranie…
            ''')
        )


class TestMergeAllEntries(MockContext):
    def setUp(self):
        self.en_us_ftl = parse(FluentParser, ftl('''
            # This Source Code Form is subject to the terms of …

            ### A resource comment.

            title  = Downloads
            header = Your Downloads
            empty  = No Downloads

            ## Menu items

            # A message comment.
            open-menuitem =
                .label = Open

            download-state-downloading = Downloading…
        '''))

        self.ab_cd_ftl = parse(FluentParser, ftl('''
            # This Source Code Form is subject to the terms of …

            empty = Brak pobranych plików
        '''))

        ab_cd_dtd = parse(DTDParser, '''
            <!ENTITY aboutDownloads.title "Pobrane pliki">
            <!ENTITY aboutDownloads.open "Otwórz">
        ''')

        ab_cd_prop = parse(PropertiesParser, '''
            downloadState.downloading=Pobieranie…
        ''')

        self.ab_cd_legacy = {
            key: val
            for strings in (ab_cd_dtd, ab_cd_prop)
            for key, val in strings.items()
        }

        self.transforms = [
            FTL.Message(
                FTL.Identifier('title'),
                value=COPY('test.properties', 'aboutDownloads.title')
            ),
            FTL.Message(
                FTL.Identifier('open-menuitem'),
                attributes=[
                    FTL.Attribute(
                        FTL.Identifier('label'),
                        COPY('test.properties', 'aboutDownloads.open')
                    ),
                ]
            ),
            FTL.Message(
                FTL.Identifier('download-state-downloading'),
                value=COPY('test.properties', 'downloadState.downloading')
            )
        ]

    def test_merge_two_way(self):
        resource = merge_resource(
            self, self.en_us_ftl, FTL.Resource(), self.transforms,
            in_changeset=lambda x: True
        )

        self.assertEqual(
            resource.to_json(),
            ftl_resource_to_json('''
                # This Source Code Form is subject to the terms of …

                ### A resource comment.

                title = Pobrane pliki

                ## Menu items

                # A message comment.
                open-menuitem =
                    .label = Otwórz
                download-state-downloading = Pobieranie…

            ''')
        )

    def test_merge_three_way(self):
        resource = merge_resource(
            self, self.en_us_ftl, self.ab_cd_ftl, self.transforms,
            in_changeset=lambda x: True
        )

        self.assertEqual(
            resource.to_json(),
            ftl_resource_to_json('''
                # This Source Code Form is subject to the terms of …

                ### A resource comment.

                title = Pobrane pliki
                empty = Brak pobranych plików

                ## Menu items

                # A message comment.
                open-menuitem =
                    .label = Otwórz

                download-state-downloading = Pobieranie…

            ''')
        )


class TestMergeSubset(MockContext):
    def setUp(self):
        self.en_us_ftl = parse(FluentParser, ftl('''
            # This Source Code Form is subject to the terms of …

            ### A resource comment.

            title  = Downloads
            header = Your Downloads
            empty  = No Downloads

            ## Menu items

            # A message comment.
            open-menuitem =
                .label = Open

            download-state-downloading = Downloading…
        '''))

        ab_cd_dtd = parse(DTDParser, '''
            <!ENTITY aboutDownloads.title "Pobrane pliki">
            <!ENTITY aboutDownloads.open "Otwórz">
        ''')

        ab_cd_prop = parse(PropertiesParser, '''
            downloadState.downloading=Pobieranie…
        ''')

        self.ab_cd_legacy = {
            key: val
            for strings in (ab_cd_dtd, ab_cd_prop)
            for key, val in strings.items()
        }

        self.transforms = [
            FTL.Message(
                FTL.Identifier('title'),
                value=COPY('test.properties', 'aboutDownloads.title')
            ),
            FTL.Message(
                FTL.Identifier('download-state-downloading'),
                value=COPY('test.properties', 'downloadState.downloading')
            )
        ]

    def test_two_way_one_entity(self):
        subset = ('title',)
        resource = merge_resource(
            self, self.en_us_ftl, FTL.Resource(), self.transforms,
            in_changeset=lambda x: x in subset
        )

        self.assertEqual(
            resource.to_json(),
            ftl_resource_to_json('''
                # This Source Code Form is subject to the terms of …

                ### A resource comment.

                title = Pobrane pliki

                ## Menu items
            ''')
        )

    def test_two_way_two_entities(self):
        subset = ('title', 'download-state-downloading')
        resource = merge_resource(
            self, self.en_us_ftl, FTL.Resource(), self.transforms,
            in_changeset=lambda x: x in subset
        )

        self.assertEqual(
            resource.to_json(),
            ftl_resource_to_json('''
                # This Source Code Form is subject to the terms of …

                ### A resource comment.

                title = Pobrane pliki

                ## Menu items

                download-state-downloading = Pobieranie…
            ''')
        )

    def test_three_way_one_entity(self):
        ab_cd_ftl = parse(FluentParser, ftl('''
            # This Source Code Form is subject to the terms of …

            empty = Brak pobranych plików
        '''))

        subset = ('title',)
        resource = merge_resource(
            self, self.en_us_ftl, ab_cd_ftl, self.transforms,
            in_changeset=lambda x: x in subset
        )

        self.assertEqual(
            resource.to_json(),
            ftl_resource_to_json('''
                # This Source Code Form is subject to the terms of …

                ### A resource comment.

                title = Pobrane pliki
                empty = Brak pobranych plików

                ## Menu items
            ''')
        )

    def test_three_way_two_entities(self):
        ab_cd_ftl = parse(FluentParser, ftl('''
            # This Source Code Form is subject to the terms of …

            empty = Brak pobranych plików
        '''))

        subset = ('title', 'download-state-downloading')
        resource = merge_resource(
            self, self.en_us_ftl, ab_cd_ftl, self.transforms,
            in_changeset=lambda x: x in subset
        )

        self.assertEqual(
            resource.to_json(),
            ftl_resource_to_json('''
                # This Source Code Form is subject to the terms of …

                ### A resource comment.

                title = Pobrane pliki
                empty = Brak pobranych plików

                ## Menu items

                download-state-downloading = Pobieranie…
            ''')
        )

    def test_three_way_one_entity_existing_section(self):
        ab_cd_ftl = parse(FluentParser, ftl('''
            # This Source Code Form is subject to the terms of …

            empty = Brak pobranych plików

            ## Menu items

            # A message comment.
            open-menuitem =
                .label = Otwórz
        '''))

        subset = ('title',)
        resource = merge_resource(
            self, self.en_us_ftl, ab_cd_ftl, self.transforms,
            in_changeset=lambda x: x in subset
        )

        self.assertEqual(
            resource.to_json(),
            ftl_resource_to_json('''
                # This Source Code Form is subject to the terms of …

                ### A resource comment.

                title = Pobrane pliki
                empty = Brak pobranych plików

                ## Menu items

                # A message comment.
                open-menuitem =
                    .label = Otwórz
            ''')
        )

    def test_three_way_two_entities_existing_section(self):
        ab_cd_ftl = parse(FluentParser, ftl('''
            # This Source Code Form is subject to the terms of …

            empty = Brak pobranych plików

            ## Menu items

            # A message comment.
            open-menuitem =
                .label = Otwórz
        '''))

        subset = ('title', 'download-state-downloading')
        resource = merge_resource(
            self, self.en_us_ftl, ab_cd_ftl, self.transforms,
            in_changeset=lambda x: x in subset
        )

        self.assertEqual(
            resource.to_json(),
            ftl_resource_to_json('''
                # This Source Code Form is subject to the terms of …

                ### A resource comment.

                title = Pobrane pliki
                empty = Brak pobranych plików

                ## Menu items

                # A message comment.
                open-menuitem =
                    .label = Otwórz
                download-state-downloading = Pobieranie…
            ''')
        )
