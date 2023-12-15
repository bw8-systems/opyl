import typing as t
from dataclasses import dataclass
from abc import ABC, abstractmethod
import copy
from collections.abc import Sequence

from compile.positioning import Stream, Spanned
from compile import lexemes
from compile.lexemes import (
    Token,
    Primitive,
    PrimitiveKind,
    Keyword,
    KeywordKind,
)
from compile import nodes


class Parse:
    type Result[T] = Match[T] | NoMatch | Errors

    @dataclass
    class Match[T]:
        item: T

    @dataclass
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


# TODO: Rename to something more agnostic for use in lexer.
class Parser[I, T](ABC):
    @abstractmethod
    def parse(self, input: Stream[I]) -> Parse.Result[T]:
        raise NotImplementedError()

    def __call__(self, input: Stream[I]) -> Parse.Result[T]:
        return self.parse(input)

    def spanned(self) -> "ToSpan[I, T]":
        return ToSpan(self)

    def alternative[U](self, other: "Parser[I, U]") -> "Alternative[I, T, U]":
        return Alternative(self, other)

    def __or__[U](self, other: "Parser[I, U]") -> "Alternative[I, T, U]":
        return self.alternative(other)

    def then[U](self, other: "Parser[I, U]") -> "Then[I, T, U]":
        return Then(self, other)

    def ignore_then[U](self, other: "Parser[I, U]") -> "IgnoreThen[I, T, U]":
        return IgnoreThen(self, other)

    def then_ignore[U](self, other: "Parser[I, U]") -> "ThenIgnore[I, T, U]":
        return ThenIgnore(self, other)

    def separated_by[U](self, separator: "Parser[I, U]") -> "SeparatedBy[I, T, U]":
        return SeparatedBy(self, separator)

    def delimited_by[
        U, V
    ](self, start: "Parser[I, U]", end: "Parser[I, V]",) -> "DelimitedBy[I, T, U, V]":
        return DelimitedBy(self, start, end)

    def or_not(self) -> "OrNot[I, T]":
        return OrNot(self)

    def or_else(self, default: T) -> "OrElse[I, T]":
        return OrElse(self, default)

    def expect(self, message: str) -> "Expect[I, T]":
        return Expect(self, message)

    def map[U](self, func: t.Callable[[T], U]) -> "Map[I, T, U]":
        return Map(self, func)

    def and_check(self, pred: t.Callable[[T], bool]) -> "AndCheck[I, T]":
        return AndCheck(self, pred)

    def chain(
        self, other: "Parser[I, list[T]]"
    ) -> "Map[I, tuple[T, list[T]], list[T]]":
        return self.then(other).map(lambda a_b: [a_b[0], *a_b[1]])

    def map_with_span[
        U
    ](self: "Parser[Token, T]", func: t.Callable[[T], U]) -> "ToSpan[U]":
        return self.map(func).spanned()

    def repeated(self) -> "Repeated[I, T]":
        return Repeated(self)

    # TODO: Move out of this class since its specialized on Token streams.
    def newlines(self: "Parser[Token, T]") -> "ThenIgnore[Token, T, list[Primitive]]":
        return self.then_ignore(just(PrimitiveKind.NewLine).repeated())


@dataclass
class ToSpan[I, T](Parser[I, Spanned[T]]):
    parser: Parser[I, T]

    @t.override
    def parse(self, input: Stream[I]) -> Parse.Result[Spanned[T]]:
        before = input.save()

        result = self.parser(input)
        if isinstance(result, Parse.Match):
            return Parse.Match(Spanned(result.item, input.span_since(since=before)))

        return result


@dataclass
class Expect[I, T](Parser[I, T]):
    parser: Parser[I, T]
    message: str

    @t.override
    def parse(self, input: Stream[I]) -> Parse.Result[T]:
        saved = input.save()
        match self.parser(input):
            case Parse.Match(item):
                return Parse.Match(item)
            case Parse.NoMatch():
                return Parse.Errors.new(offset=saved, message=self.message)
            case Parse.Errors() as errs:
                return errs.with_new(offset=saved, message=self.message)


