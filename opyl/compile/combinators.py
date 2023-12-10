import typing as t
from dataclasses import dataclass
from abc import ABC, abstractmethod
import copy

from compile.positioning import Stream, Spanned, Span
from compile import lexemes
from compile.lexemes import (
    Token,
    Primitive,
    PrimitiveKind,
    Keyword,
    KeywordKind,
)
from compile import nodes


class TokenStream(Stream[Token]):
    def span_since(self, since: int) -> Span:
        start = self.tokens[since].span
        stop = self.tokens[self.index - 1].span  # TODO: -1 may not be right here

        return start + stop


class Parse:
    type Result[T] = Match[T] | NoMatch | Errors

    @dataclass
    class Match[T]:
        item: T

    class NoMatch:
        def __eq__(self, other: t.Any) -> bool:
            return isinstance(other, self.__class__)

    @dataclass
    class Errors:
        errors: list[tuple[int, str]]

        @classmethod
        def new(cls, offset: int, message: str) -> t.Self:
            return cls(errors=[(offset, message)])

        def with_new(self, offset: int, message: str) -> t.Self:
            self.errors.append((offset, message))
            return self


class Parser[T](ABC):
    @abstractmethod
    def parse(self, input: TokenStream) -> Parse.Result[T]:
        ...

    def __call__(self, input: TokenStream) -> Parse.Result[T]:
        return self.parse(input)

    def spanned(self) -> "ToSpan[T]":
        return ToSpan(self)

    def alternative[U](self, other: "Parser[U]") -> "Alternative[T, U]":
        return Alternative(self, other)

    def __or__[U](self, other: "Parser[U]") -> "Alternative[T, U]":
        return self.alternative(other)

    def then[U](self, other: "Parser[U]") -> "Then[T, U]":
        return Then(self, other)

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

    def map_with_span[U](self, func: t.Callable[[T], U]) -> "ToSpan[U]":
        return self.map(func).spanned()

    def repeated(self) -> "Repeated[T]":
        return Repeated(self)

    def newlines(self) -> "ThenIgnore[T, list[Primitive]]":
        return self.then_ignore(just(PrimitiveKind.NewLine).repeated())


@dataclass
class ToSpan[T](Parser[Spanned[T]]):
    parser: Parser[T]

    @t.override
    def parse(self, input: TokenStream) -> Parse.Result[Spanned[T]]:
        before = input.save()

        result = self.parser(input)
        if isinstance(result, Parse.Match):
            return Parse.Match(Spanned(result.item, input.span_since(before)))

        return result


@dataclass
class Expect[T](Parser[T]):
    parser: Parser[T]
    message: str

    @t.override
    def parse(self, input: TokenStream) -> Parse.Result[T]:
        saved = input.save()
        match self.parser(input):
            case Parse.Match(item):
                return Parse.Match(item)
            case Parse.NoMatch():
                return Parse.Errors.new(offset=saved, message=self.message)
            case Parse.Errors() as errs:
                return errs.with_new(offset=saved, message=self.message)


@dataclass
class Alternative[T, U](Parser[T | U]):
    first_choice: Parser[T]
    second_choice: Parser[U]

    @t.override
    def parse(self, input: TokenStream) -> Parse.Result[T | U]:
        match self.first_choice(input):
            case Parse.Match(item):
                return Parse.Match(item)
            case Parse.NoMatch():
                ...
            case Parse.Errors() as errors:
                return errors

        match self.second_choice(input):
            case Parse.Match(item):
                return Parse.Match(item)
            case Parse.NoMatch():
                return Parse.NoMatch()
            case Parse.Errors() as errors:
                return errors


@dataclass
class Then[T, U](Parser[tuple[T, U]]):
    first: Parser[T]
    second: Parser[U]

    @t.override
    def parse(self, input: TokenStream) -> Parse.Result[tuple[T, U]]:
        match self.first(input):
            case Parse.Match(item):
                first_item = item
            case errors_or_none:
                return errors_or_none

        match self.second(input):
            case Parse.Match(item):
                second_item = item
            case errors_or_none:
                return errors_or_none

        return Parse.Match((first_item, second_item))


@dataclass
class IgnoreThen[T, U](Parser[U]):
    first: Parser[T]
    second: Parser[U]

    @t.override
    def parse(self, input: TokenStream) -> Parse.Result[U]:
        match self.first(input):
            case Parse.Match():
                ...
            case errors_or_none:
                return errors_or_none

        return self.second(input)


@dataclass
class ThenIgnore[T, U](Parser[T]):
    first: Parser[T]
    second: Parser[U]

    @t.override
    def parse(self, input: TokenStream) -> Parse.Result[T]:
        match self.first(input):
            case Parse.Match(item):
                first_item = item
            case errors_or_none:
                return errors_or_none

        match self.second(input):
            case Parse.Match():
                return Parse.Match(first_item)
            case errors_or_none:
                return errors_or_none


