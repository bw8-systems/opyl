import typing as t
from dataclasses import dataclass
from enum import Enum

from opyl.compile.token import Basic, Identifier, IntegerLiteral, StringLiteral, Token

type InfixExpression = BinaryExpression | CallExpression | SubscriptExpression | MemberAccessExpression

type Expression = (
    Identifier | IntegerLiteral | StringLiteral | PrefixExpression | InfixExpression
)


class InfixOperator(Enum):
    FunctionApply = Basic.LeftParenthesis
    Subscript = Basic.LeftBracket
    MemberAccess = Basic.Period
    ScopeResolve = Basic.Colon2


class BinOp(Enum):
    Addition = Basic.Plus
    Subtraction = Basic.Hyphen
    Multiplication = Basic.Asterisk
    Division = Basic.ForwardSlash
    Exponentiation = Basic.Caret
    Equal = Basic.Equal2
    NotEqual = Basic.BangEqual

    GreaterThan = Basic.RightAngle
    GreaterEqual = Basic.RightAngleEqual
    LessThan = Basic.LeftAngle
    LessEqual = Basic.LeftAngleEqual

    ScopeResolution = Basic.Colon2
    BitwiseAND = Basic.Ampersand
    BitwiseOR = Basic.Pipe

    LogicalAND = Basic.Ampersand2
    LogicalOR = Basic.Pipe2

    LeftShift = Basic.LeftAngle2
    RightShift = Basic.RightAngle2

    def precedence(self) -> int:
        return {
            self.Addition: 1,
            self.Subtraction: 1,
            self.Multiplication: 2,
            self.Division: 2,
            self.Exponentiation: 3,
            self.GreaterThan: 6,
            self.LessThan: 6,
            self.Equal: 7,
            self.ScopeResolution: 12,  # TODO: Remove
        }[self]

    def is_right_associative(self) -> bool:
        return {
            self.Addition: False,
            self.Subtraction: False,
            self.Multiplication: False,
            self.Division: False,
            self.Exponentiation: True,
            self.GreaterThan: False,
            self.LessThan: False,
            self.Equal: False,
            self.ScopeResolution: False,
        }[self]

    def adjusted_precedence(self) -> int:
        adjusted = self.precedence()

        if self.is_right_associative():
            adjusted -= 1

        return adjusted

    @classmethod
    def values(cls) -> set[Basic]:
        return {member.value for member in cls}

    @classmethod
    def is_binary_op(cls, any: Token) -> t.TypeGuard[Basic] | bool:
        return isinstance(any, Basic) and any in cls


class PrefixOperator(Enum):
    ArithmeticPlus = Basic.Plus
    ArithmeticMinus = Basic.Hyphen
    LogicalNegate = Basic.Bang
    BitwiseNOT = Basic.Tilde
    DeReference = Basic.At
    AddressOf = Basic.Ampersand

    def precedence(self) -> int:
        return 6

    @classmethod
    def is_prefix_op(cls, any: Token) -> t.TypeGuard[Basic] | bool:
        return isinstance(any, Basic) and any in cls


@dataclass
class BinaryExpression:
    operator: BinOp
    left: Expression
    right: Expression


@dataclass
class CallExpression:
    function: Expression
    arguments: list[Expression]


@dataclass
class SubscriptExpression:
    base: Expression
    index: Expression


@dataclass
class MemberAccessExpression:
    base: Expression
    member: Identifier


@dataclass
class PrefixExpression:
    operator: PrefixOperator
    expr: Expression


# Rows ordered by INCREASING precedence
PRECEDENCE = [
    # Scope Resolution
    [InfixOperator.FunctionApply, InfixOperator.Subscript, InfixOperator.MemberAccess],
    [
        PrefixOperator.LogicalNegate,
        PrefixOperator.BitwiseNOT,
        PrefixOperator.DeReference,
        PrefixOperator.AddressOf,
    ],
    [BinOp.Multiplication, BinOp.Division],
    [BinOp.Addition, BinOp.Subtraction],
    [BinOp.LeftShift, BinOp.RightShift],
    [
        BinOp.LessThan,
        BinOp.GreaterThan,
        BinOp.LessEqual,
        BinOp.GreaterEqual,
    ],
    [BinOp.Equal, BinOp.NotEqual],
    [BinOp.BitwiseAND],
    [BinOp.BitwiseOR],
    [BinOp.LogicalAND],
    [BinOp.LogicalOR],
]
