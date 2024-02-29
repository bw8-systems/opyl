from dataclasses import dataclass

from opyl.compile.token import (
    IntegerLiteral,
    Identifier,
    StringLiteral,
    CharacterLiteral,
)
from opyl.compile.expr import PrefixExpression, InfixExpression
from opyl.compile.types import Type


@dataclass
class TypedIntegerLiteral:
    literal: IntegerLiteral
    type: Type


@dataclass
class TypedPrefixExpression:
    expr: PrefixExpression
    type: Type


@dataclass
class TypedInfixExpression:
    expr: InfixExpression
    type: Type


type TypedExpression = (
    Identifier
    | TypedIntegerLiteral
    | StringLiteral
    | CharacterLiteral
    | TypedPrefixExpression
    | TypedInfixExpression
)
