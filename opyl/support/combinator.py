import typing as t
from dataclasses import dataclass
from abc import ABC, abstractmethod
import copy
from enum import Enum

from support.stream import Stream
from support.union import Maybe


class ParseResult:
    class Kind(Enum):
        Match = 0
        NoMatch = 1
        Error = 2

    @dataclass
    class Match[T, In]:
        item: T
        remaining: Stream[In]

    NoMatch: t.Final[t.Literal[Kind.NoMatch]] = Kind.NoMatch

    @dataclass
    class Error[Kind]:
        value: Kind

    type Type[In, T, E] = Match[T, In] | t.Literal[Kind.NoMatch] | Error[E]


PR = ParseResult


class Parser[In, Out, Err](ABC):
    @abstractmethod
    def parse(self, input: Stream[In]) -> ParseResult.Type[In, Out, Err]:
        raise NotImplementedError()

    @t.final
    def alternative[
        U
    ](self, other: "Parser[In, U, Err]") -> "Alternative[In, Out, U, Err]":
        return Alternative(self, other)

    @t.final
    def __or__[U](self, other: "Parser[In, U, Err]") -> "Alternative[In, Out, U, Err]":
        return self.alternative(other)

    @t.final
    def then[U](self, other: "Parser[In, U, Err]") -> "Then[In, Out, U, Err]":
        return Then(self, other)

    @t.final
    def ignore_then[
        U
    ](self, other: "Parser[In, U, Err]") -> "IgnoreThen[In, Out, U, Err]":
        return IgnoreThen(self, other)

    @t.final
    def then_ignore[
        U
    ](self, other: "Parser[In, U, Err]") -> "ThenIgnore[In, Out, U, Err]":
        return ThenIgnore(self, other)

    @t.final
    def separated_by[
        U
    ](self, separator: "Parser[In, U, Err]") -> "SeparatedBy[In, Out, U, Err]":
        return SeparatedBy(self, separator)

    @t.final
    def delimited_by[
        U, V
    ](
        self,
        start: "Parser[In, U, Err]",
        end: "Parser[In, V, Err]",
    ) -> "DelimitedBy[In, Out, U, V, Err]":
        return DelimitedBy(self, start, end)

    @t.final
    def or_not(self) -> "OrNot[In, Out, Err]":
        return OrNot(self)

    @t.final
    def or_else(self, default: Out) -> "OrElse[In, Out, Err]":
        return OrElse(self, default)

    @t.final
    def require(self, kind: Err) -> "Require[In, Out, Err]":
        return Require(self, kind)

    @t.final
    def map[U](self, func: t.Callable[[Out], U]) -> "Map[In, Out, U, Err]":
        return Map(self, func)

    @t.final
    def and_check(self, pred: t.Callable[[Out], bool]) -> "AndCheck[In, Out, Err]":
        return AndCheck(self, pred)

    @t.final
    def chain(
        self, other: "Parser[In, list[Out], Err]"
    ) -> "Map[In, tuple[Out, list[Out]], list[Out], Err]":
        return self.then(other).map(lambda a_b: [a_b[0], *a_b[1]])

    @t.final
    def repeated(self) -> "Repeated[In, Out, Err]":
        return Repeated(self)


@dataclass
class Require[In, Out, Err](Parser[In, Out, Err]):
    required: Parser[In, Out, Err]
    error: Err

    @t.override
    def parse(self, input: Stream[In]) -> ParseResult.Type[In, Out, Err]:
        match self.required.parse(input):
            case PR.Match(item, pos):
                return PR.Match(item, pos)
            case PR.NoMatch:
                return PR.Error(self.error)
            case PR.Error() as errs:
                return errs


@dataclass
class Alternative[In, FirstOut, SecondOut, Err](Parser[In, FirstOut | SecondOut, Err]):
    first_choice: Parser[In, FirstOut, Err]
    second_choice: Parser[In, SecondOut, Err]

    @t.override
    def parse(
        self, input: Stream[In]
    ) -> ParseResult.Type[In, FirstOut | SecondOut, Err]:
        match self.first_choice.parse(input):
            case PR.Match(item, pos):
                return PR.Match(item, pos)
            case PR.NoMatch:
                ...
            case PR.Error() as errors:
                return errors

        match self.second_choice.parse(input):
            case PR.Match(item, pos):
                return PR.Match(item, pos)
            case PR.NoMatch:
                return PR.NoMatch
            case PR.Error() as errors:
                return errors


