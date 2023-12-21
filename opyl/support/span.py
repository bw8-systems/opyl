from dataclasses import dataclass


@dataclass
class Span:
    start: int
    end: int


@dataclass
class Spanned[Item]:
    item: Item
    span: Span
