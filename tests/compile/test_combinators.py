import opyl
from opyl import Span, PrimitiveKind
from opyl.compile.combinators import (
    TokenStream,
    OrNot,
    just,
    integer,
    Parse,
    ident,
    lines,
)
from opyl import lexemes


class TestOrNot:
    def test_match(self):
        primitive = opyl.Primitive(Span.default(), PrimitiveKind.Plus)
        tokens = TokenStream([primitive])
        parser = OrNot(just(PrimitiveKind.Plus))

        result = parser(tokens)
        assert isinstance(result, Parse.Match) and result.item is primitive

    def test_no_match(self):
        tokens = TokenStream([opyl.Primitive(Span.default(), PrimitiveKind.Plus)])
        parser = OrNot(just(PrimitiveKind.Hyphen))

        result = parser(tokens)
        assert isinstance(result, Parse.Match) and result.item is None

    def test_error(self):
        kind = PrimitiveKind.Plus
        expectation = f"Expected a {kind.value}!"
        tokens = TokenStream([opyl.Primitive(Span.default(), kind)])
        parser = OrNot(just(PrimitiveKind.Hyphen).expect(expectation))

        result = parser(tokens)
        assert (
            isinstance(result, Parse.Errors)
            and len(result.errors) == 1
            and result.errors[0] == (0, expectation)
        )


class TestThen:
    def test_match(self):
        first = opyl.Primitive(Span.default(), PrimitiveKind.Plus)
        second = opyl.Primitive(Span.default(), PrimitiveKind.Hyphen)

        tokens = TokenStream([first, second])
        parser = just(PrimitiveKind.Plus).then(just(PrimitiveKind.Hyphen))

        result = parser(tokens)
        assert (
            isinstance(result, Parse.Match)
            and isinstance(result.item, tuple)
            and len(result.item) == 2
        )
        assert result.item[0] == first and result.item[1] == second

    def test_first_no_match(self):
        first = opyl.Primitive(Span.default(), PrimitiveKind.Plus)
        second = opyl.Primitive(Span.default(), PrimitiveKind.Hyphen)

        tokens = TokenStream([first, second])
        parser = just(PrimitiveKind.Hyphen).then(just(PrimitiveKind.Hyphen))

        result = parser(tokens)
        assert isinstance(result, Parse.NoMatch)

    def test_second_no_match(self):
        first = opyl.Primitive(Span.default(), PrimitiveKind.Plus)
        second = opyl.Primitive(Span.default(), PrimitiveKind.Hyphen)

        tokens = TokenStream([first, second])
        parser = just(PrimitiveKind.Plus).then(just(PrimitiveKind.Plus))

        result = parser(tokens)
        assert isinstance(result, Parse.NoMatch)

    def test_neither_match(self):
        first = opyl.Primitive(Span.default(), PrimitiveKind.Plus)
        second = opyl.Primitive(Span.default(), PrimitiveKind.Hyphen)

        tokens = TokenStream([first, second])
        parser = just(PrimitiveKind.Hyphen).then(just(PrimitiveKind.Plus))

        result = parser(tokens)
        assert isinstance(result, Parse.NoMatch)

    def test_first_error(self):
        expectation = "Expectation failed."
        first = opyl.Primitive(Span.default(), PrimitiveKind.Plus)
        second = opyl.Primitive(Span.default(), PrimitiveKind.Hyphen)

        tokens = TokenStream([first, second])
        parser = (just(PrimitiveKind.Hyphen).expect(expectation)).then(
            just(PrimitiveKind.Hyphen)
        )

        result = parser(tokens)
        assert isinstance(result, Parse.Errors) and len(result.errors) == 1
        assert result.errors[0] == (0, expectation)

    def test_second_error(self):
        expectation = "Expectation failed."
        first = opyl.Primitive(Span.default(), PrimitiveKind.Plus)
        second = opyl.Primitive(Span.default(), PrimitiveKind.Hyphen)

        tokens = TokenStream([first, second])
        parser = just(PrimitiveKind.Plus).then(
            just(PrimitiveKind.Plus).expect(expectation)
        )

        result = parser(tokens)
        assert isinstance(result, Parse.Errors) and len(result.errors) == 1
        assert result.errors[0] == (1, expectation)

    def test_both_error(self):
        expectation = "Expectation failed."
        first = opyl.Primitive(Span.default(), PrimitiveKind.Plus)
        second = opyl.Primitive(Span.default(), PrimitiveKind.Hyphen)

        tokens = TokenStream([first, second])
        parser = (just(PrimitiveKind.Hyphen).expect(expectation)).then(
            just(PrimitiveKind.Plus).expect(expectation)
        )

        result = parser(tokens)
        assert isinstance(result, Parse.Errors) and len(result.errors) == 1
        assert result.errors[0] == (0, expectation)


