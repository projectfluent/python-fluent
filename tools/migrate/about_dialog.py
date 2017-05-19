# coding=utf8

import fluent.syntax.ast as FTL
from fluent.migrate import (
    CONCAT, LITERAL, EXTERNAL_ARGUMENT, MESSAGE_REFERENCE, COPY,
    REPLACE
)


def migrate(ctx):
    """Migrate about:dialog, part {index}"""

    ctx.add_reference('browser/aboutDialog.ftl', realpath='aboutDialog.ftl')
    ctx.add_localization('browser/chrome/browser/aboutDialog.dtd')

    ctx.add_transforms('browser/aboutDialog.ftl', [
        FTL.Message(
            id=FTL.Identifier('update-failed'),
            value=CONCAT(
                COPY(
                    'browser/chrome/browser/aboutDialog.dtd',
                    'update.failed.start'
                ),
                LITERAL('<a>'),
                COPY(
                    'browser/chrome/browser/aboutDialog.dtd',
                    'update.failed.linkText'
                ),
                LITERAL('</a>'),
                COPY(
                    'browser/chrome/browser/aboutDialog.dtd',
                    'update.failed.end'
                )
            )
        ),
        FTL.Message(
            id=FTL.Identifier('channel-desc'),
            value=CONCAT(
                COPY(
                    'browser/chrome/browser/aboutDialog.dtd',
                    'channel.description.start'
                ),
                EXTERNAL_ARGUMENT('channelname'),
                COPY(
                    'browser/chrome/browser/aboutDialog.dtd',
                    'channel.description.end'
                )
            )
        ),
        FTL.Message(
            id=FTL.Identifier('community'),
            value=CONCAT(
                REPLACE(
                    'browser/chrome/browser/aboutDialog.dtd',
                    'community.start2',
                    {
                        '&brandShortName;': MESSAGE_REFERENCE(
                            'brand-short-name'
                        )
                    }
                ),
                LITERAL('<a>'),
                REPLACE(
                    'browser/chrome/browser/aboutDialog.dtd',
                    'community.mozillaLink',
                    {
                        '&vendorShortName;': MESSAGE_REFERENCE(
                            'vendor-short-name'
                        )
                    }
                ),
                LITERAL('</a>'),
                COPY(
                    'browser/chrome/browser/aboutDialog.dtd',
                    'community.middle2'
                ),
                LITERAL('<a>'),
                COPY(
                    'browser/chrome/browser/aboutDialog.dtd',
                    'community.creditsLink'
                ),
                LITERAL('</a>'),
                COPY(
                    'browser/chrome/browser/aboutDialog.dtd',
                    'community.end3'
                )
            )
        ),
    ])
