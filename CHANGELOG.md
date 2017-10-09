# Changelog

## Unreleased

  - …

## fluent 0.4.3 (October 9, 2017)

  - Bug 1397234 - Allow blank lines before attributes, tags and multiline patterns
  - Bug 1406342 - Trim trailing newline in Comment and Section spans


## fluent 0.4.2 (September 11, 2017)

  - Add an intermediate Placeable node for Expressions within Patterns.

    This allows storing more precise information about the whitespace around
    the placeable's braces.

    See https://github.com/projectfluent/fluent/pull/52.

  - Serializer: Add newlines around standalone comments.

## fluent 0.4.1 (June 27, 2017)

  - Add BaseNode.equals for deep-equality testing.

    Nodes are deeply compared on a field by field basis. If possible, False is
    returned early. When comparing attributes, tags and variants in
    SelectExpressions, the order doesn't matter. By default, spans are not
    taken into account.  Other fields may also be ignored if necessary:

        message1.equals(message2, ignored_fields=['comment', 'span'])

## fluent 0.4.0 (June 13, 2017)

  - This is the first release to be listed in the CHANGELOG.
