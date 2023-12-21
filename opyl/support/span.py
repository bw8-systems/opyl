import typing as t
from dataclasses import dataclass


@dataclass
class Span:
    start: int
    end: int


@dataclass
class Spanned[Item]:
    item: Item
    span: Span

    @classmethod
    def from_pair(cls, pair: tuple[Item, Span]) -> t.Self:
        return cls(pair[0], pair[1])