class TestAlternative:
    def test_first_match(self):
        first = opyl.Primitive(Span.default(), PrimitiveKind.Plus)
        second = opyl.Primitive(Span.default(), PrimitiveKind.Hyphen)

        tokens = TokenStream([first, second])
        parser = just(PrimitiveKind.Plus) | just(PrimitiveKind.Plus)

        result = parser(tokens)
        assert isinstance(result, Parse.Match) and result.item is first

    def test_second_match(self):
        first = opyl.Primitive(Span.default(), PrimitiveKind.Plus)
        second = opyl.Primitive(Span.default(), PrimitiveKind.Hyphen)

        tokens = TokenStream([first, second])
        parser = just(PrimitiveKind.Hyphen) | just(PrimitiveKind.Plus)

        result = parser(tokens)
        assert isinstance(result, Parse.Match) and result.item is first

    def test_neither_match(self):
        first = opyl.Primitive(Span.default(), PrimitiveKind.Plus)
        second = opyl.Primitive(Span.default(), PrimitiveKind.Hyphen)

        tokens = TokenStream([first, second])
        parser = just(PrimitiveKind.Hyphen) | just(PrimitiveKind.Hyphen)

        result = parser(tokens)
        assert isinstance(result, Parse.NoMatch)

    def test_first_error(self):
        expectation = "foo"
        first = opyl.Primitive(Span.default(), PrimitiveKind.Plus)
        second = opyl.Primitive(Span.default(), PrimitiveKind.Hyphen)

        tokens = TokenStream([first, second])
        parser = (just(PrimitiveKind.Hyphen).expect(expectation)) | just(
            PrimitiveKind.Hyphen
        )

        result = parser(tokens)
        assert isinstance(result, Parse.Errors) and len(result.errors) == 1
        assert result.errors[0] == (0, expectation)

    def test_second_error(self):
        expectation = "foo"
        first = opyl.Primitive(Span.default(), PrimitiveKind.Plus)
        second = opyl.Primitive(Span.default(), PrimitiveKind.Hyphen)

        tokens = TokenStream([first, second])
        parser = just(PrimitiveKind.Hyphen) | (
            just(PrimitiveKind.Hyphen).expect(expectation)
        )

        result = parser(tokens)
        assert isinstance(result, Parse.Errors) and len(result.errors) == 1
        assert result.errors[0] == (0, expectation)


