import typing as t
from dataclasses import dataclass


@dataclass
class TextPosition:
    absolute: int = 0
    line: int = 0
    column: int = 0


@dataclass
class Bounds:
    start: TextPosition
    end: TextPosition


@dataclass
class Span:
    file_handle: str | None
    start: TextPosition
    end: TextPosition

    def __add__(self, other: t.Any) -> t.Self:
        if not isinstance(other, Span):
            return NotImplemented

        assert other.file_handle == self.file_handle
        return self.__class__(
            file_handle=self.file_handle,
            start=self.start,
            end=other.end,
        )


@dataclass
class Spanned[Item]:
    item: Item
    span: Span
