import opyl
from opyl import Span, PrimitiveKind
from opyl.compile.combinators import TokenStream, OrNot, just, integer, Parse
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
        parser = just(PrimitiveKind.Hyphen) | just(PrimitiveKind.Hyphen)

        result = parser(tokens)
        assert isinstance(result, Parse.Match) and result.item is second

    def test_neither_match(self):
        first = opyl.Primitive(Span.default(), PrimitiveKind.Plus)
        second = opyl.Primitive(Span.default(), PrimitiveKind.Hyphen)

        tokens = TokenStream([first, second])
        parser = just(PrimitiveKind.Hyphen) | just(PrimitiveKind.Plus)

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
        parser = just(PrimitiveKind.Hyphen) | just(PrimitiveKind.Plus).expect(
            expectation
        )

        result = parser(tokens)
        assert isinstance(result, Parse.Errors) and len(result.errors) == 1
        assert result.errors[0] == (1, expectation)


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
        assert isinstance(result, Parse.NoMatch)

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
        assert isinstance(result, Parse.NoMatch)

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
        assert isinstance(result, Parse.NoMatch)

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
        assert isinstance(result, Parse.NoMatch)

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