class TestIgnoreThen:
    def test_match(self):
        first = opyl.Primitive(Span.default(), PrimitiveKind.Plus)
        second = opyl.Primitive(Span.default(), PrimitiveKind.Hyphen)

        tokens = TokenStream([first, second])
        parser = just(PrimitiveKind.Plus).ignore_then(just(PrimitiveKind.Hyphen))

        result = parser(tokens)
        assert isinstance(result, Parse.Match)
        assert result.item == second

    def test_first_no_match(self):
        first = opyl.Primitive(Span.default(), PrimitiveKind.Plus)
        second = opyl.Primitive(Span.default(), PrimitiveKind.Hyphen)

        tokens = TokenStream([first, second])
        parser = just(PrimitiveKind.Hyphen).ignore_then(just(PrimitiveKind.Hyphen))

        result = parser(tokens)
        assert isinstance(result, Parse.NoMatch)

    def test_second_no_match(self):
        first = opyl.Primitive(Span.default(), PrimitiveKind.Plus)
        second = opyl.Primitive(Span.default(), PrimitiveKind.Hyphen)

        tokens = TokenStream([first, second])
        parser = just(PrimitiveKind.Plus).ignore_then(just(PrimitiveKind.Plus))

        result = parser(tokens)
        assert isinstance(result, Parse.NoMatch)

    def test_neither_match(self):
        first = opyl.Primitive(Span.default(), PrimitiveKind.Plus)
        second = opyl.Primitive(Span.default(), PrimitiveKind.Hyphen)

        tokens = TokenStream([first, second])
        parser = just(PrimitiveKind.Hyphen).ignore_then(just(PrimitiveKind.Plus))

        result = parser(tokens)
        assert isinstance(result, Parse.NoMatch)

    def test_first_error(self):
        expectation = "Expectation failed."
        first = opyl.Primitive(Span.default(), PrimitiveKind.Plus)
        second = opyl.Primitive(Span.default(), PrimitiveKind.Hyphen)

        tokens = TokenStream([first, second])
        parser = (just(PrimitiveKind.Hyphen).expect(expectation)).ignore_then(
            just(PrimitiveKind.Hyphen)
        )

        result = parser(tokens)
        assert isinstance(result, Parse.Errors) and len(result.errors) == 1
        assert result.errors[0] == (0, expectation)

    def test_second_error(self):
        expectation = "Expectation failed."
        first = opyl.Primitive(Span.default(), PrimitiveKind.Plus)
        second = opyl.Primitive(Span.default(), PrimitiveKind.Hyphen)

        tokens = TokenStream([first, second])
        parser = just(PrimitiveKind.Plus).ignore_then(
            just(PrimitiveKind.Plus).expect(expectation)
        )

        result = parser(tokens)
        assert isinstance(result, Parse.Errors) and len(result.errors) == 1
        assert result.errors[0] == (1, expectation)

    def test_both_error(self):
        expectation = "Expectation failed."
        first = opyl.Primitive(Span.default(), PrimitiveKind.Plus)
        second = opyl.Primitive(Span.default(), PrimitiveKind.Hyphen)

        tokens = TokenStream([first, second])
        parser = (just(PrimitiveKind.Hyphen).expect(expectation)).ignore_then(
            just(PrimitiveKind.Plus).expect(expectation)
        )

        result = parser(tokens)
        assert isinstance(result, Parse.Errors) and len(result.errors) == 1
        assert result.errors[0] == (0, expectation)


