import typing as t
import enum
import textwrap
from dataclasses import dataclass

from opyl.compile.token import Token
from opyl.support.stream import Stream
from opyl.console.color import colors


REPORT = textwrap.dedent(
    f"""
    {colors.white}{colors.bold}{{fname}}:{{ln_no}}:{{col_no}}: {colors.red}error:{colors.white} {{message}}{colors.reset}
        {{line}}
    """
)[1:]


@dataclass
class Message:
    filename: str | None
    line: int
    column: int
    message: str
    excerpt: str

    annotation: tuple[int, str] | None = None

    def __str__(self) -> str:
        base = REPORT.format(
            fname=self.filename,
            ln_no=self.line,
            col_no=self.column,
            message=self.message,
            line=self.excerpt,
        )

        if self.annotation is None:
            extension = ""
        else:
            lines = (
                " " * self.annotation[0] + "^",
                " " * self.annotation[0] + self.annotation[1],
            )
            extension = f"    {lines[0]}\n    {lines[1]}"

        return base + extension

    def add_pointer(self, offset: int, expected: str) -> t.Self:
        self.annotation = (offset, expected)
        return self


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
        return f"expected '{self.expected}' following {self.following}"


def format_error(error: ParseError, remaining: Stream[Token]):
    message = Message(
        filename=remaining.spans[remaining.position].span.file_handle,
        line=remaining.spans[remaining.position].span.start.line,
        column=remaining.spans[remaining.position].span.start.column,
        message=str(error),
        excerpt="",
    )

    return message