@dataclass
class Then[In, FirstOut, SecondOut, Err](Parser[In, tuple[FirstOut, SecondOut], Err]):
    first: Parser[In, FirstOut, Err]
    second: Parser[In, SecondOut, Err]

    @t.override
    def parse(
        self, input: Stream[In]
    ) -> ParseResult.Type[In, tuple[FirstOut, SecondOut], Err]:
        first_result = self.first.parse(input)

        match first_result:
            case PR.Match():
                ...
            case PR.NoMatch:
                return PR.NoMatch
            case PR.Error() as err:
                return err

        match self.second.parse(first_result.remaining):
            case PR.Match(second_item, pos):
                return PR.Match((first_result.item, second_item), pos)
            case no_match_or_err:
                return no_match_or_err


@dataclass
class IgnoreThen[In, IgnoreOut, Out, Err](Parser[In, Out, Err]):
    first: Parser[In, IgnoreOut, Err]
    second: Parser[In, Out, Err]

    @t.override
    def parse(self, input: Stream[In]) -> ParseResult.Type[In, Out, Err]:
        match self.first.parse(input):
            case PR.Match(_, pos):
                return self.second.parse(pos)
            case no_match_or_err:
                return no_match_or_err


@dataclass
class ThenIgnore[In, Out, IgnoreOut, Err](Parser[In, Out, Err]):
    first: Parser[In, Out, Err]
    second: Parser[In, IgnoreOut, Err]

    @t.override
    def parse(self, input: Stream[In]) -> ParseResult.Type[In, Out, Err]:
        match self.first.parse(input):
            case PR.Match(item, pos):
                match self.second.parse(pos):
                    case PR.Match(_, pos):
                        return PR.Match(item, pos)
                    case no_match_or_err:
                        return no_match_or_err
            case no_match_or_err:
                return no_match_or_err


@dataclass
class SeparatedBy[In, Out, Sep, Err](Parser[In, list[Out], Err]):
    parser: Parser[In, Out, Err]
    separator: Parser[In, Sep, Err]

    _allow_leading: bool = False
    _allow_trailing: bool = False
    _at_least: int = 0

    @t.override
    def parse(self, input: Stream[In]) -> ParseResult.Type[In, list[Out], Err]:
        ...
        # # TODO: Rewrite this entire thing.
        # items = list[Out]()

        # if self._allow_leading:
        #     match self.separator(input):
        #         case PR.Match():
        #             ...
        #         case PR.NoMatch:
        #             ...
        #         case PR.Error() as errors:
        #             return errors

        # match self.parser(input):
        #     case PR.Match(item):
        #         items.append(item)
        #     case PR.NoMatch:
        #         if len(items) < self._at_least:
        #             return PR.NoMatch
        #         return PR.Match(items)
        #     case PR.Error() as errors:
        #         if len(items) < self._at_least:
        #             return errors
        #         return PR.Match(items)

        # while True:
        #     match self.separator(input):
        #         case PR.Match():
        #             ...
        #         case PR.NoMatch:
        #             break
        #         case PR.Error() as errors:
        #             return errors

        #     match self.parser(input):
        #         case PR.Match(item):
        #             items.append(item)
        #         case PR.NoMatch:
        #             break
        #         case PR.Error() as errors:
        #             if self._allow_trailing:
        #                 break

        #             return errors

        # if len(items) < self._at_least:
        #     return PR.NoMatch
        # return PR.Match(items)

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
class DelimitedBy[In, Out, Start, End, Err](Parser[In, Out, Err]):
    parser: Parser[In, Out, Err]
    start: Parser[In, Start, Err]
    end: Parser[In, End, Err]

    @t.override
    def parse(self, input: Stream[In]) -> ParseResult.Type[In, Out, Err]:
        return self.start.ignore_then(self.parser).then_ignore(self.end).parse(input)


