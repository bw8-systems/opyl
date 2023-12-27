import typing as t
from dataclasses import dataclass

from opyl.support.union import Maybe
from opyl.support.span import Spanned, Span, TextPosition


@dataclass
class Stream[ItemType]:
    spans: list[Spanned[ItemType]]
    position: int = 0

    def __iter__(self) -> t.Generator[Spanned[ItemType], None, None]:
        yield from self.spans

    @staticmethod
    def from_source(source: str, file_handle: str | None = None) -> "Stream[str]":
        spans = list[Spanned[str]]()
        line, column = 1, 1
        for idx, char in enumerate(source):
            start = TextPosition(idx, line, column)

            column += 1
            if char == "\n":
                line += 1
                column = 1

            end = TextPosition(idx, line, column)

            spans.append(Spanned(char, Span(file_handle, start, end)))

        return Stream(spans)

    def map[
        NewItemType
    ](self, mapper: t.Callable[[ItemType], NewItemType]) -> "Stream[NewItemType]":
        return Stream(
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
