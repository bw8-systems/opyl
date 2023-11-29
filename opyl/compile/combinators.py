import typing as t
from dataclasses import dataclass
from abc import ABC, abstractmethod

from compile import lexemes
from compile import nodes
from compile import errors
from compile.positioning import Stream

from compile.lexemes import PrimitiveKind as PK


@dataclass
class Parser[T](ABC):
    tokens: Stream[lexemes.Token]

    @abstractmethod
    def parse(self) -> T:
        raise NotImplementedError()

    def __call__(self) -> T:
        return self.parse()

    def __or__[U](self, second: "Parser[U]") -> "Or[T, U]":
        return Or(self.tokens, self, second)

    def __rshift__[U](self, second: "Parser[U]") -> "Consume[T, U]":
        return Consume(tokens=self.tokens, first=self, second=second)

    def consume_before[U](self, second: "Parser[U]") -> "ConsumeBefore[T, U]":
        return ConsumeBefore(tokens=self.tokens, first=self, second=second)

    def newlines(self):
        return Consume(
            tokens=self.tokens,
            first=self,
            second=Repeat(
                tokens=self.tokens,
                parser=PrimitiveTerminal(tokens=self.tokens, terminal=PK.NewLine),
            ),
        )

    def after_newlines(self):
        return ConsumeBefore(
            tokens=self.tokens,
            first=Repeat(
                tokens=self.tokens,
                parser=PrimitiveTerminal(tokens=self.tokens, terminal=PK.NewLine),
            ),
            second=self,
        )

    def repeat(self, lower: int | None = None, upper: int | None = None) -> "Repeat[T]":
        return Repeat(tokens=self.tokens, parser=self, lower=lower, upper=upper)

    def lift[U](self, parser: "Parser[U]") -> "Lift[U]":
        return Lift(tokens=self.tokens, parser=parser)

    def defer[U](self, parser_factory: t.Callable[[], "Parser[U]"]) -> "Defer[U]":
        return Defer(tokens=self.tokens, parser_factory=parser_factory)

    def empty(self) -> "Empty":
        return Empty(self.tokens)

    def maybe[U](self, target: "Parser[U]") -> "Or[U, None]":
        return target | self.empty()

    def many[U](self, target: "Parser[U]") -> "Repeat[U]":
        return Repeat(
            self.tokens,
            target,
        )

    def into[U](self, transformer: t.Callable[[T], U]) -> "Parser[U]":
        def wrap() -> U:
            return transformer(self.parse())

        return Lift(self.tokens, parser=wrap)

    def list[U, V](
        self, parser: "Parser[U]", *, separated_by: "Parser[V]"
    ) -> "List[U, V]":
        return List(self.tokens, parser, separated_by)


class TerminalParser[T](Parser[T]):
    def __and__[U](self, other: "Parser[U]") -> "And[T, U]":
        return And(self.tokens, self, other)


class NonTerminalParser[T](Parser[T]):
    def __and__[U](self, other: "Parser[U]") -> "And[T, U]":
        return And(self.tokens, self, other)


@dataclass
class Lift[T](Parser[T]):
    parser: t.Callable[[], T]

    @t.override
    def parse(self) -> T:
        return self.parser()


@dataclass
class Defer[T](Parser[T]):
    parser_factory: t.Callable[[], Parser[T]]

    @t.override
    def parse(self) -> T:
        return self.parser_factory().parse()


@dataclass
class Or[T, U](NonTerminalParser[T | U]):
    this: Parser[T]
    that: Parser[U]

    @t.override
    def parse(self) -> T | U:
        try:
            return self.this.parse()
        except errors.ParseException:
            try:
                return self.that.parse()
            except errors.ParseException:
                ...

            return self.that.parse()


@dataclass
class And[T, U](Parser[tuple[T, U]]):
    first: Parser[T]
    second: Parser[U]

    @t.override
    def parse(self) -> tuple[T, U]:
        return self.first.parse(), self.second.parse()

    def __and__[V](self, other: Parser[V]) -> "Chain[T, U, V]":
        return Chain(self.tokens, self, other)


@dataclass
class Chain[*Ts, T](Parser[tuple[*Ts, T]]):
    front: Parser[tuple[*Ts]]
    last: Parser[T]

    @t.override
    def parse(self) -> tuple[*Ts, T]:
        return *self.front.parse(), self.last.parse()

    def __and__[U](self, other: Parser[U]) -> "Chain[*Ts, T, U]":
        return Chain(self.tokens, self, other)


@dataclass
class Consume[T, U](NonTerminalParser[T]):
    first: Parser[T]
    second: Parser[U]

    @t.override
    def parse(self) -> T:
        first = self.first.parse()
        self.second.parse()

        return first


@dataclass
class ConsumeBefore[T, U](NonTerminalParser[U]):
    first: Parser[T]
    second: Parser[U]

    @t.override
    def parse(self) -> U:
        self.first.parse()
        second = self.second.parse()

        return second


@dataclass
class Repeat[T](NonTerminalParser[list[T]]):
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

    @t.override
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

        self.list_parser = (self.item | Empty(self.tokens)) & separator.consume_before(
            self.item
        ).repeat()

    @t.override
    def parse(self) -> list[T]:
        head, args = self.list_parser.parse()

        if head is not None:
            args.insert(0, head)

        return args


@dataclass
class PrimitiveTerminal(TerminalParser[lexemes.Primitive]):
    terminal: lexemes.PrimitiveKind

    @t.override
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


class IdentifierTerminal(TerminalParser[nodes.Identifier]):
    @t.override
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
class KeywordTerminal(TerminalParser[lexemes.Keyword]):
    kind: lexemes.KeywordKind

    @t.override
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
class IntegerLiteralTerminal(TerminalParser[nodes.IntegerLiteral]):
    @t.override
    def parse(self) -> nodes.IntegerLiteral:
        peeked = self.tokens.peek()

        if peeked is None:
            raise errors.UnexpectedEOF.instead_of_integer()
        if not isinstance(peeked, lexemes.IntegerLiteral):
            raise errors.UnexpectedToken.instead_of_integer(peeked)

        self.tokens.advance()
        return nodes.IntegerLiteral(span=peeked.span, integer=peeked.integer)
