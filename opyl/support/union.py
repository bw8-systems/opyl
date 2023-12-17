import typing as t
from dataclasses import dataclass
from enum import Enum


class Maybe:
    class Kind(Enum):
        Just = 0
        Nothing = 1

    @dataclass
    class Just[T]:
        item: T

    Nothing: t.Final[t.Literal[Kind.Nothing]] = Kind.Nothing

    type Type[T] = Just[T] | t.Literal[Kind.Nothing]


class Result:
    class Kind(Enum):
        Ok = 0
        Err = 1

    @dataclass
    class Ok[T]:
        item: T

    @dataclass
    class Err[E]:
        item: E

    type Type[T, E] = Ok[T] | Err[E]
