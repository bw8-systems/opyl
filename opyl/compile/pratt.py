import typing as t
from dataclasses import dataclass

from compile.token import Token, Basic
from compile.error import ParseError
from compile import expr
from compile.expr import (
    BinaryExpression,
    BinOp,
    CallExpression,
    InfixExpression,
    PrefixOperator,
    SubscriptExpression,
    PrefixExpression,
)
from support.combinator import PR, Parser, ParseResult
from support.stream import Stream
from support.atoms import just, filt, ident, integer, identity


# TODO: Move into expr.py once precedence solution has been decided on.
def check_precedence(input: Stream[Token]) -> int:
    match input.peek():
        case op if op in BinOp:
            return BinOp(op).precedence()
        case paren if paren is Basic.LeftParenthesis:
            return 8
        case brack if brack is Basic.LeftBracket:
            return 8
        case _:
            return 0


@dataclass
class Expression(Parser[Token, expr.Expression, ParseError]):
    precedence: int

    @t.override
    def parse(
        self, input: Stream[Token]
    ) -> ParseResult.Type[Token, expr.Expression, ParseError]:
        match prefix_parser.parse(input):
            case PR.Match(left, pos):
                ...
            case PR.NoMatch:
                return PR.NoMatch
            case PR.Error(err):
                return PR.Error(err)

        while self.precedence < check_precedence(pos):
            match infix_parser(left).parse(input):
                case PR.Match(expr, pos):
                    left = expr
                case PR.NoMatch:
                    return PR.NoMatch
                case PR.Error(err):
                    return PR.Error(err)

        return PR.NoMatch


def expression(precedence: int) -> Expression:
    return Expression(precedence)


grouped_expr = expression(0).then_ignore(just(Basic.RightParenthesis))


def bin_op_expr(left: expr.Expression) -> Parser[Token, BinaryExpression, ParseError]:
    return (
        filt(lambda tok: tok in BinOp)
        .map(lambda op: BinOp(op))
        .map(lambda op: (op, op.adjusted_precedence()))
        .then_with_ctx(
            lambda op_prec_inp: expression(op_prec_inp[0][1]).parse(op_prec_inp[1])
        )
        .map(
            lambda op_prec_right: BinaryExpression(
                op_prec_right[0][0], left, op_prec_right[1]
            )
        )
    )


def call_expr(function: expr.Expression) -> Parser[Token, CallExpression, ParseError]:
    args = (
        (expression(0).then_ignore(just(Basic.Comma)))
        .repeated()
        .then_ignore(just(Basic.RightParenthesis))
        .map(lambda args: CallExpression(function, args))
    )

    return identity(Basic.LeftParenthesis).ignore_then(args)


def subscript_expr(
    base: expr.Expression,
) -> Parser[Token, SubscriptExpression, ParseError]:
    return (
        identity(Basic.LeftBracket)
        .ignore_then(expression(0))
        .then_ignore(just(Basic.RightBracket))
        .map(lambda index: SubscriptExpression(base, index))
    )


prefix_op_expr = (
    filt(lambda op: op in PrefixOperator)
    .map(lambda op: PrefixOperator(op))
    .then_with_ctx(lambda op_inp: expression(op_inp[0].precedence()).parse(op_inp[1]))
    .map(lambda op_right: PrefixExpression(op_right[0], op_right[1]))
)

prefix_parser = (
    identity(Basic.LeftParenthesis).ignore_then(grouped_expr)
    | prefix_op_expr
    | ident
    | integer
)


def infix_parser(left: expr.Expression) -> Parser[Token, InfixExpression, ParseError]:
    return bin_op_expr(left) | call_expr(left) | subscript_expr(left)
