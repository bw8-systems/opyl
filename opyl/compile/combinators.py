import typing as t
from dataclasses import dataclass
from abc import ABC, abstractmethod

from opyl.compile import lexemes
from opyl.compile.positioning import Stream


@dataclass
class Err[E: Exception]:
    kind: E

    def unwrap(self) -> t.Any:
        raise self.kind


@dataclass
class Ok[T]:
    item: T

    def unwrap(self) -> T:
        return self.item


class ParseException(Exception):
    ...


class UnexpectedEOF(ParseException):
    @classmethod
    def instead_of_primitive(cls, kind: "lexemes.PrimitiveKind") -> t.Self:
        return cls(
            f"Token stream was exhausted while looking for primitive token '{kind.value}'"
        )

    @classmethod
    def instead_of_integer(cls) -> t.Self:
        return cls("Token stream was exhausted while looking for integer literal.")


class UnexpectedToken(ParseException):
    @classmethod
    def instead_of_primitive(
        cls, got: "lexemes.Token", instead_of: "lexemes.PrimitiveKind"
    ) -> t.Self:
        return cls(
            f"Got token {got} while looking for primitive token '{instead_of.value}'"
        )

    @classmethod
    def wrong_primitive(
        cls, got: "lexemes.PrimitiveKind", expected: "lexemes.PrimitiveKind"
    ) -> t.Self:
        return cls(
            f"Got primitive token '{got.value}' while looking for primitive token '{expected.value}'"
        )

    @classmethod
    def instead_of_integer(cls, got: "lexemes.Token") -> t.Self:
        return cls(f"Got token {got} while looking for integer literal.")

    @classmethod
    def instead_of_identifier(cls, got: "lexemes.Token") -> t.Self:
        return cls(f"Got token {got} while looking for identifier token.")

    @classmethod
    def instead_of_keyword(
        cls, got: "lexemes.Token", expected: "lexemes.KeywordKind"
    ) -> t.Self:
        return cls(f"Got token {got} while looking for keyword '{expected}'")


@dataclass
class Parser[T](ABC):
    tokens: Stream[lexemes.Token]

    @abstractmethod
    def parse(self) -> T:
        raise NotImplementedError()

    def __call__(self) -> T:
        return self.parse()

    def __or__[U](self, other: "Parser[U]") -> "Parser[T | U]":
        return Or(self.tokens, self, other)

    def __and__[U](self, other: "Parser[U]") -> "Then[T, U]":
        return self.then(other)

    def then[U](self, second: "Parser[U]") -> "Then[T, U]":
        return Then(tokens=self.tokens, first=self, second=second)

    def consume[U](self, second: "Parser[U]") -> "Consume[T, U]":
        return Consume(tokens=self.tokens, first=self, second=second)

    def consume_before[U](self, second: "Parser[U]") -> "ConsumeBefore[T, U]":
        return ConsumeBefore(tokens=self.tokens, first=self, second=second)

    def repeat(self, lower: int | None = None, upper: int | None = None) -> "Repeat[T]":
        return Repeat(tokens=self.tokens, parser=self, lower=lower, upper=upper)

    def lift[U](self, parser: t.Callable[[], U]) -> "Lift[U]":
        return Lift(tokens=self.tokens, parser=parser)

    def empty(self) -> "Empty":
        return Empty(self.tokens)


@dataclass
class Lift[T](Parser[T]):
    parser: t.Callable[[], T]  # TODO: Should be ParseResult[T]?

    def parse(self) -> T:
        return self.parser()


@dataclass
class Choice[T](Parser[T]):
    choices: tuple[Parser[T], ...]

    def parse(self) -> T:
        for choice in self.choices:
            try:
                return choice.parse()
            except ParseException:
                ...

        raise UnexpectedToken("Did not find expected token from choices.")


@dataclass
class Or[T, U](Parser[T | U]):
    this: Parser[T]
    that: Parser[U]

    def parse(self) -> T | U:
        try:
            return self.this.parse()
        except ParseException:
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
            except ParseException:
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
            raise UnexpectedEOF.instead_of_primitive(self.terminal)

        if not isinstance(peeked, lexemes.Primitive):
            raise UnexpectedToken.instead_of_primitive(peeked, self.terminal)

        if not peeked.kind == self.terminal:
            raise UnexpectedToken.wrong_primitive(
                got=peeked.kind, expected=self.terminal
            )

        self.tokens.advance()
        return peeked


class IdentifierTerminal(Parser[lexemes.Identifier]):
    def parse(self) -> lexemes.Identifier:
        peeked = self.tokens.peek()

        if peeked is None:
            raise UnexpectedEOF("Unexpected EOF while looking for identifier token.")
        if not isinstance(peeked, lexemes.Identifier):
            raise UnexpectedToken.instead_of_identifier(peeked)

        self.tokens.advance()
        return peeked


@dataclass
class KeywordTerminal(Parser[lexemes.Keyword]):
    kind: lexemes.KeywordKind

    def parse(self) -> lexemes.Keyword:
        peeked = self.tokens.peek()

        if peeked is None:
            raise UnexpectedEOF(
                f"Unexpected EOF while looking for keyword {self.kind}."
            )
        if not isinstance(peeked, lexemes.Keyword):
            raise UnexpectedToken.instead_of_keyword(peeked, self.kind)

        self.tokens.advance()
        return peeked


@dataclass
class IntegerLiteralTerminal(Parser[lexemes.IntegerLiteral]):
    def parse(self) -> lexemes.IntegerLiteral:
        peeked = self.tokens.peek()

        if peeked is None:
            raise UnexpectedEOF.instead_of_integer()
        if not isinstance(peeked, lexemes.IntegerLiteral):
            raise UnexpectedToken.instead_of_integer(peeked)

        self.tokens.advance()
        return peeked
