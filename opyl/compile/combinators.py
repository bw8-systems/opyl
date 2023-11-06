import typing as t
from dataclasses import dataclass
from abc import ABC, abstractmethod

from . import tokens
from . import stream
from . import errors


type Parser[T] = t.Callable[[], T]


@dataclass
class Combinator[T](ABC):
    stream: stream.Stream[tokens.Token]

    @abstractmethod
    def __call__(self) -> T:
        raise NotImplementedError()

    def then_[U](self, then: Parser[U]) -> "Combinator[U]":
        class Wrapper(Combinator[U]):
            def __call__(self) -> U:
                self()
                return then()

        return Wrapper(self.stream)

    def then[U](self, then: Parser[U]) -> "Combinator[T]":
        class Wrapper(Combinator[T]):
            def __call__(self) -> T:
                parsed = self()
                then()
                return parsed

        return Wrapper(self.stream)

    def parse(self) -> T:
        return self()


@dataclass
class ParserWrapper[T](Combinator[T]):
    def __init__(self, parser: Parser[T]):
        self.parser = parser

    def __call__(self) -> T:
        return self.parser()


@dataclass
class OneOrNone[T](Combinator[T | None]):
    parser: Parser[T]

    def __call__(self) -> T | None:
        try:
            return self.parser()
        except errors.ParseError:
            return None


@dataclass
class ZeroOrMore[T](Combinator[list[T]]):
    parser: Parser[T]

    def __call__(self) -> list[T]:
        one_or_none = OneOrNone(self.stream, self.parser)
        items = list[T]()

        while True:
            item = one_or_none()
            if item is None:
                break

            items.append(item)

        return items


@dataclass
class OneOrMore[T](Combinator[list[T]]):
    parser: Parser[T]

    def __call__(self) -> list[T]:
        zero_or_more = ZeroOrMore(self.stream, self.parser)
        items = [self.parser()]
        items.extend(zero_or_more())
        return items


class Whitespace(Combinator[tokens.Whitespace]):
    def __call__(self) -> tokens.Whitespace:
        peeked = self.stream.peek()
        if isinstance(peeked, tokens.Whitespace):
            self.stream.next()
            return peeked
        raise errors.UnexpectedToken()


class Identifier(Combinator[tokens.Identifier]):
    def __call__(self) -> tokens.Identifier:
        ZeroOrMore(self.stream, Whitespace(self.stream))()

        peeked = self.stream.peek()
        if isinstance(peeked, tokens.Identifier):
            self.stream.next()
            return peeked
        raise errors.UnexpectedToken()


class IntegerLiteral(Combinator[tokens.IntegerLiteral]):
    def __call__(self) -> tokens.IntegerLiteral:
        ZeroOrMore(self.stream, Whitespace(self.stream))()

        peeked = self.stream.peek()
        if isinstance(peeked, tokens.IntegerLiteral):
            self.stream.next()
            return peeked
        raise errors.UnexpectedToken()


@dataclass
class Primitive(Combinator[tokens.Primitive]):
    kind: tokens.PrimitiveKind

    def __call__(self) -> tokens.Primitive:
        ZeroOrMore(self.stream, Whitespace(self.stream))()

        peeked = self.stream.peek()
        if isinstance(peeked, tokens.Primitive) and peeked.kind is self.kind:
            self.stream.next()
            return peeked
        raise errors.UnexpectedToken()


@dataclass
class Keyword(Combinator[tokens.Keyword]):
    kind: tokens.KeywordKind

    def __call__(self) -> tokens.Keyword:
        ZeroOrMore(self.stream, Whitespace(self.stream))()

        peeked = self.stream.peek()
        if isinstance(peeked, tokens.Keyword) and peeked.kind is self.kind:
            self.stream.next()
            return peeked
        raise errors.UnexpectedToken()


class Between[Open, Close, Between](Combinator[tuple[Open, Close, Between]]):
    def __init__(
        self, open: Parser[Open], close: Parser[Close], between: Parser[Between]
    ):
        self.open = open
        self.close = close
        self.between = between

    def __call__(self) -> tuple[Open, Close, Between]:
        return self.open(), self.close(), self.between()
