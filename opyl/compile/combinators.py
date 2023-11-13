import typing as t
from dataclasses import dataclass
from abc import ABC, abstractmethod

from . import lexemes
from . import nodes
from . import positioning
from . import errors


type Parser[T] = t.Callable[[], T]


@dataclass
class Combinator[T](ABC):
    stream: positioning.Stream[lexemes.Token]

    @abstractmethod
    def __call__(self) -> T:
        raise NotImplementedError()

    def parse(self) -> T:
        return self()

    def consume(
        self, kind: lexemes.PrimitiveKind | lexemes.KeywordKind
    ) -> "Combinator[T]":
        if isinstance(kind, lexemes.PrimitiveKind):
            return Drop(
                self.stream, parser=self, separator=Primitive(self.stream, kind)
            )
        return Drop(self.stream, parser=self, separator=Keyword(self.stream, kind))

    def consume_then[
        U
    ](self, kind: lexemes.PrimitiveKind, parser: "Combinator[U]") -> "Combinator[U]":
        return DropThen(
            self.stream, parser=parser, separator=Primitive(self.stream, kind)
        )

    def lift[U](self, parser: Parser[U]) -> "Combinator[U]":
        return Lift(stream=self.stream, parser=parser)

    def identifier(self) -> "Combinator[nodes.Identifier]":
        return Identifier(self.stream)

    def primitive(self, kind: lexemes.PrimitiveKind) -> "Combinator[lexemes.Primitive]":
        return Primitive(self.stream, kind)

    def between[
        Start, Stop, InBetween
    ](
        self, start: Parser[Start], stop: Parser[Stop], between: Parser[InBetween]
    ) -> "Combinator[InBetween]":
        return Between(stream=self.stream, start=start, stop=stop, parser=between)

    def also[U](self, this: "Combinator[U]") -> "Combinator[tuple[T, U]]":
        return And(self.stream, self, this)


@dataclass
class Primitive(Combinator[lexemes.Primitive]):
    kind: lexemes.PrimitiveKind

    def __call__(self) -> lexemes.Primitive:
        peeked = self.stream.peek()
        if isinstance(peeked, lexemes.Primitive) and peeked.kind is self.kind:
            self.stream.next()
            return peeked
        raise errors.UnexpectedToken()


@dataclass
class Between[Start, Stop, Between](Combinator[Between]):
    start: Parser[Start]
    stop: Parser[Stop]
    parser: Parser[Between]

    def __call__(self) -> Between:
        self.start()
        between = self.parser()
        self.stop()
        return between


@dataclass
class Drop[T, U](Combinator[T]):
    parser: Combinator[T]
    separator: Combinator[U]

    def __call__(self) -> T:
        item = self.parser()
        self.separator()
        return item


@dataclass
class DropThen[T, U](Combinator[U]):
    separator: Combinator[T]
    parser: Combinator[U]

    def __call__(self) -> U:
        self.separator()
        return self.parser()


@dataclass
class Lift[T](Combinator[T]):
    parser: Parser[T]

    def __call__(self) -> T:
        return self.parser()


@dataclass
class And[T, U](Combinator[tuple[T, U]]):
    first: Combinator[T]
    second: Combinator[U]

    def __call__(self) -> tuple[T, U]:
        return self.first(), self.second()


@dataclass
class Either[T, U](Combinator[T | U]):
    first: Combinator[T]
    second: Combinator[U]

    def __call__(self) -> T | U:
        item = Maybe(self.stream, self.first).parse()
        if item is None:
            return self.second.parse()
        raise errors.ParseError


@dataclass
class Maybe[T](Combinator[T | None]):
    parser: Parser[T]

    def __call__(self) -> T | None:
        try:
            return self.parser()
        except errors.ParseError:
            return None


@dataclass
class Many[T](Combinator[list[T]]):
    parser: Parser[T]

    def __call__(self) -> list[T]:
        optional_parser = Maybe(self.stream, self.parser)
        items = list[T]()

        while True:
            item = optional_parser()
            if item is None:
                break
            items.append(item)

        return items


@dataclass
class Choice[T](Combinator[T]):
    choices: t.Sequence[Parser[T]]

    def __call__(self) -> T:
        for choice in self.choices:
            item = Maybe(self.stream, choice).parse()
            if item is not None:
                return item

        raise errors.UnexpectedToken()


@dataclass
class Keyword(Combinator[lexemes.Keyword]):
    kind: lexemes.KeywordKind

    def __call__(self) -> lexemes.Keyword:
        peeked = self.stream.peek()
        if isinstance(peeked, lexemes.Keyword) and peeked.kind is self.kind:
            self.stream.next()
            return peeked
        raise errors.UnexpectedToken()


class Identifier(Combinator[nodes.Identifier]):
    def __call__(self) -> nodes.Identifier:
        peeked = self.stream.peek()
        if isinstance(peeked, lexemes.Identifier):
            self.stream.next()
            return nodes.Identifier(span=peeked.span, name=peeked.identifier)
        raise errors.UnexpectedToken()


class IntegerLiteral(Combinator[nodes.IntegerLiteral]):
    def __call__(self) -> nodes.IntegerLiteral:
        peeked = self.stream.peek()
        if isinstance(peeked, lexemes.IntegerLiteral):
            self.stream.next()
            return nodes.IntegerLiteral(span=peeked.span, integer=peeked.integer)
        raise errors.UnexpectedToken()
