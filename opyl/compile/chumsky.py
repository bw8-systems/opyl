import typing as t
from dataclasses import dataclass
from abc import ABC, abstractmethod
import copy
from pprint import pprint

from compile import nodes
from compile.positioning import Stream, TextPosition, Span
from compile import lexemes
from compile import errors
from compile.lexemes import Token, PrimitiveKind, Primitive, KeywordKind, Keyword
from compile.lexemes import PrimitiveKind as PK
from compile.lexemes import KeywordKind as KK
from compile.errors import ParseException


@dataclass
class Marker:
    position: TextPosition
    err_count: int


@dataclass
class Located[E]:
    pos: TextPosition
    err: E


@dataclass
class Errors[E]:
    alt: Located[E] | None
    secondary: list[Located[E]]


@dataclass
class InputRef[E]:
    position: TextPosition
    input: Stream[Token]
    errors: Errors[E]

    def save(self) -> Marker:
        return Marker(
            position=self.position,
            err_count=len(self.errors.secondary),
        )

    def emit(self, pos: TextPosition, err: E):
        self.errors.secondary.append(Located(pos, err))

    def rewind(self, marker: Marker):
        self.errors.secondary = self.errors.secondary[: marker.err_count]
        self.position = marker.position


class Strategy[T](ABC):
    @abstractmethod
    def recover(
        self, input: InputRef[ParseException], parser: "Parser[T, t.Any]"
    ) -> "PResult[T]":
        raise NotImplementedError()


@dataclass
class ParseResult[T, E]:
    output: T | None
    errors: list[E]


@dataclass
class Ok[T]:
    ok: T


@dataclass
class Err[E]:
    err: E


type PResult[T] = Ok[T] | Err[tuple[()]]


class Parser[T, E](ABC):
    def parse(self, input: Stream[Token]) -> ParseResult[T, E]:
        ...

    @abstractmethod
    def go(self, input: InputRef[ParseException]) -> PResult[T]:
        raise NotImplementedError()

    def map[U](self, f: t.Callable[[T], U]) -> "Map[T, U, E]":
        return Map(parser=self, mapper=f)

    def then[U](self, parser: "Parser[U, E]") -> "Then[T, U, E]":
        # Parse a thing and then another thing. Return a tuple of both things.
        return Then(first=self, second=parser)

    def ignore_then[U](self, parser: "Parser[U, E]") -> "IgnoreThen[T, U, E]":
        # Parse a thing and then another thing. Return the second thing.
        return IgnoreThen(first=self, second=parser)

    def then_ignore[U](self, parser: "Parser[U, E]") -> "ThenIgnore[T, U, E]":
        # Parse a thing and then another thing. Return the first thing.
        return ThenIgnore(first=self, second=parser)

    # NOTE: Chumsky implements `or` using a `Choice` primitive.
    def or_try[U](self, other: "Parser[U, E]") -> "OrTry[T, U, E]":
        # Parse one thing, and on failure parse another.
        return OrTry(first=self, second=other)

    def or_not(self) -> "OrNot[T, E]":
        # Attempt to parse something, if it exists.
        return OrNot(self)

    def separated_by[U](self, separator: "Parser[U, E]") -> "SeparatedBy[T, U, E]":
        # Parse a pattern, separated by another, any number of times.
        return SeparatedBy(parser=self, separator=separator)

    def delimited_by[U, V](
        self, start: "Parser[U, E]", end: "Parser[V, E]"
    ) -> "DelimitedBy[T, U, V, E]":
        return DelimitedBy(parser=self, start=start, end=end)


@dataclass
class Map[T, U, E](Parser[U, E]):
    parser: Parser[T, E]
    mapper: t.Callable[[T], U]

    @t.override
    def go(self, input: InputRef[ParseException]) -> PResult[U]:
        out_result = self.parser.go(input)
        if isinstance(out_result, Err):
            return out_result
        return Ok(self.mapper(out_result.ok))


