# Changelog

## fluent 0.6.1 (February 6, 2018)

Various fixes to `fluent.migrate` for [bug 1424682][].

[bug 1424682]: https://bugzilla.mozilla.org/show_bug.cgi?id=1424682

  - Accept `Patterns` and `PatternElements` in `REPLACE`. (#41)

    `REPLACE` can now use `Patterns`, `PatternElements` and `Expressions` as
    replacement values. This makes `REPLACE` accept the same Transforms as
    `CONCAT`.

  - Never migrate partial translations. (#44)

    Partial translations may break the AST because they produce
    `TextElements` with `None` values. For now, we explicitly skip any
    transforms which depend on at least one missing legacy string to avoid
    serialization errors.

  - Warn about unknown FTL entries in transforms. (#40)
  - Fix how files are passed to `hg annotate`. (#39)

## fluent 0.6.0 (January 31, 2018)

  - Implement Fluent Syntax 0.5.

    - Add support for terms.
    - Add support for `#`, `##` and `###` comments.
    - Remove support for tags.
    - Add support for `=` after the identifier in message and term
      defintions.
    - Forbid newlines in string expressions.
    - Allow trailing comma in call expression argument lists.

    In fluent-syntax 0.6.x the new Syntax 0.5 is supported alongside the old
    Syntax 0.4. This should make migrations easier.

    `FluentParser` will correctly parse Syntax 0.4 comments (prefixed with
    `//`), sections and message definitions without the `=` after the
    identifier. The one exception are tags which are no longer supported.
    Please use attributed defined on terms instead.

    `FluentSerializer` always serializes using the new Syntax 0.5.

  - Expose `FluentSerializer.serializeExpression`. (#134)

  - Fix Bug 1428000 - Migrate: only annotate affected files (#34)


## fluent 0.4.4 (November 29, 2017)

  - Run Structure and Behavior tests in Python 3 (#22)
  - Bug 1411943 - Fix Blame for Mercurial 4.3+ (#23)
  - Bug 1412808 - Remove the LITERAL helper. (#25)
  - Bug 1321279 - Read target FTL files before migrations. (#24)

    The reference file for the transforms must now be passed as the second
    argument to add_transforms.

  - Bug 1318960 - Migrate files only when their messages change (#26)
  - Bug 1366298 - Skip SelectExpression in PLURALS for one plural category (#27)
  - Bug 1321290 - Migrate HTML entities to Unicode characters (#28)
  - Bug 1420225 - Read legacy files when scanning for Sources in transforms (#30)

    MergeContext.maybe_add_localization is now automaatically called
    interally when the context encounters a transforms which is a subclass of
    Source.


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
