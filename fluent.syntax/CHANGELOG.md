# Changelog

## fluent.syntax 0.15.0 (April 17, 2019)

  - Support Fluent Syntax 1.0.

    Fluent Syntax 1.0 has been published today. There are no changes to the
    grammar nor the AST compared to the Syntax 0.9.

## fluent.syntax 0.14.0 (March 26, 2019)

This release of `fluent.syntax` brings support for version 0.9 of the Fluent
Syntax spec. The API remains unchanged. Files written in valid Syntax 0.8 may
parse differently in this release. See the compatibility note below. Consult
the full Syntax 0.9 [changelog][chlog0.9] for details.

[chlog0.9]: https://github.com/projectfluent/fluent/releases/tag/v0.9.0

  - Flatten complex reference expressions.

    Reference expressions which may take complex forms, such as a reference
    to a message's attribute, or a parameterized reference to an attribute of
    a term, are now stored in a simplified manner. Instead of nesting
    multiple expression nodes (e.g. `CallExpression` of an
    `AttributeExpression` of a `TermReference`), all information is available
    directly in the reference expression.

    This change affects the following AST nodes:

    -  `MessageReference` now has an optional `attribute` field,
    - `FunctionReference` now has a required `arguments` field,
    - `TermReference` now has an optional `attribute` field and an optional
      `arguments` field.

  - Remove `VariantLists`.

    The `VariantLists` and the `VariantExpression` syntax and AST nodes were
    deprecated in Syntax 0.9 and have now been removed.

  - Rename `StringLiteral.raw` to `value`.

    `StringLiteral.value` contains the exact contents of the string literal,
    character-for-character. Escape sequences are stored verbatim without
    processing. A new method, `Literal.parse`, can be used to process the raw
    value of the literal into an unescaped form.

  - Rename `args` to `arguments`.

    The `args` field of `MessageReference`, `TermReference`,
    `FunctionReference`, and `Annotation` has been renamed to `arguments`.


## fluent.syntax 0.13.0 (March 25, 2019)

- Make `BaseNode.equals` stricter when comparing lists.

  Starting from this version, `BaseNode.equals` now takes the order of
  variants and attributes into account when comparing two nodes.

- Remove `FluentSerializer.serialize_expression`.

  The stateless equivalent can still be imported from `fluent.syntax.serializer`:

  ```python
  from fluent.syntax.serializer import serialize_expression
  ```

## fluent.syntax 0.12.0 (February 15, 2019)

- Fixes to the `Visitor` API

  The `Visitor` API introduced in 0.11 was changed to align more with
  what Python's `ast.Visitor` does. This also allows implementations
  to have code after descending into child nodes.


## fluent.syntax 0.11.0 (February 13, 2019)

- API enhancements

  There are two new APIs in `fluent.syntax.ast`, `Visitor` and `Transformer`.
  Use these APIs for read-only iteration over AST trees, and in-place mutation
  of AST trees, respectively. There's also a new method `BaseNode.clone`,
  which can be used to create a deep copy of an AST node.

- DEPRECATIONS

  The API `BaseNode.traverse` is deprecated and will be removed in a future
  release. Please adjust your code to the `Visitor` or `Transformer` APIs.

## fluent.syntax 0.10.0 (January 15, 2019)

The `fluent` package which used to provide the `fluent.syntax` module has been
renamed to `fluent.syntax` on PyPI. The code is identical to `fluent` 0.10.

## fluent-syntax 0.10.0 (December 13, 2018)

