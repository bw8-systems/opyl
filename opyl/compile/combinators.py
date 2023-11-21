import typing as t
from dataclasses import dataclass
from abc import ABC, abstractmethod

from compile import lexemes
from compile import nodes
from compile import errors
from compile.positioning import Stream


@dataclass
class Parser[T](ABC):
    tokens: Stream[lexemes.Token]

    @abstractmethod
    def parse(self) -> T:
        raise NotImplementedError()

    def __call__(self) -> T:
        return self.parse()

    def __or__[U](self, other: "Parser[U] | t.Callable[[], U]") -> "Or[T, U]":
        match other:
            case Parser():
                return Or(self.tokens, self, other)
            case _:
                return Or(self.tokens, self, Lift(self.tokens, other))

    def __ror__[U](self, other: "Parser[U] | t.Callable[[], U]") -> "Parser[T | U]":
        match other:
            case Parser():
                return Or(self.tokens, self, other)
            case _:
                return Or(self.tokens, self, Lift(self.tokens, other))

    @t.overload
    def __and__[U](self, other: "Parser[U] | t.Callable[[], U]") -> "Then[T, U]":
        ...

    @t.overload
    def __and__(self, other: lexemes.PrimitiveKind) -> "Then[T, lexemes.Primitive]":
        ...

    @t.overload
    def __and__(self, other: lexemes.KeywordKind) -> "Then[T, lexemes.Keyword]":
        ...

    def __and__[U](
        self,
        other: "Parser[U] | t.Callable[[], U] | lexemes.PrimitiveKind | lexemes.KeywordKind",
    ) -> "Then[T, U] | Then[T, lexemes.Primitive] | Then[T, lexemes.Keyword]":
        match other:
            case Parser():
                return self.then(other)
            case lexemes.PrimitiveKind():
                return self.then(PrimitiveTerminal(self.tokens, other))
            case lexemes.KeywordKind():
                return self.then(KeywordTerminal(self.tokens, other))
            case _:
                return self.then(Lift(self.tokens, other))

    @t.overload
    def __rand__[U](self, other: "Parser[U] | t.Callable[[], U]") -> "Then[U, T]":
        ...

    @t.overload
    def __rand__(self, other: lexemes.PrimitiveKind) -> "Then[lexemes.Primitive, T]":
        ...

    @t.overload
    def __rand__(self, other: lexemes.KeywordKind) -> "Then[lexemes.Keyword, T]":
        ...

    def __rand__[U](
        self,
        other: "Parser[U] | t.Callable[[], U] | lexemes.PrimitiveKind | lexemes.KeywordKind",
    ) -> "Then[U, T] | Then[lexemes.Primitive, T] | Then[lexemes.Keyword, T]":
        match other:
            case Parser():
                return other.then(self)
            case lexemes.PrimitiveKind():
                return PrimitiveTerminal(self.tokens, other).then(self)
            case lexemes.KeywordKind():
                return KeywordTerminal(self.tokens, other).then(self)
            case _:
                return Lift(self.tokens, other).then(self)

    def then[U](self, second: "Parser[U]") -> "Then[T, U]":
        return Then(tokens=self.tokens, first=self, second=second)

    @t.overload
    def consume[U](self, second: "Parser[U]") -> "Consume[T, U]":
        ...

    @t.overload
    def consume(self, second: lexemes.PrimitiveKind) -> "Consume[T, lexemes.Primitive]":
        ...

    def consume[U](
        self, second: "Parser[U] | lexemes.PrimitiveKind"
    ) -> "Consume[T, U] | Consume[T, lexemes.Primitive]":
        match second:
            case Parser():
                return Consume(tokens=self.tokens, first=self, second=second)
            case _:
                return Consume(
                    tokens=self.tokens,
                    first=self,
                    second=PrimitiveTerminal(self.tokens, second),
                )

    @t.overload
    def __rshift__[U](self, second: "Parser[U]") -> "Consume[T, U]":
        ...

    @t.overload
    def __rshift__(
        self, second: lexemes.PrimitiveKind
    ) -> "Consume[T, lexemes.Primitive]":
        ...

    def __rshift__[U](
        self, second: "Parser[U] | lexemes.PrimitiveKind"
    ) -> "Consume[T, U] | Consume[T, lexemes.Primitive]":
        return self.consume(second)

    @t.overload
    def __rrshift__[U](self, second: "Parser[U]") -> "Consume[T, U]":
        ...

    @t.overload
    def __rrshift__(
        self, second: lexemes.PrimitiveKind
    ) -> "Consume[T, lexemes.Primitive]":
        ...

    def __rrshift__[U](
        self, second: "Parser[U] | lexemes.PrimitiveKind"
    ) -> "Consume[T, U] | Consume[T, lexemes.Primitive]":
        return self.consume(second)

    @t.overload
    def consume_before[U](
        self, second: "Parser[U] | t.Callable[[], U]"
    ) -> "ConsumeBefore[T, U]":
        ...

    @t.overload
    def consume_before(
        self, second: lexemes.PrimitiveKind
    ) -> "ConsumeBefore[T, lexemes.Primitive]":
        ...

    def consume_before[U](
        self, second: "t.Callable[[], U] | Parser[U] | lexemes.PrimitiveKind"
    ) -> "ConsumeBefore[T, U] | ConsumeBefore[T, lexemes.Primitive]":
        match second:
            case Parser():
                return ConsumeBefore(tokens=self.tokens, first=self, second=second)
            case lexemes.PrimitiveKind():
                return ConsumeBefore(
                    tokens=self.tokens,
                    first=self,
                    second=PrimitiveTerminal(self.tokens, second),
                )
            case _:
                return ConsumeBefore(
                    tokens=self.tokens,
                    first=self,
                    second=Lift(tokens=self.tokens, parser=second),
                )

    def repeat(self, lower: int | None = None, upper: int | None = None) -> "Repeat[T]":
        return Repeat(tokens=self.tokens, parser=self, lower=lower, upper=upper)

    def lift[U](self, parser: t.Callable[[], U]) -> "Lift[U]":
        return Lift(tokens=self.tokens, parser=parser)

    def empty(self) -> "Empty":
        return Empty(self.tokens)

    def maybe[U](self, parser: t.Callable[[], U]) -> "Or[U, None]":
        return Lift(self.tokens, parser) | self.empty()


