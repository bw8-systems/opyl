import typing as t
from dataclasses import dataclass
from abc import ABC, abstractmethod

from compile import nodes
from compile.positioning import Stream, TextPosition, Span
from compile.lexemes import Token, PrimitiveKind, Primitive, KeywordKind, Keyword
from compile.lexemes import PrimitiveKind as PK
from compile.lexemes import KeywordKind as KK
from compile.errors import ParseException


@dataclass
class Marker[Offset]:
    offset: Offset
    err_count: int


class Input[T](t.Protocol):
    ...


@dataclass
class Located[T, E]:
    pos: T
    err: E

    @staticmethod
    def at(pos: T, err: E) -> "Located[T, E]":
        return Located(pos, err)


@dataclass
class Errors[T, E]:
    alt: Located[T, E] | None
    secondary: list[Located[T, E]]


@dataclass
class InputRef[Offset, Error]:
    offset: Offset
    input: Input[Offset]
    errors: Errors[Offset, Error]

    def save(self) -> Marker[Offset]:
        return Marker(
            offset=self.offset,
            err_count=len(self.errors.secondary),
        )

    def emit(self, pos: Offset, err: Error):
        self.errors.secondary.append(Located.at(pos, err))

    def rewind(self, marker: Marker[Offset]):
        self.errors.secondary = self.errors.secondary[: marker.err_count]
        self.offset = marker.offset


class Strategy[T](ABC):
    @abstractmethod
    def recover(
        self, input: InputRef[TextPosition, ParseException], parser: "Parser[T, t.Any]"
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
    def go(self, input: InputRef[TextPosition, ParseException]) -> PResult[T]:
        raise NotImplementedError()

    def map[U](self, f: t.Callable[[T], U]) -> "Map[T, U, E]":
        ...
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
    def go(self, input: InputRef[TextPosition, ParseException]) -> PResult[U]:
        out_result = self.parser.go(input)
        if isinstance(out_result, Err):
            return out_result
        return Ok(self.mapper(out_result.ok))


@dataclass
class Then[T, U, E](Parser[tuple[T, U], E]):
    first: Parser[T, E]
    second: Parser[U, E]

    @t.override
    def go(self, input: InputRef[TextPosition, ParseException]) -> PResult[tuple[T, U]]:
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
    def go(self, input: InputRef[TextPosition, ParseException]) -> PResult[U]:
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
    def go(self, input: InputRef[TextPosition, ParseException]) -> PResult[T]:
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
    def go(self, input: InputRef[TextPosition, ParseException]) -> PResult[T | U]:
        ...


@dataclass
class OrNot[T, E](Parser[T | None, E]):
    parser: Parser[T, E]

    @t.override
    def go(self, input: InputRef[TextPosition, ParseException]) -> PResult[T | None]:
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
    def go(self, input: InputRef[TextPosition, ParseException]) -> PResult[list[T]]:
        ...

    def allow_leading(self) -> t.Self:
        return self.__class__(
            parser=self.parser,
            separator=self.separator,
            _allow_leading=True,
            _allow_trailing=self._allow_trailing,
            _at_least=self._at_least,
        )

    def allow_trailing(self) -> t.Self:
        return self.__class__(
            parser=self.parser,
            separator=self.separator,
            _allow_leading=self._allow_leading,
            _allow_trailing=True,
            _at_least=self._at_least,
        )

    def at_least(self, min: int) -> t.Self:
        return self.__class__(
            parser=self.parser,
            separator=self.separator,
            _allow_leading=self._allow_leading,
            _allow_trailing=True,
            _at_least=min,
        )


@dataclass
class DelimitedBy[A, B, C, E](Parser[A, E]):
    parser: Parser[A, E]
    start: Parser[B, E]
    end: Parser[C, E]

    @t.override
    def go(self, input: InputRef[TextPosition, ParseException]) -> PResult[A]:
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
        self, input: InputRef[TextPosition, ParseException], parser: Parser[T, t.Any]
    ) -> PResult[T]:
        alt = input.errors.alt
        assert alt is not None, "Attempting to recover from error without an error..."
        while True:
            before = input.save()

            until_result = self.until.go(input)
            if isinstance(until_result, Ok):
                input.emit(input.offset, alt.err)
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


# @dataclass
# class SkipThenRetryUntil[T, E](Strategy[T]):
#     skip: Parser[tuple[()], E]
#     until: Parser[tuple[()], E]

#     @t.override
#     def recover(
#         self, input: InputRef[TextPosition, ParseException], parser: Parser[T, t.Any]
#     ) -> PResult[T]:
#         alt = input.errors.alt
#         assert alt is not None, "Attempting to recover from error without an error..."

#         while True:
#             before = input.save()
#             match self.until.go(input):
#                 case Ok():
#                     input.errors.alt = alt
#                     input.rewind(before)
#                     return Err(())
#                 case Err():
#                     input.rewind(before)

#             skip_result = self.skip.go(input)
#             if isinstance(skip_result, Err):
#                 input.errors.alt = alt
#                 return Err(())

#             before = input.save()
#             parser_result = parser.go(input)
#             assert isinstance(parser_result, Ok)


class Identifier(Parser[nodes.Identifier, ParseException]):
    @t.override
    def go(
        self, input: InputRef[TextPosition, ParseException]
    ) -> PResult[nodes.Identifier]:
        return Ok(nodes.Identifier(span=Span.default(), name="Foo"))


class IntegerLiteral(Parser[nodes.IntegerLiteral, ParseException]):
    @t.override
    def go(
        self, input: InputRef[TextPosition, ParseException]
    ) -> PResult[nodes.IntegerLiteral]:
        return Ok(nodes.IntegerLiteral(span=Span.default(), integer=4))


@dataclass
class PrimitiveToken(Parser[Primitive, ParseException]):
    kind: PrimitiveKind

    @t.override
    def go(
        self, input: InputRef[TextPosition, ParseException]
    ) -> PResult[nodes.Primitive]:
        return Ok(Primitive(span=Span.default(), kind=self.kind))


@dataclass
class KeywordToken(Parser[Keyword, ParseException]):
    kind: KeywordKind

    @t.override
    def go(self, input: InputRef[TextPosition, ParseException]) -> PResult[Keyword]:
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
