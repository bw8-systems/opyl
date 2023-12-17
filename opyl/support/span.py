from dataclasses import dataclass


@dataclass
class Span:
    start: int
    end: int


@dataclass
class Spanned[ItemType]:
    item: ItemType
    span: Span