@dataclass
class OrNot[In, Out, Err](Parser[In, Maybe.Type[Out], Err]):
    maybe: Parser[In, Out, Err]

    @t.override
    def parse(self, input: Stream[In]) -> ParseResult.Type[In, Maybe.Type[Out], Err]:
        match self.maybe.parse(input):
            case PR.Match(item, remaining):
                return PR.Match(Maybe.Just(item), remaining)
            case PR.NoMatch:
                return PR.Match(Maybe.Nothing, input)
            case PR.Error() as errors:
                return errors


@dataclass
class OrElse[In, Out, Err](Parser[In, Out, Err]):
    maybe: Parser[In, Out, Err]
    default: Out

    @t.override
    def parse(self, input: Stream[In]) -> ParseResult.Type[In, Out, Err]:
        match self.maybe.parse(input):
            case PR.Match(item, remaining):
                return PR.Match(item, remaining)
            case PR.NoMatch:
                return PR.Match(self.default, input)
            case PR.Error() as errors:
                return errors


@dataclass
class Map[In, Out, Mapped, Err](Parser[In, Mapped, Err]):
    parser: Parser[In, Out, Err]
    func: t.Callable[[Out], Mapped]

    @t.override
    def parse(self, input: Stream[In]) -> ParseResult.Type[In, Mapped, Err]:
        match self.parser.parse(input):
            case PR.Match(item, pos):
                return PR.Match(self.func(item), pos)
            case no_match_or_err:
                return no_match_or_err


@dataclass
class Filter[In, Err](Parser[In, In, Err]):
    func: t.Callable[[In], bool]

    @t.override
    def parse(self, input: Stream[In]) -> ParseResult.Type[In, In, Err]:
        match input.peek():
            case Maybe.Just(item):
                if self.func(item):
                    return PR.Match(item, input.advance())
                return PR.NoMatch
            case Maybe.Nothing:
                return PR.NoMatch


@dataclass
class AndCheck[In, Out, Err](Parser[In, Out, Err]):
    parser: Parser[In, Out, Err]
    predicate: t.Callable[[Out], bool]

    @t.override
    def parse(self, input: Stream[In]) -> ParseResult.Type[In, Out, Err]:
        match self.parser.parse(input):
            case PR.Match(item, remaining):
                if self.predicate(item):
                    return PR.Match(item, remaining)
                return PR.NoMatch
            case no_match_or_err:
                return no_match_or_err


@dataclass
class Repeated[In, Out, Err](Parser[In, list[Out], Err]):
    parser: Parser[In, Out, Err]
    _at_least: int = 0

    @t.override
    def parse(self, input: Stream[In]) -> ParseResult.Type[In, list[Out], Err]:
        items = list[Out]()

        while True:
            match self.parser.parse(input):
                case PR.Match(item, pos):
                    input = pos
                    items.append(item)
                case PR.NoMatch:
                    if len(items) < self._at_least:
                        return PR.NoMatch
                    return PR.Match(items, input)
                case PR.Error() as err:
                    return err

    def at_least(self, minimum: int) -> t.Self:
        other = copy.copy(self)
        other._at_least = minimum
        return other


@dataclass
class OneOf[In, Err](Parser[In, In, Err]):
    choices: t.Sequence[In]

    @t.override
    def parse(self, input: Stream[In]) -> ParseResult.Type[In, In, Err]:
        match input.peek():
            case Maybe.Just(item):
                if item in self.choices:
                    return PR.Match(item, input.advance())
                return PR.NoMatch
            case Maybe.Nothing:
                return PR.NoMatch


@dataclass
class Just[In, Err](Parser[In, In, Err]):
    pattern: In

    @t.override
    def parse(self, input: Stream[In]) -> ParseResult.Type[In, In, Err]:
        match input.peek():
            case Maybe.Just(item):
                if item == self.pattern:
                    return PR.Match(self.pattern, input.advance())
                return PR.NoMatch
            case Maybe.Nothing:
                return PR.NoMatch


def filter[In](func: t.Callable[[In], bool]) -> Filter[In, t.Any]:
    return Filter(func)


def one_of[In](choices: t.Sequence[In]) -> OneOf[In, t.Any]:
    return OneOf(choices)
