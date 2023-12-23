import typing as t
from pprint import pprint

from opyl.support.combinator import ParseResult, Parser
from opyl.support.stream import Stream
from opyl.compile.token import Token
from opyl.compile.error import LexError

# TODO: Figure out why these don't work with the expr and parser tests


def panic(message: str) -> t.NoReturn:
    assert False, message


def parse_test(
    parser: Parser[t.Any, t.Any, t.Any], source: str, expected: Token | None
):
    stream = Stream.from_source(source)

    result = parser.parse(stream)
    pprint(f"Parser: {parser}")
    pprint(f"Parsing result: {result}")

    match result:
        case ParseResult.Match(item):
            assert (
                expected is not None
            ), f"Parser produced a match when it wasn't expected to: {item}"
            assert item == expected
        case ParseResult.NoMatch:
            assert (
                expected is None
            ), "Parser did not produce a match when it was expected to."
        case ParseResult.Error() as error:
            panic(f"Parser produced an error when it wasn't expected to: {error}")


def parse_test_err(
    parser: Parser[t.Any, t.Any, t.Any], source: str, expected: LexError
):
    stream = Stream[str].from_source(source)

    match parser.parse(stream):
        case ParseResult.Match(item):
            panic(f"Parser produced a match when it wasn't expected to: {item}")
        case ParseResult.NoMatch:
            panic("Parser did not produce an error when it was expected to.")
        case ParseResult.Error() as error:
            assert error.value == expected
