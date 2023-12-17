import typing as t
from dataclasses import dataclass

from support.union import Maybe


@dataclass
class Stream[ItemType]:
    items: list[ItemType]
    position: int = 0

    @classmethod
    def from_source(cls, source: str) -> t.Self:
        return cls(list(source))

    def remaining(self) -> list[ItemType]:
        return self.items[self.position :]

    def peek(self) -> Maybe.Type[ItemType]:
        try:
            item = self.items[self.position]
        except IndexError:
            return Maybe.Nothing
        else:
            return Maybe.Just(item)

    def advance(self) -> t.Self:
        return self.__class__(
            items=self.items,
            position=min(self.position + 1, len(self.items)),
        )