@dataclass
class Lift[T](Parser[T]):
    parser: t.Callable[[], T]

    def parse(self) -> T:
        return self.parser()


@dataclass
class Or[T, U](Parser[T | U]):
    this: Parser[T]
    that: Parser[U]

    def parse(self) -> T | U:
        try:
            # print(self.tokens.stack.index)
            return self.this.parse()
        except errors.ParseException:
            try:
                return self.that.parse()
            except errors.ParseException:
                ...

            return self.that.parse()


@dataclass
class Then[T, U](Parser[tuple[T, U]]):
    first: Parser[T]
    second: Parser[U]

    def parse(self) -> tuple[T, U]:
        return self.first.parse(), self.second.parse()


@dataclass
class Consume[T, U](Parser[T]):
    first: Parser[T]
    second: Parser[U]

    def parse(self) -> T:
        first = self.first.parse()
        self.second.parse()

        return first


@dataclass
class ConsumeBefore[T, U](Parser[U]):
    first: Parser[T]
    second: Parser[U]

    def parse(self) -> U:
        self.first.parse()
        second = self.second.parse()

        return second


@dataclass
class Repeat[T](Parser[list[T]]):
    parser: Parser[T]
    lower: int | None = None
    upper: int | None = None

    def __post_init__(self):
        if self.lower is None:
            self.validated_lower = 0
        else:
            self.validated_lower = self.lower

        assert self.validated_lower > -1
        assert self.upper is None or isinstance(self.upper, int)

        if isinstance(self.upper, int):
            assert self.upper > 0

    def parse(self) -> list[T]:
        items = list[T]()

        while True:
            try:
                item = self.parser.parse()
            except errors.ParseException:
                if len(items) >= self.validated_lower:
                    return items
                raise

            items.append(item)
            if len(items) == self.upper:
                return items

    def extend(self, parser: "Repeat[T]") -> "Extend[T]":
        return Extend(tokens=self.tokens, first=self, second=parser)


class Empty(Parser[None]):
    def parse(self) -> None:
        return None


@dataclass
class List[T, U](Parser[list[T]]):
    item: Parser[T]
    separator: Parser[U] | None = None

    def __post_init__(self):
        if self.separator is None:
            separator = Empty(self.tokens)
        else:
            separator = self.separator

        self.list_parser = (self.item | Empty(self.tokens)).then(
            separator.consume_before(self.item).repeat()
        )

    def parse(self) -> list[T]:
        head, args = self.list_parser.parse()

        if head is not None:
            args.insert(0, head)

        return args


@dataclass
class Extend[T](Parser[list[T]]):
    first: Repeat[T]
    second: Repeat[T]

    def __post_init__(self):
        self.then_parser = self.then(self.second)

    def parse(self) -> list[T]:
        first_list, second_list = self.then_parser.parse()
        return [*first_list, *second_list]


@dataclass
class PrimitiveTerminal(Parser[lexemes.Primitive]):
    terminal: lexemes.PrimitiveKind

    def parse(self) -> lexemes.Primitive:
        peeked = self.tokens.peek()
        if peeked is None:
            raise errors.UnexpectedEOF.instead_of_primitive(self.terminal)

        if not (isinstance(peeked, lexemes.Primitive) and peeked.kind is self.terminal):
            raise errors.UnexpectedToken.instead_of_primitive(peeked, self.terminal)

        if not peeked.kind == self.terminal:
            raise errors.UnexpectedToken.wrong_primitive(
                got=peeked.kind, expected=self.terminal
            )

        self.tokens.advance()
        return peeked


class IdentifierTerminal(Parser[nodes.Identifier]):
    def parse(self) -> nodes.Identifier:
        peeked = self.tokens.peek()

        if peeked is None:
            raise errors.UnexpectedEOF(
                "Unexpected EOF while looking for identifier token."
            )
        if not isinstance(peeked, lexemes.Identifier):
            raise errors.UnexpectedToken.instead_of_identifier(peeked)

        self.tokens.advance()
        return nodes.Identifier(span=peeked.span, name=peeked.identifier)


@dataclass
class KeywordTerminal(Parser[lexemes.Keyword]):
    kind: lexemes.KeywordKind

    def parse(self) -> lexemes.Keyword:
        peeked = self.tokens.peek()

        if peeked is None:
            raise errors.UnexpectedEOF(
                f"Unexpected EOF while looking for keyword {self.kind}."
            )
        if not (isinstance(peeked, lexemes.Keyword) and peeked.kind is self.kind):
            raise errors.UnexpectedToken.instead_of_keyword(peeked, self.kind)

        self.tokens.advance()
        return peeked


@dataclass
class IntegerLiteralTerminal(Parser[nodes.IntegerLiteral]):
    def parse(self) -> nodes.IntegerLiteral:
        peeked = self.tokens.peek()

        if peeked is None:
            raise errors.UnexpectedEOF.instead_of_integer()
        if not isinstance(peeked, lexemes.IntegerLiteral):
            raise errors.UnexpectedToken.instead_of_integer(peeked)

        self.tokens.advance()
        return nodes.IntegerLiteral(span=peeked.span, integer=peeked.integer)
