# coding=utf8

import fluent.syntax.ast as FTL
from fluent.migrate import CONCAT, EXTERNAL, LITERAL, LITERAL_FROM, REPLACE_FROM


def migrate(ctx):
    """Migrate about:dialog, part {index}"""

    ctx.add_reference('browser/aboutDialog.ftl', realpath='aboutDialog.ftl')
    ctx.add_localization('browser/chrome/browser/aboutDialog.dtd')

    ctx.add_transforms('browser/aboutDialog.ftl', [
        FTL.Entity(
            id=FTL.Identifier('update-failed'),
            value=CONCAT(
                LITERAL_FROM(
                    'browser/chrome/browser/aboutDialog.dtd',
                    'update.failed.start'
                ),
                LITERAL('<a>'),
                LITERAL_FROM(
                    'browser/chrome/browser/aboutDialog.dtd',
                    'update.failed.linkText'
                ),
                LITERAL('</a>'),
                LITERAL_FROM(
                    'browser/chrome/browser/aboutDialog.dtd',
                    'update.failed.end'
                )
            )
        ),
        FTL.Entity(
            id=FTL.Identifier('channel-desc'),
            value=CONCAT(
                LITERAL_FROM(
                    'browser/chrome/browser/aboutDialog.dtd',
                    'channel.description.start'
                ),
                EXTERNAL('channelname'),
                LITERAL_FROM(
                    'browser/chrome/browser/aboutDialog.dtd',
                    'channel.description.end'
                )
            )
        ),
        FTL.Entity(
            id=FTL.Identifier('community'),
            value=CONCAT(
                REPLACE_FROM(
                    'browser/chrome/browser/aboutDialog.dtd',
                    'community.start2',
                    {
                        '&brandShortName;': FTL.ExternalArgument(
                            id=FTL.Identifier('brand-short-name')
                        )
                    }
                ),
                LITERAL('<a>'),
                REPLACE_FROM(
                    'browser/chrome/browser/aboutDialog.dtd',
                    'community.mozillaLink',
                    {
                        '&vendorShortName;': FTL.ExternalArgument(
                            id=FTL.Identifier('vendor-short-name')
                        )
                    }
                ),
                LITERAL('</a>'),
                LITERAL_FROM(
                    'browser/chrome/browser/aboutDialog.dtd',
                    'community.middle2'
                ),
                LITERAL('<a>'),
                LITERAL_FROM(
                    'browser/chrome/browser/aboutDialog.dtd',
                    'community.creditsLink'
                ),
                LITERAL('</a>'),
                LITERAL_FROM(
                    'browser/chrome/browser/aboutDialog.dtd',
                    'community.end3'
                )
            )
        ),
    ])
