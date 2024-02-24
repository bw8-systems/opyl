import typing as t
from dataclasses import dataclass
from copy import copy
import enum

from opyl.support.span import Span
from opyl.support.stream import Source
from opyl.support.combinator import ParseResult
from opyl.console.color import colors
from opyl.io import file


@dataclass
class TextPosition:
    absolute: int = 0
    line: int = 0
    column: int = 0

    def advance(self, char: str) -> t.Self:
        other = copy(self)
        other.absolute += 1
        other.column += 1

        if char == "\n":
            other.line += 1
            other.column = 0

        return other


def to_location(span: Span, source: str) -> tuple[TextPosition, TextPosition]:
    # Given a start and end index into the source file, return two
    # text positions that give a human readable representation of the location.
    start = TextPosition()

    for char in source[: span.start]:
        start = start.advance(char)

    end = TextPosition()
    for char in source[: span.end]:
        end = end.advance(char)

    return start, end


class LexError(enum.Enum):
    UnexpectedCharacter = "unexpected character"
    UnterminatedStringLiteral = "unterminated string literal"
    UnterminatedCharacterLiteral = "unterminated character literal"
    MalformedHexadecimalIntegerLiteral = "malformed hexadecimal integer literal"
    MalformedDecimalIntegerLiteral = "malformed decimal integer literal"
    MalformedBinaryIntegerLiteral = "malformed binary integer literal"


@dataclass
class ParseError:
    expected: str
    following: str

    def __str__(self) -> str:
        return f"{colors.bold}error: expected '{self.expected}' following {self.following}{colors.reset}"


def format_error(error: ParseError, span: Span, source: Source):
    start, _ = to_location(span, source.text)

    message = f"{colors.bold}{source.file}:{start.line+1}:{start.column}: {colors.red}error:{colors.reset}{colors.bold} expected '{error.expected}' following {error.following}{colors.reset}"
    message += f"\n    {source.line(start.line)}"
    message += (
        "\n    "
        + (start.column - 1) * " "
        + f"{colors.bold}{colors.green}^{colors.reset}"
    )
    message += (
        "\n    "
        + (start.column - 1) * " "
        + f"{colors.bold}{colors.orange}{error.expected}{colors.reset}"
    )

    return message


def report_lex_errors(
    errors: list[ParseResult.Error[LexError]],
    source: Source,
    file: t.TextIO = file.stderr,
):
    for error in errors:
        start, _ = to_location(error.span, source.text)
        message = f"{colors.bold}{source.file}:{start.line+1}:{start.column}: {colors.red}lexical error:{colors.reset}{colors.bold} {error.value.value}{colors.reset}"
        message += f"\n    {source.line(start.line)}"
        message += (
            "\n    "
            + start.column * " "
            + f"{colors.bold}{colors.green}^{colors.reset}"
        )

        print(message, file=file)
