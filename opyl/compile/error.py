import typing as t
import enum
from dataclasses import dataclass
from copy import copy

from opyl.support.span import Span


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
    IllegalCharacter = enum.auto()
    UnexpectedCharacter = enum.auto()
    UnterminatedStringLiteral = enum.auto()
    UnterminatedCharacterLiteral = enum.auto()
    MalformedIntegerLiteral = enum.auto()


@dataclass
class ParseError:
    expected: str
    following: str

    def __str__(self) -> str:
        return f"Error: Expected {self.expected} following {self.following}"


def format_error(error: ParseError, span: Span, source: str):
    start, end = to_location(span, source)

    if start.line == end.line:
        return f"ln {start.line}:{start.column}..{end.column}: {error}"
    else:
        return f"ln {start.line}..{end.line}:{end.column}: {error}"