This release brings support for version 0.8 of the Fluent Syntax spec. The API
remains unchanged. Files written in valid Syntax 0.7 may not parse correctly in
this release. See the summary of backwards-incompatible changes below.

  - Implement Fluent Syntax 0.8. (#303)

    This is only a quick summary of the spec changes in Syntax 0.8. Consult the
    full [changelog][chlog0.8] for details.

    [chlog0.8]: https://github.com/projectfluent/fluent/releases/tag/v0.8.0

    In multiline `Patterns`, all common indent is now removed from each
    indented line in the final value of the pattern.

    ```properties
    multiline =
        This message has 2 spaces of indent
          on the second line of its value.
    ```

    `Terms` can now be parameterized via the call expression syntax.

    ```properties
    # A parametrized Term with a Pattern as a value.
    -thing = { $article ->
       *[definite] the thing
        [indefinite] a thing
    }

    this = This is { -thing(article: "indefinite") }.
    ```

    `VariantLists` are now deprecated and will be removed from the Syntax
    before version 1.0.

    All escapes sequences can only be used in `StringLiterals` now (see below).
    `\UHHHHHH` is a new escape sequence format suitable for codepoints above
    U+FFFF, e.g. `{"\U01F602"}`.

### Backward-incompatible changes:

  - The backslash character (`\`) is now considered a regular character in
    `TextElements`. It's no longer possible to use escape sequences in
    `TextElements`. Please use `StringLiterals` instead, e.g. `{"\u00A0"}`.
  - The closing curly brace character (`}`) is not allowed in `TextElements`
    now. Please use `StringLiterals` instead: `{"}"}`.
  - `StringLiteral.value` was changed to store the unescaped ("cooked") value.
    `StringLiteral.raw` has been added to store the raw value.
  - The AST of `CallExpressions` was changed to better accommodate the
    introduction of parameterized `Terms`. The `Function` AST node has been
    replaced by the `FunctionReference` node.
  - The leading dash (`-`) is no longer part of the `Identifier` node in
    `Terms` and `TermReferences`.


## fluent 0.9.0 (October 23, 2018)

This release brings support for version 0.7 of the Fluent Syntax spec. The
API remains unchanged. Files written in valid Syntax 0.6 may not parse
correctly in this release. See the summary of backwards-incompatible changes
below.

  - Implement Fluent Syntax 0.7. (#287)

    The major new feature of Syntax 0.7 is the relaxation of the indentation
    requirement for all non-text elements of patterns. It's finally possible
    to leave the closing brace of select expressions unindented:

    ```properties
    emails = { $unread_email_count ->
        [one] You have one unread email.
       *[other] You have { $unread_email_count } unread emails.
    }
    ```

    Consult the [changelog](https://github.com/projectfluent/fluent/releases/tag/v0.7.0) to learn about other changes in Syntax 0.7.

### Backward-incompatible changes:

  - Variant keys can now be either `NumberLiterals` (as previously) or
    `Identifiers`. The `VariantName` node class has been removed. Variant keys
    with spaces in them produce syntax errors, e.g. `[New York]`.
  - `CR` is not a valid EOL character anymore. Please use `LF` or `CRLF`.
  - `Tab` is not recognized as syntax whitespace. It can only be used in
    translation content.


## fluent 0.8.0 (July 24, 2018)

  - Implement support for Fluent Syntax 0.6. (#69)

    Syntax 0.6 keeps the syntax unchanged but makes many changes to the AST.
    Consult https://github.com/projectfluent/fluent/releases/tag/v0.6.0
    for the list of changes.


## fluent 0.7.0 (April 11, 2018)

  - Remove `fluent.migrate`.

    The migration code has been moved into its own repository:
    [fluent-migration](https://hg.mozilla.org/l10n/fluent-migration). See
    [bug 1445881](https://bugzilla.mozilla.org/show_bug.cgi?id=1445881) for
    more information about the move.


  - Add the `ref` field to `VariantExpression`. (#62)

    The `Identifier`-typed `id` field has been removed. The new `ref` field
    contains the `MessageReference` node rigt now. The range of valid
    expressions for `ref` may be extended in the future.

  - Fix missing `Spans` on `Function` nodes.

## fluent 0.6.4 (March 1, 2018)

  - use compare-locales for plurals ordering ([bug 1415844](https://bugzilla.mozilla.org/show_bug.cgi?id=1415844))
  - create transforms when all dependencies have been met up to a changeset
  - support variant keys in BaseNode.equals
  - serialize select expressions on a new line

## fluent 0.6.3 (February 13, 2018)

  - Fix merge code to handle Terms properly

## fluent 0.6.2 (February 8, 2018)

  - Inline Patterns may start with any character. (#48)

    `}`, `.`, `*` and `[` are only special when they appear at the beginning of
    indented Pattern lines. When a Pattern starts on the same line as `id =` or
    `[variant key]`, its first character doesn't carry any special meaning and
    it may be one of those four ones as well.

    This also fixes a regression from 0.6.0 where a message at the EOF without
    value nor attributes was incorrectly parsed as a message with an empty
    Pattern rather than produce a syntax error.

  - Require compare-locales to run and test fluent.migrate. (#47)

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
