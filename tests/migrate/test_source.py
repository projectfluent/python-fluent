# coding=utf8
from __future__ import unicode_literals

import unittest

import fluent.syntax.ast as FTL

from fluent.migrate.errors import NotSupportedError
from fluent.migrate.transforms import Source, COPY, PLURALS, REPLACE
from fluent.migrate.helpers import EXTERNAL_ARGUMENT


class TestNotSupportedError(unittest.TestCase):
    def test_source(self):
        pattern = ('Migrating translations from Fluent files is not supported')
        with self.assertRaisesRegexp(NotSupportedError, pattern):
            Source('test.ftl', 'foo')

    def test_copy(self):
        pattern = ('Migrating translations from Fluent files is not supported')
        with self.assertRaisesRegexp(NotSupportedError, pattern):
            FTL.Message(
                FTL.Identifier('foo'),
                value=COPY('test.ftl', 'foo')
            )

    def test_plurals(self):
        pattern = ('Migrating translations from Fluent files is not supported')
        with self.assertRaisesRegexp(NotSupportedError, pattern):
            FTL.Message(
                FTL.Identifier('delete-all'),
                value=PLURALS(
                    'test.ftl',
                    'deleteAll',
                    EXTERNAL_ARGUMENT('num')
                )
            )

    def test_replace(self):
        pattern = ('Migrating translations from Fluent files is not supported')
        with self.assertRaisesRegexp(NotSupportedError, pattern):
            FTL.Message(
                FTL.Identifier(u'hello'),
                value=REPLACE(
                    'test.ftl',
                    'hello',
                    {
                        '#1': EXTERNAL_ARGUMENT('username')
                    }
                )
            )
