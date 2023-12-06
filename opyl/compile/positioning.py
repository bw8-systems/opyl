import contextlib
from dataclasses import dataclass


@dataclass
class TextPosition:
    absolute: int = 0
    line: int = 0
    column: int = 0

    def copy(self) -> "TextPosition":
        return TextPosition(
            absolute=self.absolute,
            line=self.line,
            column=self.column,
        )

    def increment(self, newline: bool) -> "TextPosition":
        return TextPosition(
            absolute=self.absolute + 1,
            line=self.line + 1 if newline else self.line,
            column=0 if newline else self.column + 1,
        )

    @staticmethod
    def default() -> "TextPosition":
        return TextPosition(0, 0, 0)


@dataclass
class Span:
    start: TextPosition
    stop: TextPosition

    def __add__(self, other: "Span") -> "Span":
        return Span(
            start=self.start,
            stop=other.stop,
        )

    @staticmethod
    def default() -> "Span":
        return Span(start=TextPosition.default(), stop=TextPosition.default())


@dataclass
class Spanned[T]:
    item: T
    span: Span


class TextStream:
    def __init__(self, text: str):
        self.text = text
        self.index = TextPosition(0, 0, 0)

    def __iter__(self):
        for char in self.text[self.index.absolute :]:
            yield char

    def advance(self, *, newline: bool):
        self.index.absolute += 1
        if newline:
            self.index.line += 1
            self.index.column = 0
        else:
            self.index.column += 1

    def advance_for(self, pattern: str):
        for char in pattern:
            self.advance(newline=char == "\n")

    def current(self) -> str:
        with contextlib.suppress(IndexError):
            return self.text[self.index.absolute]
        return ""

    def startswith(self, pattern: str) -> bool:
        return self.text[self.index.absolute :].startswith(pattern)


@dataclass
class Stream[T]:
    tokens: list[T]
    index: int = 0

    def save(self) -> int:
        return self.index

    def rewind(self, index: int):
        self.index = index

    def next(self) -> T | None:
        if self.index >= len(self.tokens):
            return None

        item = self.tokens[self.index]
        self.index += 1
        return item