class TestThenIgnore:
    def test_match(self):
        first = opyl.Primitive(Span.default(), PrimitiveKind.Plus)
        second = opyl.Primitive(Span.default(), PrimitiveKind.Hyphen)

        tokens = TokenStream([first, second])
        parser = just(PrimitiveKind.Plus).then_ignore(just(PrimitiveKind.Hyphen))

        result = parser(tokens)
        assert isinstance(result, Parse.Match)
        assert result.item == first

    def test_first_no_match(self):
        first = opyl.Primitive(Span.default(), PrimitiveKind.Plus)
        second = opyl.Primitive(Span.default(), PrimitiveKind.Hyphen)

        tokens = TokenStream([first, second])
        parser = just(PrimitiveKind.Hyphen).then_ignore(just(PrimitiveKind.Hyphen))

        result = parser(tokens)
        assert isinstance(result, Parse.NoMatch)

    def test_second_no_match(self):
        first = opyl.Primitive(Span.default(), PrimitiveKind.Plus)
        second = opyl.Primitive(Span.default(), PrimitiveKind.Hyphen)

        tokens = TokenStream([first, second])
        parser = just(PrimitiveKind.Plus).then_ignore(just(PrimitiveKind.Plus))

        result = parser(tokens)
        assert isinstance(result, Parse.NoMatch)

    def test_neither_match(self):
        first = opyl.Primitive(Span.default(), PrimitiveKind.Plus)
        second = opyl.Primitive(Span.default(), PrimitiveKind.Hyphen)

        tokens = TokenStream([first, second])
        parser = just(PrimitiveKind.Hyphen).then_ignore(just(PrimitiveKind.Plus))

        result = parser(tokens)
        assert isinstance(result, Parse.NoMatch)

    def test_first_error(self):
        expectation = "Expectation failed."
        first = opyl.Primitive(Span.default(), PrimitiveKind.Plus)
        second = opyl.Primitive(Span.default(), PrimitiveKind.Hyphen)

        tokens = TokenStream([first, second])
        parser = (just(PrimitiveKind.Hyphen).expect(expectation)).then_ignore(
            just(PrimitiveKind.Hyphen)
        )

        result = parser(tokens)
        assert isinstance(result, Parse.Errors) and len(result.errors) == 1
        assert result.errors[0] == (0, expectation)

    def test_second_error(self):
        expectation = "Expectation failed."
        first = opyl.Primitive(Span.default(), PrimitiveKind.Plus)
        second = opyl.Primitive(Span.default(), PrimitiveKind.Hyphen)

        tokens = TokenStream([first, second])
        parser = just(PrimitiveKind.Plus).then_ignore(
            just(PrimitiveKind.Plus).expect(expectation)
        )

        result = parser(tokens)
        assert isinstance(result, Parse.Errors) and len(result.errors) == 1
        assert result.errors[0] == (1, expectation)

    def test_both_error(self):
        expectation = "Expectation failed."
        first = opyl.Primitive(Span.default(), PrimitiveKind.Plus)
        second = opyl.Primitive(Span.default(), PrimitiveKind.Hyphen)

        tokens = TokenStream([first, second])
        parser = (just(PrimitiveKind.Hyphen).expect(expectation)).then_ignore(
            just(PrimitiveKind.Plus).expect(expectation)
        )

        result = parser(tokens)
        assert isinstance(result, Parse.Errors) and len(result.errors) == 1
        assert result.errors[0] == (0, expectation)


