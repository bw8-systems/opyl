import pytest

from opyl.compile.token import (
    Identifier,
    IntegerLiteral,
    Basic,
    Token,
)
from opyl.support.stream import Stream
from opyl.compile import lex
from opyl.support.atoms import just, integer


@pytest.fixture
def no_trailing_or_leading_list() -> Stream[Token]:
    return lex.tokenize("1, 2, 3, 4").unwrap()[0]


class TestStream:
    def test_startswith_str_success(self):
        stream = Stream.from_source("foo")

        assert stream.startswith("f")
        assert stream.startswith("fo")
        assert stream.startswith("foo")

    def test_startswith_str_fail(self):
        stream = Stream.from_source("foo")

        assert not stream.startswith("oof")
        assert not stream.startswith("of")
        assert not stream.startswith(" f")

    def test_startswith_str_empty(self):
        stream = Stream.from_source("")

        assert not stream.startswith("")
        assert not stream.startswith(" ")

    def test_startswith_empty_pattern(self):
        stream = Stream.from_source("foo")

        assert not stream.startswith("")
        assert not stream.startswith(" ")

    def test_startswith_tok_success(self):
        tokens, _ = lex.tokenize("foo").unwrap()

        assert tokens.startswith([Identifier("foo")])

    def test_startswith_multi_tok_success(self):
        tokens, _ = lex.tokenize("foo 4").unwrap()

        assert tokens.startswith([Identifier("foo"), IntegerLiteral(4)])


class TestCombinator:
    def test_separated_by_dont_allow_trailing_leading(
        self, no_trailing_or_leading_list: Stream[Token]
    ):
        result = (
            integer.separated_by(just(Basic.Comma))
            .parse(no_trailing_or_leading_list)
            .unwrap()
        )
        assert result[0] == [
            IntegerLiteral(1),
            IntegerLiteral(2),
            IntegerLiteral(3),
            IntegerLiteral(4),
        ]

    def test_separated_by_allow_trailing(
        self, no_trailing_or_leading_list: Stream[Token]
    ):
        result = (
            integer.separated_by(just(Basic.Comma))
            .allow_leading()
            .allow_trailing()
            .parse(no_trailing_or_leading_list)
            .unwrap()
        )
        assert result[0] == [
            IntegerLiteral(1),
            IntegerLiteral(2),
            IntegerLiteral(3),
            IntegerLiteral(4),
        ]

    def test_separated_by_allow_trailing_with_trailing(self):
        tokens = lex.tokenize("1, 2, 3, 4,").unwrap()[0]
        result = (
            integer.separated_by(just(Basic.Comma))
            .allow_trailing()
            .parse(tokens)
            .unwrap()
        )
        assert result[0] == [
            IntegerLiteral(1),
            IntegerLiteral(2),
            IntegerLiteral(3),
            IntegerLiteral(4),
        ]

    def test_separated_by_empty(self):
        tokens = lex.tokenize("").unwrap()[0]
        result = integer.separated_by(just(Basic.Comma)).parse(tokens).unwrap()
        assert result[0] == []
