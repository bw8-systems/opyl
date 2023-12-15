import typing as t
from opyl.compile.lex import (
    Token,
    IntegerLiteral,
    Identifier,
    StringLiteral,
    CharacterLiteral,
    integer,
    identifier,
    string,
    character,
)
from opyl.combinator.combinators import ParseResult, Parser
from opyl.support.streams import Stream


class TestIntegerLiteral:
    def test_empty_integer(self):
        parse_test(integer, "", None)

    def test_single_digit_integer(self):
        parse_test(integer, "5", IntegerLiteral(5))

    def test_multi_digit_integer(self):
        parse_test(integer, "512", IntegerLiteral(512))

    def test_zero_integer(self):
        parse_test(integer, "0", IntegerLiteral(0))

    def test_illegal_integer(self):
        parse_test(
            integer, "05", IntegerLiteral(0)
        )  # TODO: Should be illegal. We'll fix it in post.


class TestIdentifier:
    def test_ident(self):
        parse_test(identifier, "foo", Identifier("foo"))

    def test_empty_ident(self):
        parse_test(identifier, "", None)

    def test_illegal_ident_leading_digit(self):
        parse_test(identifier, "5foo", None)

    def test_ident_underscore(self):
        parse_test(identifier, "_", Identifier("_"))

    def test_ident_leading_underscore(self):
        parse_test(identifier, "_foo", Identifier("_foo"))


class TestStringLiteral:
    def test_string(self):
        parse_test(string, '"foo"', StringLiteral("foo"))

    def test_empty_string(self):
        parse_test(string, '""', StringLiteral(""))

    def test_unterminated_string(self):
        parse_test(string, '"foo', None)

    def test_newline_string(self):
        parse_test(string, '"foo\n"', None)


class TestCharacterLiteral:
    def test_char(self):
        parse_test(character, "'a'", CharacterLiteral("a"))

    def test_long_char(self):
        parse_test(character, "'aa'", None)

    def test_unterminated_char(self):
        parse_test(character, "'a", None)


def panic(message: str) -> t.NoReturn:
    assert False, message


def parse_test(
    parser: Parser[t.Any, t.Any, t.Any], source: str, expected: Token | None
):
    stream = Stream[Token].from_source(source)

    match parser.parse(stream):
        case ParseResult.Match(item):
            assert (
                expected is not None
            ), f"Parser produced a match when it wasn't expected to: {item}"
            assert item == expected
        case ParseResult.NoMatch:
            assert (
                expected is None
            ), "Parser did not produce a match when it was expected to."
        case ParseResult.Error(err):
            panic(f"Parser produced an error when it wasn't expected to: {err}")

# TODO! For verifying errors rather than just Match and NoMatch
def parse_test_err():
    ...