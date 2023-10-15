from enum import Enum, auto
from dataclasses import dataclass
from typing import Literal, Self


class _Complex(Enum):
    Integer = auto()
    Identifier = auto()


Integer: Literal[_Complex.Integer] = _Complex.Integer
Identifier: Literal[_Complex.Identifier] = _Complex.Identifier


class kind:
    class PrimitiveKind(Enum):
        Colon = auto()
        Equals = auto()
        LeftBrace = auto()
        RightBrace = auto()

    class KeywordKind(Enum):
        Const = auto()
        Let = auto()
        Enum = auto()

    IntegerKind = Literal[_Complex.Integer]
    IdentifierKind = Literal[_Complex.Identifier]

    type TokenKind = kind.PrimitiveKind | kind.KeywordKind | kind.IntegerKind | kind.IdentifierKind


@dataclass
class Span:
    start: int
    stop: int

    def __add__(self, other: Self) -> Self:
        return Span(start=self.start, stop=other.stop)


class token:
    @dataclass
    class BaseToken[Kind: kind.TokenKind]:
        span: Span
        kind: Kind

    type PrimitiveToken = BaseToken[kind.PrimitiveKind]
    type KeywordToken = BaseToken[kind.KeywordKind]

    @dataclass
    class IntegerToken(BaseToken[kind.IntegerKind]):
        value: int

    @dataclass
    class IdentifierToken(BaseToken[kind.IdentifierKind]):
        value: str

    type Token = PrimitiveToken | KeywordToken | IntegerToken | IdentifierToken


# --------------
# Parsing
# --------------


@dataclass
class Node:
    span: Span


@dataclass
class KeywordNode(Node):
    keyword: kind.KeywordKind


@dataclass
class IdentifierNode(Node):
    name: str


@dataclass
class IntegerNode(Node):
    value: int


@dataclass
class TypeNode(Node):
    ...  # TODO


@dataclass
class ExpressionNode(Node):
    ...  # TODO


@dataclass
class ConstantNode(Node):
    name: str
    type: TypeNode
    expr: ExpressionNode


@dataclass
class VariableDeclarationNode(Node):
    name: str
    type: TypeNode
    expr: ExpressionNode | None


@dataclass
class EnumDeclarationNode(Node):
    name: str
    members: list[IdentifierNode]
