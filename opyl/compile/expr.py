import typing as t
from dataclasses import dataclass
from enum import Enum

from compile.token import Basic, Identifier, IntegerLiteral, Token

type Expression = (
    Identifier
    | IntegerLiteral
    | PrefixExpression
    | BinaryExpression
    | CallExpression
    | SubscriptExpression
)


class InfixOperator(Enum):
    FunctionApply = Basic.LeftParenthesis
    Subscript = Basic.LeftBracket
    MemberAccess = Basic.Period
    ScopeResolve = Basic.ColonColon


class BinaryOperator(Enum):
    Addition = Basic.Plus
    Subtraction = Basic.Hyphen
    Multiplication = Basic.Asterisk
    Division = Basic.ForwardSlash
    Exponentiation = Basic.Caret
    Equality = Basic.EqualEqual

    GreaterThan = Basic.RightAngle
    LessThan = Basic.LeftAngle

    ScopeResolution = Basic.ColonColon

    def precedence(self) -> int:
        return {
            self.Addition: 1,
            self.Subtraction: 1,
            self.Multiplication: 2,
            self.Division: 2,
            self.Exponentiation: 3,
            self.GreaterThan: 6,
            self.LessThan: 6,
            self.Equality: 7,
            self.ScopeResolution: 12,
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
            self.Equality: False,
            self.ScopeResolution: False,
        }[self]

    @classmethod
    def values(cls) -> set[Basic]:
        return {member.value for member in cls}

    @classmethod
    def is_binary_op(cls, any: Token) -> t.TypeGuard[Basic] | bool:
        return isinstance(any, Basic) and any in cls


class PrefixOperator(Enum):
    ArithmeticPlus = Basic.Plus
    ArithmeticMinus = Basic.Hyphen
    LogicalNegate = Basic.Exclamation

    def precedence(self) -> int:
        return 6

    @classmethod
    def is_prefix_op(cls, any: Token) -> t.TypeGuard[Basic] | bool:
        return isinstance(any, Basic) and any in cls


@dataclass
class BinaryExpression:
    operator: BinaryOperator
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
class PrefixExpression:
    operator: PrefixOperator
    expr: Expression
