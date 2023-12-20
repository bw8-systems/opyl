import typing as t
from dataclasses import dataclass

from opyl.support.union import Maybe


@dataclass
class Stream[ItemType]:
    items: list[ItemType]
    position: int = 0

    @staticmethod
    def from_source(source: str) -> "Stream[str]":
        return Stream(list(source))

    def remaining(self) -> list[ItemType]:
        return self.items[self.position :]

    def peek(self) -> Maybe.Type[ItemType]:
        try:
            item = self.items[self.position]
        except IndexError:
            return Maybe.Nothing
        else:
            return Maybe.Just(item)

    def advance(self, by: int = 1) -> t.Self:
        return self.__class__(
            items=self.items,
            position=min(self.position + by, len(self.items)),
        )

    def startswith(self, pattern: t.Sequence[ItemType]) -> bool:
        if (len(self.items) == 0) or (len(pattern) == 0):
            return False

        for pat, item in zip(pattern, self.items):
            if item != pat:
                return False

        return True