class TestSeparatedBy:
    def test_match(self):
        first = lexemes.IntegerLiteral(Span.default(), 0)
        second = lexemes.IntegerLiteral(Span.default(), 1)

        stream = TokenStream(
            [
                first,
                opyl.Primitive(Span.default(), PrimitiveKind.Comma),
                second,
            ]
        )

        parser = integer.separated_by(just(PrimitiveKind.Comma))
        result = parser(stream)
        assert (
            isinstance(result, Parse.Match)
            and isinstance(result.item, list)
            and len(result.item) == 2
        )
        assert result.item[0].integer == first.integer
        assert result.item[1].integer == second.integer

    def test_with_trailing(self):
        # This test should expect a Parse.Match because its beyond the scope of
        # SeparatedBy to enforce anything "beyond" the alternating pattern of
        # item - separator - item. After the pattern fails - even if thats because
        # a separator was found when there shouldn't have been one - the parser no
        # longer cares. As long as the correct number of items were found, it should
        # be considered successful. So...
        # TODO: Any code that assumes this parser should return NoMatch when an unexpected
        # trailing separator is found should be reworked to no longer make this assumption.
        # BASICALLY: The only "NoMatch" condition on this parser is on whether the minimum
        # number of items were parsed.

        stream = TokenStream(
            [
                lexemes.IntegerLiteral(Span.default(), 0),
                opyl.Primitive(Span.default(), PrimitiveKind.Comma),
                lexemes.IntegerLiteral(Span.default(), 1),
                opyl.Primitive(Span.default(), PrimitiveKind.Comma),
            ]
        )

        parser = integer.separated_by(just(PrimitiveKind.Comma))
        result = parser(stream)
        assert isinstance(result, Parse.Match)

    def test_with_leading(self):
        stream = TokenStream(
            [
                opyl.Primitive(Span.default(), PrimitiveKind.Comma),
                lexemes.IntegerLiteral(Span.default(), 0),
                opyl.Primitive(Span.default(), PrimitiveKind.Comma),
                lexemes.IntegerLiteral(Span.default(), 1),
            ]
        )

        result = integer.separated_by(just(PrimitiveKind.Comma)).parse(stream)
        assert isinstance(result, Parse.Match) and len(result.item) == 0

    def test_allow_trailing_match(self):
        first = lexemes.IntegerLiteral(Span.default(), 0)
        second = lexemes.IntegerLiteral(Span.default(), 1)

        stream = TokenStream(
            [
                first,
                opyl.Primitive(Span.default(), PrimitiveKind.Comma),
                second,
            ]
        )

        result = (
            integer.separated_by(just(PrimitiveKind.Comma))
            .allow_trailing()
            .parse(stream)
        )
        assert isinstance(result, Parse.Match) and isinstance(result.item, list)
        assert result.item[0].integer == first.integer
        assert result.item[1].integer == second.integer

    def test_allow_trailing_with_trailing_match(self):
        first = lexemes.IntegerLiteral(Span.default(), 0)
        second = lexemes.IntegerLiteral(Span.default(), 1)

        stream = TokenStream(
            [
                first,
                opyl.Primitive(Span.default(), PrimitiveKind.Comma),
                second,
                opyl.Primitive(Span.default(), PrimitiveKind.Comma),
            ]
        )

        result = (
            integer.separated_by(just(PrimitiveKind.Comma))
            .allow_trailing()
            .parse(stream)
        )
        assert isinstance(result, Parse.Match) and isinstance(result.item, list)
        assert result.item[0].integer == first.integer
        assert result.item[1].integer == second.integer

    def test_allow_leading_match(self):
        first = lexemes.IntegerLiteral(Span.default(), 0)
        second = lexemes.IntegerLiteral(Span.default(), 1)

        stream = TokenStream(
            [
                first,
                opyl.Primitive(Span.default(), PrimitiveKind.Comma),
                second,
            ]
        )

        result = (
            integer.separated_by(just(PrimitiveKind.Comma))
            .allow_leading()
            .parse(stream)
        )
        assert isinstance(result, Parse.Match) and isinstance(result.item, list)
        assert result.item[0].integer == first.integer
        assert result.item[1].integer == second.integer

    def test_allow_leading_with_leading_match(self):
        first = lexemes.IntegerLiteral(Span.default(), 0)
        second = lexemes.IntegerLiteral(Span.default(), 1)

        stream = TokenStream(
            [
                opyl.Primitive(Span.default(), PrimitiveKind.Comma),
                first,
                opyl.Primitive(Span.default(), PrimitiveKind.Comma),
                second,
            ]
        )

        result = (
            integer.separated_by(just(PrimitiveKind.Comma))
            .allow_leading()
            .parse(stream)
        )
        assert isinstance(result, Parse.Match) and isinstance(result.item, list)
        assert result.item[0].integer == first.integer
        assert result.item[1].integer == second.integer

    def test_allow_leading_with_trailing_no_match(self):
        stream = TokenStream(
            [
                lexemes.IntegerLiteral(Span.default(), 0),
                opyl.Primitive(Span.default(), PrimitiveKind.Comma),
                lexemes.IntegerLiteral(Span.default(), 1),
                opyl.Primitive(Span.default(), PrimitiveKind.Comma),
            ]
        )

        result = (
            integer.separated_by(just(PrimitiveKind.Comma))
            .allow_leading()
            .parse(stream)
        )
        assert isinstance(result, Parse.Match)

    def test_allow_trailing_with_leading_no_match(self):
        stream = TokenStream(
            [
                opyl.Primitive(Span.default(), PrimitiveKind.Comma),
                lexemes.IntegerLiteral(Span.default(), 0),
                opyl.Primitive(Span.default(), PrimitiveKind.Comma),
                lexemes.IntegerLiteral(Span.default(), 1),
            ]
        )

        result = (
            integer.separated_by(just(PrimitiveKind.Comma))
            .allow_trailing()
            .parse(stream)
        )
        assert isinstance(result, Parse.Match)

    def test_allow_leading_and_trailing_with_both_match(self):
        stream = TokenStream(
            [
                opyl.Primitive(Span.default(), PrimitiveKind.Comma),
                lexemes.IntegerLiteral(Span.default(), 0),
                opyl.Primitive(Span.default(), PrimitiveKind.Comma),
                lexemes.IntegerLiteral(Span.default(), 1),
                opyl.Primitive(Span.default(), PrimitiveKind.Comma),
            ]
        )

        result = (
            integer.separated_by(just(PrimitiveKind.Comma))
            .allow_leading()
            .allow_trailing()
            .parse(stream)
        )
        assert isinstance(result, Parse.Match)

    def test_at_least_3_but_got_2(self):
        stream = TokenStream(
            [
                lexemes.IntegerLiteral(Span.default(), 0),
                opyl.Primitive(Span.default(), PrimitiveKind.Comma),
                lexemes.IntegerLiteral(Span.default(), 1),
            ]
        )

        result = (
            integer.separated_by(just(PrimitiveKind.Comma)).at_least(3).parse(stream)
        )
        assert isinstance(result, Parse.NoMatch)

    def test_at_least_3_got_3(self):
        stream = TokenStream(
            [
                lexemes.IntegerLiteral(Span.default(), 0),
                opyl.Primitive(Span.default(), PrimitiveKind.Comma),
                lexemes.IntegerLiteral(Span.default(), 1),
                opyl.Primitive(Span.default(), PrimitiveKind.Comma),
                lexemes.IntegerLiteral(Span.default(), 2),
            ]
        )

        result = (
            integer.separated_by(just(PrimitiveKind.Comma)).at_least(3).parse(stream)
        )
        assert isinstance(result, Parse.Match)

    def test_at_least_3_got_4(self):
        stream = TokenStream(
            [
                lexemes.IntegerLiteral(Span.default(), 0),
                opyl.Primitive(Span.default(), PrimitiveKind.Comma),
                lexemes.IntegerLiteral(Span.default(), 1),
                opyl.Primitive(Span.default(), PrimitiveKind.Comma),
                lexemes.IntegerLiteral(Span.default(), 2),
                opyl.Primitive(Span.default(), PrimitiveKind.Comma),
                lexemes.IntegerLiteral(Span.default(), 3),
            ]
        )

        result = (
            integer.separated_by(just(PrimitiveKind.Comma)).at_least(3).parse(stream)
        )
        assert isinstance(result, Parse.Match)

    def test_empty_no_minimum(self):
        stream = TokenStream([])

        result = integer.separated_by(just(PrimitiveKind.Comma)).parse(stream)
        assert isinstance(result, Parse.Match)

    def test_empty_doesnt_meet_minimum(self):
        stream = TokenStream([])

        result = (
            integer.separated_by(just(PrimitiveKind.Comma)).at_least(1).parse(stream)
        )
        assert isinstance(result, Parse.NoMatch)

    def test_empty_allow_leading_no_minimum(self):
        stream = TokenStream([])

        result = (
            integer.separated_by(just(PrimitiveKind.Comma))
            .allow_leading()
            .parse(stream)
        )
        assert isinstance(result, Parse.Match)

    def test_empty_allow_leading_doesnt_meet_minimum(self):
        stream = TokenStream([])

        result = (
            integer.separated_by(just(PrimitiveKind.Comma))
            .allow_leading()
            .at_least(1)
            .parse(stream)
        )
        assert isinstance(result, Parse.NoMatch)


