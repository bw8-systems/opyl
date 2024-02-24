import typing as t
from dataclasses import dataclass
from enum import Enum
import sys


class Maybe:
    class Kind(Enum):
        Just = 0
        Nothing = 1

        def unwrap(self) -> t.NoReturn:
            assert self is self.Nothing
            assert False, "Unwrapping failed: Maybe is not Maybe.Just"

    @dataclass
    class Just[T]:
        item: T

        def unwrap(self) -> T:
            return self.item

    Nothing: t.Final[t.Literal[Kind.Nothing]] = Kind.Nothing

    type Type[T] = Just[T] | t.Literal[Kind.Nothing]


class Result:
    class Kind(Enum):
        Ok = 0
        Err = 1

    type Type[T, E] = Ok[T] | Err[E]

    @dataclass
    class Ok[T]:
        item: T

        def unwrap(self) -> T:
            return self.item

        def unwrap_err(self) -> t.NoReturn:
            assert False, "Unwrapping failed. Result.Ok is not Result.Err"

        def and_then[
            U, E
        ](self, op: "t.Callable[[T], Result.Type[U, E]]") -> "Result.Type[U, E]":
            return op(self.item)

        def expect(self, _expectation: str) -> T:
            return self.item

        def is_ok(self) -> t.Literal[True]:
            return True

        def is_err(self) -> t.Literal[False]:
            return False

    @dataclass
    class Err[E]:
        item: E

        def unwrap(self) -> t.NoReturn:
            assert False, "Unwrapping failed. Result.Err is not Result.Ok"

        def unwrap_err(self) -> E:
            return self.item

        def and_then[
            T, U
        ](self, op: "t.Callable[[T], Result.Type[U, E]]") -> "Result.Type[U, E]":
            return self

        def expect(self, expectation: str) -> t.NoReturn:
            print(expectation, file=sys.stderr)
            exit(-1)

        def is_ok(self) -> t.Literal[False]:
            return False

        def is_err(self) -> t.Literal[True]:
            return True
