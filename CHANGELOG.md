# Changelog

## Unreleased

  - Add BaseNode.equals for deep-equality testing.

    Nodes are deeply compared on a field by field basis. If possible, False is
    returned early. When comparing attributes, tags and variants in
    SelectExpressions, the order doesn't matter. By default, spans are not
    taken into account.  Other fields may also be ignored if necessary:

        message1.equals(message2, ignored_fields=['comment', 'span'])

## fluent 0.4.0 (June 13th, 2017)

  - This is the first release to be listed in the CHANGELOG.
