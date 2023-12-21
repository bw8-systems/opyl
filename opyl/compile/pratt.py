import typing as t
from dataclasses import dataclass

from opyl.compile.token import Token, Basic
from opyl.compile.error import ParseError
from opyl.compile import expr as ex
from opyl.compile.expr import (
    BinaryExpression,
    BinOp,
    CallExpression,
    InfixExpression,
    PrefixOperator,
    SubscriptExpression,
    PrefixExpression,
)
from opyl.support.combinator import PR, Parser, ParseResult
from opyl.support.stream import Stream
from opyl.support.atoms import just, filt, ident, integer, newlines
from opyl.support.union import Maybe


# TODO: Move into expr.py once precedence solution has been decided on.
def check_precedence(input: Stream[Token]) -> int:
    match input.peek():
        case Maybe.Just(tok):
            match tok:
                case op if isinstance(op, Basic) and op in BinOp:
                    return BinOp(op).precedence()
                case paren if paren is Basic.LeftParenthesis:
                    return 8
                case brack if brack is Basic.LeftBracket:
                    return 8
                case _:
                    return 0
        case Maybe.Nothing:
            return 0


@dataclass
class Expression(Parser[Token, ex.Expression, ParseError]):
    precedence: int

    @t.override
    def parse(
        self, input: Stream[Token]
    ) -> ParseResult.Type[Token, ex.Expression, ParseError]:
        match prefix_parser.parse(input):
            case PR.Match(left, pos):
                ...
            case PR.NoMatch:
                return PR.NoMatch
            case PR.Error(err):
                return PR.Error(err)

        while self.precedence < check_precedence(pos):
            match infix_parser(left).parse(pos):
                case PR.Match(expr, pos):
                    left = expr
                case PR.NoMatch:
                    return PR.NoMatch
                case PR.Error(err):
                    return PR.Error(err)

        return PR.Match(left, pos)


def expression(precedence: int) -> Expression:
    return Expression(precedence)


expr = expression(0)

grouped_expr = (
    just(Basic.LeftParenthesis)
    .ignore_then(newlines)
    .ignore_then(expr.then_ignore(newlines).then_ignore(just(Basic.RightParenthesis)))
)


def bin_op_expr(left: ex.Expression) -> Parser[Token, BinaryExpression, ParseError]:
    return (
        # TODO: Don't like isinstance here and elsewhere
        filt(lambda tok: isinstance(tok, Basic) and tok in BinOp)
        .map(lambda op: BinOp(op))
        .map(lambda op: (op, op.adjusted_precedence()))
        .then_with_ctx(lambda op_prec, input: expression(op_prec[1]).parse(input))
        .map(
            lambda op_prec_right: BinaryExpression(
                op_prec_right[0][0], left, op_prec_right[1]
            )
        )
    )


def call_expr(function: ex.Expression) -> Parser[Token, CallExpression, ParseError]:
    args = (
        expr.separated_by(just(Basic.Comma).then_ignore(newlines))
        .allow_trailing()
        .then_ignore(newlines)
        .then_ignore(just(Basic.RightParenthesis))
    ).map(lambda args: CallExpression(function, args))

    return just(Basic.LeftParenthesis).ignore_then(newlines).ignore_then(args)


def subscript_expr(
    base: ex.Expression,
) -> Parser[Token, SubscriptExpression, ParseError]:
    return (
        just(Basic.LeftBracket)
        .ignore_then(newlines)
        .ignore_then(expr)
        .then_ignore(newlines)
        .then_ignore(just(Basic.RightBracket))
        .map(lambda index: SubscriptExpression(base, index))
    )


prefix_op_expr = (
    filt(lambda op: isinstance(op, Basic) and op in PrefixOperator)
    .map(lambda op: PrefixOperator(op))
    .then_with_ctx(lambda op, input: expression(op.precedence()).parse(input))
    .map(lambda op_right: PrefixExpression(op_right[0], op_right[1]))
)

prefix_parser = grouped_expr | prefix_op_expr | ident | integer


def infix_parser(left: ex.Expression) -> Parser[Token, InfixExpression, ParseError]:
    return bin_op_expr(left) | call_expr(left) | subscript_expr(left)
