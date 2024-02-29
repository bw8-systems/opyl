from opyl.support.union import Maybe
from opyl.compile.expr import (
    Expression,
    BinaryExpression,
    StringLiteral,
    CharacterLiteral,
    IntegerLiteral,
    BinOp,
    PrefixExpression,
    CallExpression,
    SubscriptExpression,
    MemberAccessExpression,
    PrefixOperator,
)
from opyl.compile.token import Identifier
from opyl.compile.types import Type, Primitive


def check_expression(expression: Expression) -> Maybe.Type[Type]:
    match expression:
        case Identifier():
            # TODO: Symbol table lookups
            return Maybe.Nothing
        case IntegerLiteral():
            return Maybe.Just(Primitive.UInt16)
        case StringLiteral():
            return Maybe.Just(Primitive.String)
        case CharacterLiteral():
            return Maybe.Just(Primitive.Character)
        case PrefixExpression(operator, expression):
            return check_prefix_expr(operator, expression)
        case BinaryExpression(operator, lhs, rhs):
            return check_binary_expr(operator, lhs, rhs)
        case CallExpression(invokable, arguments):
            return check_call_expr(invokable, arguments)
        case SubscriptExpression(base, index):
            return check_subscript_expr(base, index)
        case MemberAccessExpression(base, member):
            return check_member_access_expr(base, member)


def check_prefix_expr(
    operator: PrefixOperator, expression: Expression
) -> Maybe.Type[Type]:
    check_expression(expression)
    return Maybe.Nothing


def check_binary_expr(
    op: BinOp,
    lhs: Expression,
    rhs: Expression,
) -> Maybe.Type[Type]:
    left = check_expression(lhs).unwrap()
    right = check_expression(rhs).unwrap()

    match (left, right):
        case (Primitive.UInt16, Primitive.UInt16):
            return Maybe.Just(Primitive.UInt16)
        case (Primitive.String, _):
            return Maybe.Nothing
        case (_, Primitive.String):
            return Maybe.Nothing
        case (Primitive.Character, _):
            return Maybe.Nothing
        case (_, Primitive.Character):
            return Maybe.Nothing
        case _:
            assert False


def check_call_expr(
    invokable: Expression, arguments: list[Expression]
) -> Maybe.Type[Type]: ...


def check_subscript_expr(base: Expression, index: Expression) -> Maybe.Type[Type]: ...
def check_member_access_expr(
    base: Expression, member: Identifier
) -> Maybe.Type[Type]: ...