class TestExpect:
    def test_match(self):
        kind = PrimitiveKind.Plus
        token = lexemes.Primitive(Span.default(), kind)
        stream = TokenStream([token])

        result = just(kind).expect(f"Expected {kind.value}").parse(stream)
        assert isinstance(result, Parse.Match) and result.item == token

    def test_no_match(self):
        kind = PrimitiveKind.Plus
        token = lexemes.Primitive(Span.default(), kind)
        stream = TokenStream([token])

        expectation = f"Expected {kind.value}"
        result = just(PrimitiveKind.Hyphen).expect(expectation).parse(stream)
        assert (
            isinstance(result, Parse.Errors)
            and len(result.errors) == 1
            and result.errors[0] == (0, expectation)
        )


class TestDelimitedBy:
    def test_match(self):
        start_kind = PrimitiveKind.LeftBrace
        end_kind = PrimitiveKind.RightBrace
        token = lexemes.IntegerLiteral(Span.default(), 420)
        stream = TokenStream(
            [
                lexemes.Primitive(Span.default(), start_kind),
                token,
                lexemes.Primitive(Span.default(), end_kind),
            ]
        )

        result = integer.delimited_by(start=just(start_kind), end=just(end_kind)).parse(
            stream
        )

        assert isinstance(result, Parse.Match) and result.item.integer == token.integer

    def test_no_closing(self):
        start_kind = PrimitiveKind.LeftBrace
        end_kind = PrimitiveKind.RightBrace
        token = lexemes.IntegerLiteral(Span.default(), 420)
        stream = TokenStream(
            [
                lexemes.Primitive(Span.default(), start_kind),
                token,
                lexemes.Primitive(Span.default(), PrimitiveKind.RightParenthesis),
            ]
        )

        result = integer.delimited_by(start=just(start_kind), end=just(end_kind)).parse(
            stream
        )

        assert isinstance(result, Parse.Errors) and len(result.errors) == 1
        assert result.errors[0][0] == 2

    def test_no_opening(self):
        start_kind = PrimitiveKind.LeftBrace
        end_kind = PrimitiveKind.RightBrace
        token = lexemes.IntegerLiteral(Span.default(), 420)
        stream = TokenStream(
            [
                lexemes.Primitive(Span.default(), PrimitiveKind.LeftParenthesis),
                token,
                lexemes.Primitive(Span.default(), end_kind),
            ]
        )

        result = integer.delimited_by(start=just(start_kind), end=just(end_kind)).parse(
            stream
        )

        assert isinstance(result, Parse.Errors) and len(result.errors) == 1
        assert result.errors[0][0] == 0