@dataclass
class SeparatedBy[T, U](Parser[list[T]]):
    parser: Parser[T]
    separator: Parser[U]

    _allow_leading: bool = False
    _allow_trailing: bool = False
    _at_least: int = 0

    @t.override
    def parse(self, input: TokenStream) -> Parse.Result[list[T]]:
        items = list[T]()

        while True:
            before_separator = input.save()
            if len(items) == 0 and self._allow_leading:
                match self.separator(input):
                    case Parse.Errors():
                        input.rewind(before_separator)
                    case Parse.NoMatch():
                        input.rewind(before_separator)
                    case _:
                        ...
                    # case Parse.Match():
                    #     if not self._allow_leading:
                    #         input.rewind(before_separator)
                    #         return Parse.NoMatch()

            elif len(items) > 0:
                match self.separator(input):
                    case Parse.Match():
                        ...
                    case Parse.NoMatch() | Parse.Errors() as errors if len(
                        items
                    ) < self._at_least:
                        input.rewind(before_separator)
                        return errors
                        # return Parse.Errors.new(
                        #     before_separator,
                        #     f"Expected {self._at_least} items, got {len(items)}",
                        # )
                    case Parse.NoMatch() | Parse.Errors():
                        input.rewind(before_separator)
                        return Parse.Match(items)

            before_item = input.save()
            match self.parser(input):
                case Parse.Match(item):
                    items.append(item)
                case (Parse.NoMatch() | Parse.Errors()) as errors if len(
                    items
                ) < self._at_least:
                    input.rewind(before_separator)
                    return errors
                case Parse.NoMatch() | Parse.Errors():
                    if self._allow_trailing:
                        input.rewind(before_item)
                    else:
                        input.rewind(before_separator)
                    return Parse.Match(items)

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
class DelimitedBy[T, U, V](Parser[T]):
    parser: Parser[T]
    start: Parser[U]
    end: Parser[V]

    @t.override
    def parse(self, input: TokenStream) -> Parse.Result[T]:
        return (
            self.start.expect("Expected starting delimiter.")
            .ignore_then(self.parser)
            .then_ignore(self.end.expect("Expected ending delimiter"))
            .parse(input)
        )


@dataclass
class OrNot[T](Parser[T | None]):
    parser: Parser[T]

    @t.override
    def parse(self, input: TokenStream) -> Parse.Result[T | None]:
        saved = input.save()

        match self.parser(input):
            case Parse.NoMatch():
                input.rewind(saved)
                return Parse.Match(None)
            case Parse.Errors() as errors:
                return errors
            case Parse.Match(item):
                return Parse.Match(item)


@dataclass
class Map[T, U](Parser[U]):
    parser: Parser[T]
    func: t.Callable[[T], U]

    @t.override
    def parse(self, input: TokenStream) -> Parse.Result[U]:
        match self.parser.parse(input):
            case (Parse.NoMatch() | Parse.Errors()) as err:
                return err
            case Parse.Match(item):
                return Parse.Match(self.func(item))


@dataclass
class Repeated[T](Parser[list[T]]):
    parser: Parser[T]
    _at_least: int = -1

    @t.override
    def parse(self, input: TokenStream) -> Parse.Result[list[T]]:
        items = list[T]()
        while True:
            saved = input.save()
            match self.parser(input):
                case Parse.Match(item):
                    items.append(item)
                case Parse.NoMatch():
                    input.rewind(saved)
                    if len(items) < self._at_least:
                        return Parse.NoMatch()
                    return Parse.Match(items)
                case Parse.Errors() as errors:
                    input.rewind(saved)
                    if len(items) < self._at_least:
                        return errors
                    return Parse.Match(items)

    def at_least(self, minimum: int) -> t.Self:
        other = copy.copy(self)
        other._at_least = minimum
        return other


class IdentifierTerminal(Parser[nodes.Identifier]):
    @t.override
    def parse(self, input: TokenStream) -> Parse.Result[nodes.Identifier]:
        match input.next():
            case lexemes.Identifier() as ident:
                return Parse.Match(nodes.Identifier(name=ident.identifier))
            case _:
                return Parse.NoMatch()


@dataclass
class IntegerLiteralTerminal(Parser[nodes.IntegerLiteral]):
    @t.override
    def parse(self, input: TokenStream) -> Parse.Result[nodes.IntegerLiteral]:
        match input.next():
            case lexemes.IntegerLiteral() as int_lit:
                return Parse.Match(nodes.IntegerLiteral(integer=int_lit.integer))
            case _:
                return Parse.NoMatch()


@dataclass
class PrimitiveTerminal(Parser[Primitive]):
    kind: PrimitiveKind

    @t.override
    def parse(self, input: TokenStream) -> Parse.Result[Primitive]:
        match input.next():
            case Primitive(_, kind) as prim if kind is self.kind:
                return Parse.Match(prim)
            case _:
                return Parse.NoMatch()


@dataclass
class KeywordTerminal(Parser[Keyword]):
    kind: KeywordKind

    @t.override
    def parse(self, input: TokenStream) -> Parse.Result[Keyword]:
        match input.next():
            case Keyword(_, kind) as kw if kind is self.kind:
                return Parse.Match(kw)
            case _:
                return Parse.NoMatch()


ident = IdentifierTerminal()
integer = IntegerLiteralTerminal()
newlines = PrimitiveTerminal(PrimitiveKind.NewLine).repeated()


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


def block[T](parser: Parser[T]) -> DelimitedBy[list[T], Primitive, Primitive]:
    """
    Parse any number of elements separated by >= 1 newline characters between delimiting curly braces.
    """

    return parser.separated_by(
        just(PrimitiveKind.NewLine).repeated().at_least(1)
    ).delimited_by(
        start=just(PrimitiveKind.LeftParenthesis),
        end=just(PrimitiveKind.RightParenthesis),
    )


def parens[T](parser: Parser[T]) -> DelimitedBy[T, Primitive, Primitive]:
    return parser.delimited_by(
        start=just(PrimitiveKind.LeftParenthesis),
        end=just(PrimitiveKind.RightParenthesis),
    )