@dataclass
class Alternative[I, T, U](Parser[I, T | U]):
    first_choice: Parser[I, T]
    second_choice: Parser[I, U]

    @t.override
    def parse(self, input: Stream[I]) -> Parse.Result[T | U]:
        saved = input.save()

        match self.first_choice(input):
            case Parse.Match(item):
                return Parse.Match(item)
            case Parse.NoMatch():
                input.rewind(saved)
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
class Then[I, T, U](Parser[I, tuple[T, U]]):
    first: Parser[I, T]
    second: Parser[I, U]

    @t.override
    def parse(self, input: Stream[I]) -> Parse.Result[tuple[T, U]]:
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
class IgnoreThen[I, T, U](Parser[I, U]):
    first: Parser[I, T]
    second: Parser[I, U]

    @t.override
    def parse(self, input: Stream[I]) -> Parse.Result[U]:
        match self.first(input):
            case Parse.Match():
                ...
            case errors_or_none:
                return errors_or_none

        return self.second(input)


@dataclass
class ThenIgnore[I, T, U](Parser[I, T]):
    first: Parser[I, T]
    second: Parser[I, U]

    @t.override
    def parse(self, input: Stream[I]) -> Parse.Result[T]:
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
class SeparatedBy[I, T, U](Parser[I, list[T]]):
    parser: Parser[I, T]
    separator: Parser[I, U]

    _allow_leading: bool = False
    _allow_trailing: bool = False
    _at_least: int = 0

    @t.override
    def parse(self, input: Stream[I]) -> Parse.Result[list[T]]:
        items = list[T]()

        before_separator = input.save()

        if self._allow_leading:
            match self.separator(input):
                case Parse.Match():
                    ...
                case Parse.NoMatch():
                    input.rewind(before_separator)
                case Parse.Errors() as errors:
                    return errors

        before_item = input.save()

        match self.parser(input):
            case Parse.Match(item):
                items.append(item)
            case Parse.NoMatch():
                if len(items) < self._at_least:
                    return Parse.NoMatch()
                return Parse.Match(items)
            case Parse.Errors() as errors:
                input.rewind(before_item)
                if len(items) < self._at_least:
                    return errors
                return Parse.Match(items)

        while True:
            before_separator = input.save()
            match self.separator(input):
                case Parse.Match():
                    ...
                case Parse.NoMatch():
                    input.rewind(before_separator)
                    break
                case Parse.Errors() as errors:
                    return errors

            after_separator = input.save()

            match self.parser(input):
                case Parse.Match(item):
                    items.append(item)
                case Parse.NoMatch():
                    if self._allow_trailing:
                        input.rewind(after_separator)
                    break
                case Parse.Errors() as errors:
                    if self._allow_trailing:
                        input.rewind(after_separator)
                        break

                    return errors

        if len(items) < self._at_least:
            return Parse.NoMatch()
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
class DelimitedBy[I, T, U, V](Parser[I, T]):
    parser: Parser[I, T]
    start: Parser[I, U]
    end: Parser[I, V]

    @t.override
    def parse(self, input: Stream[I]) -> Parse.Result[T]:
        return (
            self.start.expect("Expected starting delimiter.")
            .ignore_then(self.parser)
            .then_ignore(self.end.expect("Expected ending delimiter"))
            .parse(input)
        )


@dataclass
class OrNot[I, T](Parser[I, T | None]):
    parser: Parser[I, T]

    @t.override
    def parse(self, input: Stream[I]) -> Parse.Result[T | None]:
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
class OrElse[I, T](Parser[I, T]):
    parser: Parser[I, T]
    default: T

    @t.override
    def parse(self, input: Stream[I]) -> Parse.Result[T]:
        saved = input.save()

        match self.parser(input):
            case Parse.NoMatch():
                input.rewind(saved)
                return Parse.Match(self.default)
            case Parse.Errors() as errors:
                return errors
            case Parse.Match(item):
                return Parse.Match(item)


@dataclass
class Map[I, T, U](Parser[I, U]):
    parser: Parser[I, T]
    func: t.Callable[[T], U]

    @t.override
    def parse(self, input: Stream[I]) -> Parse.Result[U]:
        match self.parser.parse(input):
            case (Parse.NoMatch() | Parse.Errors()) as err:
                return err
            case Parse.Match(item):
                return Parse.Match(self.func(item))


