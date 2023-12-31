import typing as t
from dataclasses import dataclass

from opyl.support.union import Maybe
from opyl.support.span import Spanned, Span


@dataclass
class Source:
    text: str
    file: str

    def line(self, index: int) -> str:
        lines = self.text.splitlines()
        return lines[index]


@dataclass
class Stream[ItemType]:
    file_handle: str | None
    spans: list[Spanned[ItemType]]
    position: int = 0

    def __iter__(self) -> t.Generator[Spanned[ItemType], None, None]:
        yield from self.spans

    @staticmethod
    def from_source(source: str, file_handle: str | None = None) -> "Stream[str]":
        return Stream(
            file_handle=file_handle,
            spans=[
                Spanned(item, Span(idx, idx + 1)) for idx, item in enumerate(source)
            ],
        )

    def map[
        NewItemType
    ](self, mapper: t.Callable[[ItemType], NewItemType]) -> "Stream[NewItemType]":
        return Stream(
            file_handle=self.file_handle,
            spans=[
                Spanned(mapper(spanned.item), spanned.span) for spanned in self.spans
            ],
        )

    def remaining(self) -> list[Spanned[ItemType]]:
        return self.spans[self.position :]

    def peek(self) -> Maybe.Type[Spanned[ItemType]]:
        try:
            span = self.spans[self.position]
        except IndexError:
            return Maybe.Nothing
        else:
            return Maybe.Just(span)

    def advance(self, by: int = 1) -> t.Self:
        return self.__class__(
            file_handle=self.file_handle,
            spans=self.spans,
            position=min(self.position + by, len(self.spans)),
        )

    def startswith(self, pattern: t.Sequence[ItemType]) -> bool:
        if len(pattern) == 0:
            return False
        if len(self.spans) < len(pattern):
            return False

        for pat, spanned in zip(pattern, self.spans):
            if spanned.item != pat:
                return False

        return True

    def end(self) -> Span:
        return self.spans[-1].span
