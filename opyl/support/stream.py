import typing as t
from dataclasses import dataclass

from opyl.support.union import Maybe
from opyl.support.span import Spanned, Span


@dataclass
class Source:
    text: str
    file: str


@dataclass
class Stream[ItemType]:
    spans: list[Spanned[ItemType]]
    position: int = 0

    @staticmethod
    def from_source(source: str) -> "Stream[str]":
        return Stream(
            [Spanned(char, Span(idx, idx + 1)) for idx, char in enumerate(source)],
        )

    def map[
        NewItemType
    ](self, mapper: t.Callable[[ItemType], NewItemType]) -> "Stream[NewItemType]":
        return Stream(
            [Spanned(mapper(spanned.item), spanned.span) for spanned in self.spans],
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