@dataclass
class Filter[I](Parser[I, I]):
    func: t.Callable[[I], bool]

    @t.override
    def parse(self, input: Stream[I]) -> Parse.Result[I]:
        next_item = input.next()
        if next_item is None:
            return Parse.NoMatch()

        if self.func(next_item):
            return Parse.Match(next_item)

        return Parse.NoMatch()


@dataclass
class AndCheck[I, T](Parser[I, T]):
    parser: Parser[I, T]
    predicate: t.Callable[[T], bool]

    @t.override
    def parse(self, input: Stream[I]) -> Parse.Result[T]:
        match self.parser(input):
            case Parse.Match(item):
                if self.predicate(item):
                    return Parse.Match(item)
                return Parse.NoMatch()
            case Parse.NoMatch():
                return Parse.NoMatch()
            case Parse.Errors() as errors:
                return errors


@dataclass
class Repeated[I, T](Parser[I, list[T]]):
    parser: Parser[I, T]

    _at_least: int = -1

    @t.override
    def parse(self, input: Stream[I]) -> Parse.Result[list[T]]:
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
                    return errors

    def at_least(self, minimum: int) -> t.Self:
        other = copy.copy(self)
        other._at_least = minimum
        return other


@dataclass
class OneOf[I](Parser[I, I]):
    choices: t.Sequence[I]

    @t.override
    def parse(self, input: Stream[I]) -> Parse.Result[I]:
        match input.next():
            case None:
                return Parse.NoMatch()
            case item if item in self.choices:
                return Parse.Match(item)
            case _:
                return Parse.NoMatch()


def filter[I](func: t.Callable[[I], bool]) -> Filter[I]:
    return Filter(func)


def one_of[I](choices: t.Sequence[I]) -> OneOf[I]:
    return OneOf(choices)


class IdentifierTerminal(Parser[Token, nodes.Identifier]):
    @t.override
    def parse(self, input: Stream[Token]) -> Parse.Result[nodes.Identifier]:
        match input.next():
            case lexemes.Identifier() as ident:
                return Parse.Match(nodes.Identifier(name=ident.identifier))
            case _:
                return Parse.NoMatch()


@dataclass
class IntegerLiteralTerminal(Parser[Token, nodes.IntegerLiteral]):
    @t.override
    def parse(self, input: Stream[Token]) -> Parse.Result[nodes.IntegerLiteral]:
        match input.next():
            case lexemes.IntegerLiteral() as int_lit:
                return Parse.Match(nodes.IntegerLiteral(integer=int_lit.integer))
            case _:
                return Parse.NoMatch()


@dataclass
class PrimitiveTerminal(Parser[Token, Primitive]):
    kind: PrimitiveKind

    @t.override
    def parse(self, input: Stream[Token]) -> Parse.Result[Primitive]:
        match input.next():
            case Primitive(kind) as prim if kind is self.kind:
                return Parse.Match(prim)
            case _:
                return Parse.NoMatch()


@dataclass
class KeywordTerminal(Parser[Token, Keyword]):
    kind: KeywordKind

    @t.override
    def parse(self, input: Stream[Token]) -> Parse.Result[Keyword]:
        match input.next():
            case Keyword(kind) as kw if kind is self.kind:
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


def block[
    T
](parser: Parser[Token, T]) -> DelimitedBy[Token, list[T], Primitive, Primitive]:
    """
    Parse any number of elements separated by >= 1 newline characters between delimiting curly braces.
    """

    return parser.separated_by(
        just(PrimitiveKind.NewLine).repeated().at_least(1)
    ).delimited_by(
        start=just(PrimitiveKind.LeftParenthesis),
        end=just(PrimitiveKind.RightParenthesis),
    )


def parens[T](parser: Parser[Token, T]) -> DelimitedBy[Token, T, Primitive, Primitive]:
    return parser.delimited_by(
        start=just(PrimitiveKind.LeftParenthesis),
        end=just(PrimitiveKind.RightParenthesis),
    )


def lines[T](parser: Parser[Token, T]) -> SeparatedBy[Token, T, Primitive]:
    return parser.separated_by(just(PrimitiveKind.NewLine))