@dataclass
class Then[T, U, E](Parser[tuple[T, U], E]):
    first: Parser[T, E]
    second: Parser[U, E]

    @t.override
    def go(self, input: InputRef[ParseException]) -> PResult[tuple[T, U]]:
        first_result = self.first.go(input)
        if isinstance(first_result, Err):
            return first_result

        second_result = self.second.go(input)
        if isinstance(second_result, Err):
            return second_result

        return Ok((first_result.ok, second_result.ok))


@dataclass
class IgnoreThen[T, U, E](Parser[U, E]):
    first: Parser[T, E]
    second: Parser[U, E]

    @t.override
    def go(self, input: InputRef[ParseException]) -> PResult[U]:
        first_result = self.first.go(input)
        if isinstance(first_result, Err):
            return first_result

        second_result = self.second.go(input)
        if isinstance(second_result, Err):
            return second_result

        return second_result


@dataclass
class ThenIgnore[T, U, E](Parser[T, E]):
    first: Parser[T, E]
    second: Parser[U, E]

    @t.override
    def go(self, input: InputRef[ParseException]) -> PResult[T]:
        first_result = self.first.go(input)
        if isinstance(first_result, Err):
            return first_result

        second_result = self.second.go(input)
        if isinstance(second_result, Err):
            return second_result

        return first_result


@dataclass
class OrTry[T, U, E](Parser[T | U, E]):
    first: Parser[T, E]
    second: Parser[U, E]

    @t.override
    def go(self, input: InputRef[ParseException]) -> PResult[T | U]:
        ...


@dataclass
class OrNot[T, E](Parser[T | None, E]):
    parser: Parser[T, E]

    @t.override
    def go(self, input: InputRef[ParseException]) -> PResult[T | None]:
        # NOTE: Chumsky saves a `Marker` based on `InputRef`'s internal error count. Should this be owned
        # by OpalParser / Parser? Or is maintaining a stack index like this okay? Honestly seems like not
        # using a stack is simpler lol. Don't have to clean the stack with drops.
        before = input.save()
        match self.parser.go(input):
            case Ok(out):
                return Ok(out)
            case Err():
                input.rewind(before)
                return Ok(None)


@dataclass
class SeparatedBy[T, U, E](Parser[list[T], E]):
    parser: Parser[T, E]
    separator: Parser[U, E]
    _allow_leading: bool = False
    _allow_trailing: bool = False
    _at_least: int = 0

    @t.override
    def go(self, input: InputRef[ParseException]) -> PResult[list[T]]:
        while True:
            before = input.position

            try:
                token = input.input.next()
            except errors.UnexpectedEOF:
                ...
            else:
                ...

    def next(self, input: InputRef[ParseException]) -> ...:
        let out = self.parser.next

    def allow_leading(self) -> t.Self:
        new = copy.copy(self)
        new._allow_leading = True
        return new

    def allow_trailing(self) -> t.Self:
        new = copy.copy(self)
        new._allow_trailing = True
        return new

    def at_least(self, min: int) -> t.Self:
        new = copy.copy(self)
        new._at_least = min
        return new


@dataclass
class DelimitedBy[A, B, C, E](Parser[A, E]):
    parser: Parser[A, E]
    start: Parser[B, E]
    end: Parser[C, E]

    @t.override
    def go(self, input: InputRef[ParseException]) -> PResult[A]:
        start_result = self.start.go(input)
        if not isinstance(start_result, Ok):
            return start_result

        parse_result = self.parser.go(input)
        if not isinstance(parse_result, Ok):
            return parse_result

        end_result = self.end.go(input)
        if not isinstance(end_result, Ok):
            return end_result

        return parse_result


@dataclass
class SkipUntil[T, E](Strategy[T]):
    skip: Parser[tuple[()], E]
    until: Parser[tuple[()], E]
    fallback: t.Callable[[], T]

    @t.override
    def recover(
        self, input: InputRef[ParseException], parser: Parser[T, t.Any]
    ) -> PResult[T]:
        alt = input.errors.alt
        assert alt is not None, "Attempting to recover from error without an error..."
        while True:
            before = input.save()

            until_result = self.until.go(input)
            if isinstance(until_result, Ok):
                input.emit(input.position, alt.err)
                return Ok(self.fallback())
            input.rewind(before)

            skip_result = self.skip.go(input)
            if isinstance(skip_result, Err):
                input.errors.alt = alt
                return Err(())


