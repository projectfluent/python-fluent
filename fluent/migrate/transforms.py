# coding=utf8
from __future__ import unicode_literals

import fluent.syntax.ast as FTL


def evaluate(ctx, node):
    def eval_node(subnode):
        if isinstance(subnode, Transform):
            return subnode(ctx)
        else:
            return subnode

    return node.traverse(eval_node)


class Transform(FTL.Node):
    def __call__(self, ctx):
        raise NotImplementedError


class SOURCE(Transform):
    """Declare the source translation to be migrated with other transforms.

    When evaluated `SOURCE` returns a simple string value.  All \\uXXXX from
    the original translations are converted beforehand to the literal
    characters they encode.

    HTML entities are left unchanged for now because we can't know if they
    should be converted to the characters they represent or not.  Consider the
    following example in which `&amp;` could be replaced with the literal `&`:

        Privacy &amp; History

    vs. these two examples where the HTML encoding should be preserved:

        Erreur&nbsp;!
        Use /help &lt;command&gt; for more information.

    """

    # XXX Perhaps there's a strict subset of HTML entities which must or must
    # not be replaced?

    def __init__(self, path, key):
        self.path = path
        self.key = key

    def __call__(self, ctx):
        return ctx.get_source(self.path, self.key)


class LITERAL(Transform):
    """Create a Pattern with the literal text `value`.

    This transform is used by `LITERAL_FROM` and can be used on its own with
    `CONCAT`.
    """

    def __init__(self, value):
        self.value = value

    def __call__(self, ctx):
        elements = [FTL.TextElement(self.value)]
        return FTL.Pattern(elements)


class LITERAL_FROM(SOURCE):
    """Create a Pattern with the translation value from the given source."""

    def __call__(self, ctx):
        source = super(self.__class__, self).__call__(ctx)
        return LITERAL(source)(ctx)


class EXTERNAL(Transform):
    """Create a Pattern with the external argument `name`

    This is a common use-case when joining translations with CONCAT.
    """

    def __init__(self, name):
        self.name = name

    def __call__(self, ctx):
        external = FTL.ExternalArgument(
            id=FTL.Identifier(self.name)
        )
        return FTL.Pattern([external])


class REPLACE(Transform):
    """Replace various placeables in the translation with FTL placeables.

    The original placeables are defined as keys on the `replacements` dict.
    For each key the value is defined as a list of FTL Expressions to be
    interpolated.
    """

    def __init__(self, value, replacements):
        self.value = value
        self.replacements = replacements

    def __call__(self, ctx):

        # Only replace placeable which are present in the translation.
        replacements = {
            k: v for k, v in self.replacements.iteritems() if k in self.value
        }

        # Order the original placeables by their position in the translation.
        keys_in_order = sorted(
            replacements.keys(),
            lambda x, y: self.value.find(x) - self.value.find(y)
        )

        # Used to reduce the `keys_in_order` list.
        def replace(acc, cur):
            """Convert original placeables and text into FTL Nodes.

            For each original placeable the translation will be partitioned
            around it and the text before it will be converted into an
            `FTL.TextElement` and the placeable will be replaced with its
            replacement. The text following the placebale will be fed again to
            the `replace` function.
            """

            parts, rest = acc
            before, key, after = rest.value.partition(cur)

            # Return the elements found and converted so far, and the remaining
            # text which hasn't been scanned for placeables yet.
            return (
                parts + [FTL.TextElement(before), replacements[key]],
                FTL.TextElement(after)
            )

        def is_non_empty(elem):
            """Used for filtering empty `FTL.TextElement` nodes out."""
            return not isinstance(elem, FTL.TextElement) or len(elem.value)

        # Start with an empty list of elements and the original translation.
        init = ([], FTL.TextElement(self.value))
        parts, tail = reduce(replace, keys_in_order, init)

        # Explicitly concat the trailing part to get the full list of elements
        # and filter out the empty ones.
        elements = filter(is_non_empty, parts + [tail])

        return FTL.Pattern(elements)


class REPLACE_FROM(SOURCE):
    """Create a Pattern with interpolations from given source.

    Interpolations in the translation value from the given source will be
    replaced with FTL placeables using the `REPLACE` transform.
    """

    def __init__(self, path, key, replacements):
        super(self.__class__, self).__init__(path, key)
        self.replacements = replacements

    def __call__(self, ctx):
        value = super(self.__class__, self).__call__(ctx)
        return REPLACE(value, self.replacements)(ctx)


class PLURALS(Transform):
    """Convert semicolon-separated variants into a select expression.

    Build an `FTL.SelectExpression` with the supplied `selector` and variants
    extracted from the source.  Each variant will be run through the
    `foreach` function, which should return an `FTL.Node`.
    """

    def __init__(self, value, selector, foreach):
        self.value = value
        self.selector = selector
        self.foreach = foreach

    def __call__(self, ctx):
        variants = self.value.split(';')
        keys = ctx.plural_categories
        last_index = min(len(variants), len(keys)) - 1

        def createVariant(zipped_enum):
            index, (key, variant) = zipped_enum
            # Run the legacy variant through `foreach` which returns an
            # `FTL.Node` describing the transformation required for each
            # variant.  Then evaluate it to a migrated FTL node.
            value = evaluate(ctx, self.foreach(variant))
            return FTL.Variant(
                key=FTL.Symbol(key),
                value=value,
                default=index == last_index
            )

        select = FTL.SelectExpression(
            expression=self.selector,
            variants=map(createVariant, enumerate(zip(keys, variants)))
        )

        return FTL.Pattern([select])


class PLURALS_FROM(SOURCE):
    """Create a Pattern with plurals from given source.

    Semi-colon separated variants in the translation value from the given
    source will be replaced with an FTL select expression using the `PLURALS`
    transform.
    """

    def __init__(self, path, key, selector, foreach):
        super(self.__class__, self).__init__(path, key)
        self.selector = selector
        self.foreach = foreach

    def __call__(self, ctx):
        value = super(self.__class__, self).__call__(ctx)
        return PLURALS(value, self.selector, self.foreach)(ctx)


class CONCAT(Transform):
    """Concatenate elements of many patterns."""

    def __init__(self, *patterns):
        self.patterns = list(patterns)

    def __call__(self, ctx):
        # Flatten the list of patterns of which each has a list of elements.
        elements = [
            elems for pattern in self.patterns for elems in pattern.elements
        ]

        # Merge adjecent `FTL.TextElement` nodes.
        def merge_adjecent_text(acc, cur):
            if type(cur) == FTL.TextElement and len(acc):
                last = acc[-1]
                if type(last) == FTL.TextElement:
                    last.value += cur.value
                else:
                    acc.append(cur)
            else:
                acc.append(cur)
            return acc

        elements = reduce(merge_adjecent_text, elements, [])
        return FTL.Pattern(elements)

    def traverse(self, fun):
        def visit(value):
            if isinstance(value, FTL.Node):
                return value.traverse(fun)
            if isinstance(value, list):
                return fun(map(visit, value))
            else:
                return fun(value)

        node = self.__class__(
            *[
                visit(value) for value in self.patterns
            ]
        )

        return fun(node)

    def to_json(self):
        def to_json(value):
            if isinstance(value, FTL.Node):
                return value.to_json()
            else:
                return value

        return {
            'type': self.__class__.__name__,
            'patterns': [
                to_json(value) for value in self.patterns
            ]
        }
