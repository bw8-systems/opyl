import typing as t
import contextlib
import dataclasses

from . import errors


@dataclasses.dataclass
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

    def increment(self, newline: bool) -> t.Self:
        return TextPosition(
            absolute=self.absolute + 1,
            line=self.line + 1 if newline else self.line,
            column=0 if newline else self.column + 1,
        )

    @staticmethod
    def default() -> "TextPosition":
        return TextPosition(0, 0, 0)


@dataclasses.dataclass
class Span:
    start: TextPosition
    stop: TextPosition

    def __add__(self, other: "Span") -> "Span":
        return Span(
            start=self.start,
            stop=other.stop,
        )


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
        return "\0"

    def startswith(self, pattern: str) -> bool:
        return self.text.startswith(pattern)


@dataclasses.dataclass
class Stack:
    index: int = 0

    def __post_init__(self):
        self.stack = list[int]()

    def push(self):
        self.stack.append(self.index)

    def drop(self) -> int:
        try:
            return self.stack.pop()
        except IndexError:
            raise RuntimeError  # TODO: What kind of error is this?

    def pop(self):
        self.index = self.drop()


# TODO: Combine with TextStream class
class Stream[T]:
    def __init__(self, stream: t.Sequence[T]):
        self.stack = Stack()
        self.stream = stream

    def peek(self) -> T | None:
        try:
            return self.stream[self.stack.index]
        except IndexError:
            return None

    def increment(self) -> None:
        self.stack.index += 1

    def next(self) -> T:
        maybe = self.peek()
        if maybe is None:
            raise errors.UnexpectedEOF()

        # Pyright has narrowed from T | None to T via conditional above.
        # Renaming for semantic clarity.
        peeked = maybe

        self.increment()
        return peeked
