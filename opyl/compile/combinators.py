import typing as t
from dataclasses import dataclass
from abc import ABC, abstractmethod
import copy

from compile.positioning import Stream, Spanned, Span
from compile import lexemes
from compile.lexemes import Token, Primitive, PrimitiveKind, Keyword, KeywordKind
from compile import nodes


class TokenStream(Stream[Token]):
    def span_since(self, since: int) -> Span:
        start = self.tokens[since].span
        stop = self.tokens[self.index - 1].span  # TODO: -1 may not be right here

        return start + stop


class ParseException(Exception):
    ...


class NoMatch(ParseException):
    ...


@dataclass
class ParseError(ParseException):
    offset: int
    message: str


type ParseResult[T] = T | NoMatch | ParseError


class Parser[T](ABC):
    @abstractmethod
    def parse(self, input: TokenStream) -> ParseResult[T]:
        ...

    def __call__(self, input: TokenStream) -> ParseResult[T]:
        return self.parse(input)

    def spanned(self) -> "ToSpan[T]":
        return ToSpan(self)

    def alternative[U](self, other: "Parser[U]") -> "Alternative[T, U]":
        return Alternative(self, other)

    def __or__[U](self, other: "Parser[U]") -> "Alternative[T, U]":
        return self.alternative(other)

    def ignore_then[U](self, other: "Parser[U]") -> "IgnoreThen[T, U]":
        return IgnoreThen(self, other)

    def then_ignore[U](self, other: "Parser[U]") -> "ThenIgnore[T, U]":
        return ThenIgnore(self, other)

    def separated_by[U](self, separator: "Parser[U]") -> "SeparatedBy[T, U]":
        return SeparatedBy(self, separator)

    def delimited_by[U, V](
        self,
        start: "Parser[U]",
        end: "Parser[V]",
    ) -> "DelimitedBy[T, U, V]":
        return DelimitedBy(self, start, end)

    def or_not(self) -> "OrNot[T]":
        return OrNot(self)

    def expect(self, message: str) -> "Expect[T]":
        return Expect(self, message)

    def map[U](self, func: t.Callable[[T], U]) -> "Map[T, U]":
        return Map(self, func)


class NonChainingParser[T](Parser[T]):
    def then[U](self, other: Parser[U]) -> "Then[T, U]":
        return Then(self, other)


@dataclass
class ToSpan[T](NonChainingParser[Spanned[T]]):
    parser: Parser[T]

    @t.override
    def parse(self, input: TokenStream) -> ParseResult[Spanned[T]]:
        before = input.save()

        match self.parser(input):
            case NoMatch() | ParseError() as err:
                return err
            case item:
                return Spanned(item, input.span_since(before))


@dataclass
class Expect[T](NonChainingParser[T]):
    parser: Parser[T]
    message: str

    @t.override
    def parse(self, input: TokenStream) -> ParseResult[T]:
        match self.parser(input):
            case NoMatch() | ParseError():
                return ParseError(offset=input.index, message=self.message)
            case item:
                return item


@dataclass
class Alternative[T, U](NonChainingParser[T | U]):
    first_choice: Parser[T]
    second_choice: Parser[U]

    @t.override
    def parse(self, input: TokenStream) -> ParseResult[T | U]:
        match self.first_choice(input):
            case NoMatch() | ParseError():
                return self.second_choice(input)
            case item:
                return item


@dataclass
class Then[T, U](Parser[tuple[T, U]]):
    first: Parser[T]
    second: Parser[U]

    @t.override
    def parse(self, input: TokenStream) -> ParseResult[tuple[T, U]]:
        first_result = self.first(input)
        if isinstance(first_result, (NoMatch, ParseError)):
            return first_result

        second_result = self.second(input)
        if isinstance(second_result, (NoMatch, ParseError)):
            return second_result

        return first_result, second_result

    def then[V](self, other: Parser[V]) -> "Chain[T, U, V]":
        return Chain(self, other)


@dataclass
class Chain[*Ts, T](Parser[tuple[*Ts, T]]):
    all_but_last: Parser[tuple[*Ts]]
    last: Parser[T]

    @t.override
    def parse(self, input: TokenStream) -> ParseResult[tuple[*Ts, T]]:
        first_result = self.all_but_last(input)
        if isinstance(first_result, (NoMatch, ParseError)):
            return first_result

        second_result = self.last(input)
        if isinstance(second_result, (NoMatch, ParseError)):
            return second_result

        return *first_result, second_result

    def then[U](self, other: Parser[U]) -> "Chain[*Ts, T, U]":
        return Chain(self, other)


@dataclass
class IgnoreThen[T, U](NonChainingParser[U]):
    first: Parser[T]
    second: Parser[U]

    @t.override
    def parse(self, input: TokenStream) -> ParseResult[U]:
        first_result = self.first(input)
        if isinstance(first_result, (NoMatch, ParseError)):
            return first_result

        second_result = self.second(input)
        if isinstance(second_result, (NoMatch, ParseError)):
            return second_result

        return second_result


@dataclass
class ThenIgnore[T, U](NonChainingParser[T]):
    first: Parser[T]
    second: Parser[U]

    @t.override
    def parse(self, input: TokenStream) -> ParseResult[T]:
        first_result = self.first(input)
        if isinstance(first_result, (NoMatch, ParseError)):
            return first_result

        second_result = self.second(input)
        if isinstance(second_result, (NoMatch, ParseError)):
            return second_result

        return first_result


