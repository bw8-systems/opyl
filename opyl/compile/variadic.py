import typing as t
from abc import ABC, abstractmethod
from dataclasses import dataclass


class Parser[T](ABC):
    @abstractmethod
    def parse(self) -> T:
        raise NotImplementedError()

    def __invert__(self) -> "Drop[T]":
        return Drop(self)


class TerminalParser[T](Parser[T]):
    def __or__[U](self, other: "Parser[U]") -> "Or[T, U]":
        return Or(self, other)

    def __and__[U](self, other: "TerminalParser[U]") -> "And[T, U]":
        return And(self, other)


@dataclass
class ConsumeBefore[T, U](Parser[U]):
    drop: Parser[T]
    then: Parser[U]

    @t.override
    def parse(self) -> U:
        self.drop.parse()
        return self.then.parse()


@dataclass
class Drop[T](Parser[T]):
    parser: Parser[T]

    @t.override
    def parse(self) -> T:
        return self.parser.parse()

    def __and__[U](self, other: "TerminalParser[U]") -> "ConsumeBefore[T, U]":
        return ConsumeBefore(self, other)


@dataclass
class Or[T, U](TerminalParser[T | U]):
    left: Parser[T]
    right: Parser[U]

    def parse(self) -> T | U:
        return self.left.parse() or self.right.parse()


@dataclass
class And[T, U](Parser[tuple[T, U]]):
    first: Parser[T]
    second: Parser[U]

    @t.override
    def parse(self) -> tuple[T, U]:
        return (self.first.parse(), self.second.parse())

    def __and__[V](self, other: Parser[V]) -> "Chain[T, U, V]":
        return Chain(self, other)


@dataclass
class Chain[*Ts, T](Parser[tuple[*Ts, T]]):
    front: Parser[tuple[*Ts]]
    last: Parser[T]

    @t.override
    def parse(self) -> tuple[*Ts, T]:
        return (*self.front.parse(), self.last.parse())


class IntTerminal(TerminalParser[int]):
    @t.override
    def parse(self) -> int:
        ...


class StrTerminal(TerminalParser[str]):
    @t.override
    def parse(self) -> str:
        ...


class FloatTerminal(TerminalParser[float]):
    @t.override
    def parse(self) -> float:
        ...


# result = ((IntTerminal() | StrTerminal()) & FloatTerminal()).parse()
result = (~IntTerminal() & StrTerminal()).parse()