def skip_until[T, E](
    skip: Parser[tuple[()], E], until: Parser[tuple[()], E], fallback: t.Callable[[], T]
) -> SkipUntil[T, E]:
    return SkipUntil(skip=skip, until=until, fallback=fallback)


class Identifier(Parser[nodes.Identifier, ParseException]):
    @t.override
    def go(self, input: InputRef[ParseException]) -> PResult[nodes.Identifier]:
        return Ok(nodes.Identifier(span=Span.default(), name="Foo"))


class IntegerLiteral(Parser[nodes.IntegerLiteral, ParseException]):
    @t.override
    def go(self, input: InputRef[ParseException]) -> PResult[nodes.IntegerLiteral]:
        return Ok(nodes.IntegerLiteral(span=Span.default(), integer=4))


@dataclass
class PrimitiveToken(Parser[Primitive, ParseException]):
    kind: PrimitiveKind

    @t.override
    def go(self, input: InputRef[ParseException]) -> PResult[nodes.Primitive]:
        return Ok(Primitive(span=Span.default(), kind=self.kind))


@dataclass
class KeywordToken(Parser[Keyword, ParseException]):
    kind: KeywordKind

    @t.override
    def go(self, input: InputRef[ParseException]) -> PResult[Keyword]:
        return Ok(Keyword(span=Span.default(), kind=self.kind))


def just(kind: PrimitiveKind) -> PrimitiveToken:
    return PrimitiveToken(kind)


def keyword(kind: KeywordKind) -> KeywordToken:
    return KeywordToken(kind)


@dataclass
class Call:
    name: nodes.Identifier
    args: list[nodes.IntegerLiteral]


ident = Identifier()
expr = IntegerLiteral()

call = ident.then(
    expr.separated_by(just(PK.Comma))
    .allow_trailing()
    .delimited_by(just(PK.LeftParenthesis), just(PK.RightParenthesis))
).map(lambda parsed: Call(name=parsed[0], args=parsed[1]))

type = ident
field = ident.then(just(PK.Colon)).then(type)

struct = (
    keyword(KK.Struct)
    .ignore_then(ident)
    .then(
        field.separated_by(just(PK.NewLine))
        .at_least(1)
        .allow_leading()
        .allow_trailing()
        .delimited_by(start=just(PK.LeftParenthesis), end=just(PK.RightParenthesis))
    )
)

let = (
    keyword(KK.Let)
    .ignore_then(ident)
    .then(
        (
            just(PK.Colon).ignore_then(type).then_ignore(just(PK.Equal)).then(expr)
        ).or_try(just(PK.Equal).then(expr))
    )
)

union = (
    keyword(KK.Union)
    .ignore_then(ident)
    .then_ignore(just(PK.Equal))
    .then(ident.separated_by(just(PK.Pipe)).at_least(2))
)

enum = (
    keyword(KK.Enum)
    .ignore_then(ident)
    .then(
        ident.separated_by(just(PK.Comma))
        .at_least(1)
        .allow_trailing()
        .delimited_by(start=just(PK.LeftBrace), end=just(PK.RightBrace))
    )
)

tokens = [
    lexemes.Keyword(Span.default(), KK.Enum),
    lexemes.Identifier(Span.default(), "Foo"),
    lexemes.Primitive(Span.default(), PK.LeftBrace),
    lexemes.Identifier(Span.default(), "MEMBER"),
    lexemes.Primitive(Span.default(), PK.Comma),
    lexemes.Primitive(Span.default(), PK.RightBrace),
]


item = (keyword(KK.Enum).then(ident).then(ident.separated_by(just(PK.Comma)))).go(
    input=InputRef(
        position=TextPosition(0, 0, 0),
        input=Stream(tokens),
        errors=Errors(alt=None, secondary=list()),
    )
)

if isinstance(item, Ok):
    pprint(item.ok)
