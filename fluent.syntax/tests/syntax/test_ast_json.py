from fluent.syntax.ast import from_json
from fluent.syntax.parser import FluentParser

from . import dedent_ftl


class TestASTJSON:
    def test_simple_resource(self):
        input = """\
            foo = Foo
        """

        ast1 = FluentParser().parse(dedent_ftl(input))
        json1 = ast1.to_json()
        ast2 = from_json(json1)
        json2 = ast2.to_json()

        assert json1 == json2

    def test_complex_resource(self):
        input = """\
            ### A Resource comment

            # A comment about shared-photos
            shared-photos =
                { $user_name } { $photo_count ->
                    [0] hasn't added any photos yet
                    [one] added a new photo
                   *[other] added { $photo_count } new photos
                }.


            ## A Section comment

            // A Syntax 0.4 comment about liked-comment
            liked-comment =
                { $user_name } liked your comment on { $user_gender ->
                    [male] his
                    [female] her
                   *[other] their
                } post.
        """

        ast1 = FluentParser().parse(dedent_ftl(input))
        json1 = ast1.to_json()
        ast2 = from_json(json1)
        json2 = ast2.to_json()

        assert json1 == json2

    def test_syntax_error(self):
        input = """\
            foo = Foo {
        """

        ast1 = FluentParser().parse(dedent_ftl(input))
        json1 = ast1.to_json()
        ast2 = from_json(json1)
        json2 = ast2.to_json()

        assert json1 == json2
