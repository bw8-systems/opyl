import typing as t
import enum
from dataclasses import dataclass


class Error:
    ...


type Token = t.Literal[JsonKind.Null] | Boolean | String | Number | Array | Object


class JsonKind(enum.Enum):
    Null = enum.auto()
    Boolean = enum.auto()
    String = enum.auto()
    Number = enum.auto()
    Array = enum.auto()
    Object = enum.auto()


Null: t.Final[t.Literal[JsonKind.Null]] = JsonKind.Null


@dataclass
class Boolean:
    boolean: bool


@dataclass
class String:
    string: str


@dataclass
class Number:
    number: int


@dataclass
class Array:
    items: list[Token]


@dataclass
class Object:
    map: dict[String, Token]