@dataclass
class SeparatedBy[T, U](NonChainingParser[list[T]]):
    parser: Parser[T]
    separator: Parser[U]

    _allow_leading: bool = False
    _allow_trailing: bool = False
    _at_least: int = 0

    @t.override
    def parse(self, input: TokenStream) -> ParseResult[list[T]]:
        items = list[T]()

        while True:
            before = input.save()

            match self.separator(input):
                case NoMatch() | ParseError() if len(items) == 0:
                    input.rewind(before)
                case NoMatch() | ParseError() if len(items) != 0:
                    input.rewind(before)
                    if len(items) <= self._at_least:
                        return NoMatch()
                    return items
                case _:
                    if (not self._allow_leading) and (len(items) == 0):
                        return NoMatch()

            before = input.save()

            match self.parser(input):
                case (NoMatch() | ParseError()) as err:
                    if self._allow_trailing:
                        input.rewind(before)
                        return items
                    return err
                case item:
                    items.append(item)

    def allow_leading(self) -> t.Self:
        other = copy.copy(self)
        other._allow_leading = True
        return other

    def allow_trailing(self) -> t.Self:
        other = copy.copy(self)
        other._allow_trailing = True
        return other

    def at_least(self, minimum: int) -> t.Self:
        other = copy.copy(self)
        other._at_least = minimum
        return other


@dataclass
class DelimitedBy[T, U, V](NonChainingParser[T]):
    parser: Parser[T]
    start: Parser[U]
    end: Parser[V]

    @t.override
    def parse(self, input: TokenStream) -> ParseResult[T]:
        start_result = self.start(input)
        if isinstance(start_result, (NoMatch, ParseError)):
            return start_result

        parsed_result = self.parser(input)
        if isinstance(parsed_result, (NoMatch, ParseError)):
            return parsed_result

        end_result = self.end(input)
        if isinstance(end_result, (NoMatch, ParseError)):
            return end_result

        return parsed_result


@dataclass
class OrNot[T](NonChainingParser[T | None]):
    parser: Parser[T]

    @t.override
    def parse(self, input: TokenStream) -> ParseResult[T | None]:
        saved = input.save()
        match self.parser(input):
            case NoMatch() | ParseError():
                input.rewind(saved)
                return None
            case item:
                return item


@dataclass
class Map[T, U](NonChainingParser[U]):
    parser: Parser[T]
    func: t.Callable[[T], U]

    @t.override
    def parse(self, input: TokenStream) -> ParseResult[U]:
        match self.parser.parse(input):
            case (NoMatch() | ParseError()) as err:
                return err
            case item:
                return self.func(item)


class IdentifierTerminal(NonChainingParser[nodes.Identifier]):
    @t.override
    def parse(self, input: TokenStream) -> ParseResult[nodes.Identifier]:
        maybe_next = input.next()

        if maybe_next is None:
            return NoMatch()

        if isinstance(maybe_next, lexemes.Identifier):
            return nodes.Identifier(maybe_next.span, maybe_next.identifier)

        return NoMatch()


@dataclass
class PrimitiveTerminal(NonChainingParser[Primitive]):
    kind: PrimitiveKind

    @t.override
    def parse(self, input: TokenStream) -> ParseResult[Primitive]:
        maybe_next = input.next()
        if maybe_next is None:
            return NoMatch()

        if isinstance(maybe_next, Primitive) and maybe_next.kind is self.kind:
            return maybe_next

        return NoMatch()


@dataclass
class KeywordTerminal(NonChainingParser[Keyword]):
    kind: KeywordKind

    @t.override
    def parse(self, input: TokenStream) -> ParseResult[Keyword]:
        maybe_next = input.next()
        if maybe_next is None:
            return NoMatch()

        if isinstance(maybe_next, Keyword) and maybe_next.kind is self.kind:
            return maybe_next

        return NoMatch()


ident = IdentifierTerminal()


@t.overload
def just(kind: PrimitiveKind) -> PrimitiveTerminal:
    ...


@t.overload
def just(kind: KeywordKind) -> KeywordTerminal:
    ...


def just(kind: PrimitiveKind | KeywordKind) -> PrimitiveTerminal | KeywordTerminal:
    if isinstance(kind, PrimitiveKind):
        return PrimitiveTerminal(kind)
    return KeywordTerminal(kind)


def block[T](parser: Parser[T]) -> DelimitedBy[T, Primitive, Primitive]:
    return parser.delimited_by(
        start=just(PrimitiveKind.LeftBrace), end=just(PrimitiveKind.RightBrace)
    )


def parens[T](parser: Parser[T]) -> DelimitedBy[T, Primitive, Primitive]:
    return parser.delimited_by(
        start=just(PrimitiveKind.LeftParenthesis),
        end=just(PrimitiveKind.RightParenthesis),
    )


def lines[T](parser: Parser[T]) -> SeparatedBy[T, Primitive]:
    return (
        parser.separated_by(just(PrimitiveKind.NewLine))
        .allow_leading()
        .allow_trailing()
    )
