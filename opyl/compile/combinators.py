import typing as t
from dataclasses import dataclass
from abc import ABC, abstractmethod
from functools import singledispatchmethod

from . import tokens
from . import nodes
from . import stream
from . import errors


type Parser[T] = t.Callable[[], T]


def parse[T](parser: Parser[T]) -> T:
    return parser()


@dataclass
class Combinator[T](ABC):
    stream: stream.Stream[tokens.Token]

    @abstractmethod
    def __call__(self) -> T:
        raise NotImplementedError()

    @singledispatchmethod
    def followed_by(self, _separator: t.Any) -> "Combinator[T]":
        raise NotImplementedError

    @followed_by.register
    def _[U](self, separator: Parser[U]) -> "Combinator[T]":
        def wrapper() -> T:
            item = self()
            separator()
            return item

        return Lift(wrapper)

    @followed_by.register
    def _[U](self, kind: tokens.PrimitiveKind) -> "Combinator[T]":
        def wrapper() -> T:
            item = self()
            sep_parser = Primitive(self.stream, kind)
            sep_parser()
            return item

        return Lift(wrapper)

    def then[U](self, then: Parser[U]) -> "Combinator[U]":
        def wrapper() -> U:
            self()
            return then()

        return Lift(wrapper)

    def and_also[U](self, this: Parser[U]) -> "Combinator[tuple[T, U]]":
        def wrapper() -> tuple[T, U]:
            return self(), this()

        return Lift(wrapper)


@dataclass
class Lift[T](Combinator[T]):
    # Overriding __init__ to drop the stream parameter
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


class Identifier(Combinator[nodes.Identifier]):
    def __call__(self) -> nodes.Identifier:
        ZeroOrMore(self.stream, Whitespace(self.stream))()

        peeked = self.stream.peek()
        if isinstance(peeked, tokens.Identifier):
            self.stream.next()
            return nodes.Identifier(span=peeked.span, name=peeked.identifier)
        raise errors.UnexpectedToken()


class IntegerLiteral(Combinator[nodes.IntegerLiteral]):
    def __call__(self) -> nodes.IntegerLiteral:
        ZeroOrMore(self.stream, Whitespace(self.stream))()

        peeked = self.stream.peek()
        if isinstance(peeked, tokens.IntegerLiteral):
            self.stream.next()
            return nodes.IntegerLiteral(span=peeked.span, integer=peeked.integer)
        raise errors.UnexpectedToken()


@dataclass
class Primitive(Combinator[tokens.Primitive]):
    kind: tokens.PrimitiveKind

    def __call__(self) -> tokens.Primitive:
        parse(ZeroOrMore(self.stream, Whitespace(self.stream)))

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


@dataclass
class Between[Open, Close, Between](Combinator[tuple[Open, Close, Between]]):
    open: Parser[Open]
    close: Parser[Close]
    between: Parser[Between]

    def __call__(self) -> tuple[Open, Close, Between]:
        return self.open(), self.close(), self.between()


@dataclass
class Either[Left, Right](Combinator[Left | Right]):
    left: Parser[Left]
    right: Parser[Right]

    def __call__(self) -> Left | Right:
        left_or_none = parse(OneOrNone(self.stream, self.left))
        if left_or_none is not None:
            return left_or_none

        return parse(self.right)


@dataclass
class ManyEither[Left, Right](Combinator[tuple[list[Left], list[Right]]]):
    left: Parser[Left]
    right: Parser[Right]
    filter: t.Callable[[t.Any], t.TypeGuard[Left]]

    def __post_init__(self):
        self.parser = OneOrNone(
            stream=self.stream,
            parser=Either(
                stream=self.stream,
                left=self.left,
                right=self.right,
            ),
        )

    # This song and dance is being done because Pyright is not able to
    # properly type narrow to Right in __call__ despite excluding None
    # and excluding Left.
    def anti_filter(self, item: Left | Right) -> t.TypeGuard[Right]:
        return not self.filter(item)

    def __call__(self) -> tuple[list[Left], list[Right]]:
        lefts = list[Left]()
        rights = list[Right]()

        maybe_item = self.parser()

        while maybe_item is not None:
            if self.filter(maybe_item):
                lefts.append(maybe_item)
            if self.anti_filter(maybe_item):
                rights.append(maybe_item)

            maybe_item = self.parser()

        return lefts, rights


# class OneOrMoreOfEither[Left, Right](Combinator[tuple[list[Left], list[Right]]]):
#     left: Parser[Left]
#     right: Parser[Right]
#     filter: t.Callable[[t.Any], t.TypeGuard[Left]]

#     def __post_init__(self):
#         self.parser = OneOrMore(
#             stream=self.stream,
#             parser=Either(
#                 stream=self.stream,
#                 left=self.left,
#                 right=self.right,
#             ),
#         )

#     def __call__(self) -> tuple[list[Left], list[Right]]:
#         item = self.parser()


@dataclass
class Choice[T](Combinator[T]):
    choices: tuple[Parser[T], ...]

    def __call__(self) -> T:
        for choice in self.choices:
            item = parse(OneOrNone(self.stream, choice))
            if item is not None:
                return item

        raise errors.UnexpectedToken()


@dataclass
class BaseTokenParser:
    stream: stream.Stream[tokens.Token]

    def __post_init__(self):
        self.primitive = {
            kind: Primitive(self.stream, kind) for kind in tokens.PrimitiveKind
        }
        self.keyword = {kind: Keyword(self.stream, kind) for kind in tokens.KeywordKind}

        self.identifier = Identifier(self.stream)
        self.integer = IntegerLiteral(self.stream)
        self.whitespace = Whitespace(self.stream)

    def one_or_none[T](self, parser: Parser[T]) -> OneOrNone[T | None]:
        return OneOrNone(stream=self.stream, parser=parser)

    def one_or_more[T](self, parser: Parser[T]) -> OneOrMore[T]:
        return OneOrMore(stream=self.stream, parser=parser)

    def zero_or_more[T](self, parser: Parser[T]) -> ZeroOrMore[T]:
        return ZeroOrMore(stream=self.stream, parser=parser)

    def between[Open, Close, InBetween](
        self, open: Parser[Open], close: Parser[Close], between: Parser[InBetween]
    ) -> Between[Open, Close, InBetween]:
        return Between(stream=self.stream, open=open, close=close, between=between)

    def between_pair[InBetween](
        self, pair: tokens.GroupingPair, between: Parser[InBetween]
    ) -> Between[tokens.Primitive, tokens.Primitive, InBetween]:
        open, close = pair.value

        return self.between(
            open=self.primitive[open], close=self.primitive[close], between=between
        )

    def either[Left, Right](
        self, left: Parser[Left], right: Parser[Right]
    ) -> Combinator[Left | Right]:
        return Either(stream=self.stream, left=left, right=right)

    def many_either[Left, Right](
        self,
        left: Parser[Left],
        right: Parser[Right],
        filter: t.Callable[[t.Any], t.TypeGuard[Left]],
    ) -> ManyEither[Left, Right]:
        return ManyEither(stream=self.stream, left=left, right=right, filter=filter)

    def choice[T](self, choices: tuple[Parser[T], ...]) -> Combinator[T]:
        return Choice(stream=self.stream, choices=choices)