class TestLines:
    def test_match(self):
        integers = (
            lexemes.IntegerLiteral(Span.default(), 1),
            lexemes.IntegerLiteral(Span.default(), 2),
            lexemes.IntegerLiteral(Span.default(), 3),
        )

        stream = TokenStream(
            [
                integers[0],
                lexemes.Primitive(Span.default(), PrimitiveKind.NewLine),
                integers[1],
                lexemes.Primitive(Span.default(), PrimitiveKind.NewLine),
                integers[2],
            ]
        )

        result = lines(integer).parse(stream)
        assert isinstance(result, Parse.Match) and all(
            parsed.integer == token.integer
            for parsed, token in zip(result.item, integers)
        )

    def test_match_with_trailing(self):
        integers = (
            lexemes.IntegerLiteral(Span.default(), 1),
            lexemes.IntegerLiteral(Span.default(), 2),
            lexemes.IntegerLiteral(Span.default(), 3),
        )

        stream = TokenStream(
            [
                integers[0],
                lexemes.Primitive(Span.default(), PrimitiveKind.NewLine),
                integers[1],
                lexemes.Primitive(Span.default(), PrimitiveKind.NewLine),
                integers[2],
                lexemes.Primitive(Span.default(), PrimitiveKind.NewLine),
            ]
        )

        result = lines(integer).parse(stream)
        assert isinstance(result, Parse.Match) and all(
            parsed.integer == token.integer
            for parsed, token in zip(result.item, integers)
        )

    def test_match_with_leading(self):
        integers = (
            lexemes.IntegerLiteral(Span.default(), 1),
            lexemes.IntegerLiteral(Span.default(), 2),
            lexemes.IntegerLiteral(Span.default(), 3),
        )

        stream = TokenStream(
            [
                lexemes.Primitive(Span.default(), PrimitiveKind.NewLine),
                integers[0],
                lexemes.Primitive(Span.default(), PrimitiveKind.NewLine),
                integers[1],
                lexemes.Primitive(Span.default(), PrimitiveKind.NewLine),
                integers[2],
            ]
        )

        result = lines(integer).parse(stream)
        assert isinstance(result, Parse.Match) and all(
            parsed.integer == token.integer
            for parsed, token in zip(result.item, integers)
        )

    def test_match_with_leading_and_trailing(self):
        integers = (
            lexemes.IntegerLiteral(Span.default(), 1),
            lexemes.IntegerLiteral(Span.default(), 2),
            lexemes.IntegerLiteral(Span.default(), 3),
        )

        stream = TokenStream(
            [
                lexemes.Primitive(Span.default(), PrimitiveKind.NewLine),
                integers[0],
                lexemes.Primitive(Span.default(), PrimitiveKind.NewLine),
                integers[1],
                lexemes.Primitive(Span.default(), PrimitiveKind.NewLine),
                integers[2],
                lexemes.Primitive(Span.default(), PrimitiveKind.NewLine),
            ]
        )

        result = lines(integer).parse(stream)
        assert isinstance(result, Parse.Match) and all(
            parsed.integer == token.integer
            for parsed, token in zip(result.item, integers)
        )

    def test_no_match_first_item(self):
        integers = (
            lexemes.IntegerLiteral(Span.default(), 1),
            lexemes.IntegerLiteral(Span.default(), 2),
            lexemes.IntegerLiteral(Span.default(), 3),
        )

        stream = TokenStream(
            [
                lexemes.Primitive(Span.default(), PrimitiveKind.Plus),
                lexemes.Primitive(Span.default(), PrimitiveKind.NewLine),
                integers[1],
                lexemes.Primitive(Span.default(), PrimitiveKind.NewLine),
                integers[2],
                lexemes.Primitive(Span.default(), PrimitiveKind.NewLine),
            ]
        )

        result = lines(integer).parse(stream)
        assert isinstance(result, Parse.Match)


def test_return_type_present():
    name = "foo"
    stream = TokenStream(
        [
            lexemes.Primitive(Span.default(), PrimitiveKind.RightArrow),
            lexemes.Identifier(Span.default(), name),
        ]
    )

    result = just(PrimitiveKind.RightArrow).or_not().ignore_then(ident).parse(stream)
    assert (
        isinstance(result, Parse.Match)
        and result.item is not None
        and result.item.name == name
    )


def test_return_type_not_present():
    stream = TokenStream([])
    result = just(PrimitiveKind.RightArrow).or_not().ignore_then(ident).parse(stream)
    assert isinstance(result, Parse.NoMatch)


def test_return_type_only_arrow():
    stream = TokenStream(
        [
            lexemes.Primitive(Span.default(), PrimitiveKind.RightArrow),
        ]
    )

    result = just(PrimitiveKind.RightArrow).or_not().ignore_then(ident).parse(stream)
    assert isinstance(result, Parse.NoMatch)
