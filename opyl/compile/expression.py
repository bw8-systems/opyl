from enum import Enum
from dataclasses import dataclass
import typing as t

# from opyl import lexemes
# from opyl.compile.lexemes import IntegerLiteral, Primitive, PrimitiveKind
# from opyl.compile.positioning import Span, TextPosition


@dataclass
class Int:
    value: int


class BinOp(Enum):
    Add = "+"
    Sub = "-"
    Mul = "*"
    Div = "/"
    Pow = "^"


class UnaryOp(Enum):
    Fact = "!"


type Token = Int | BinOp | t.Literal["("] | t.Literal[")"]
type Expr = Int | BinExpr | UnaryExpr


@dataclass
class BinExpr:
    op: BinOp
    lhs: Expr
    rhs: Expr


@dataclass
class UnaryExpr:
    op: UnaryOp
    lhs: Expr


def precedence(binop: BinOp) -> int:
    return {
        BinOp.Add: 1,
        BinOp.Sub: 1,
        BinOp.Mul: 2,
        BinOp.Div: 2,
        BinOp.Pow: 3,
    }[binop]


def is_right_associative(binop: BinOp) -> bool:
    return {
        BinOp.Add: False,
        BinOp.Sub: False,
        BinOp.Mul: False,
        BinOp.Div: False,
        BinOp.Pow: True,
    }[binop]


def parse(tokens: list[Token]) -> Expr | None:
    match pratt(0, tokens):
        case [expr, *_tokens_after_expr]:
            return expr
        case None:
            return None


def prefix(tokens: list[Token]) -> tuple[Expr, list[Token]] | None:
    match tokens:
        case []:
            return None
        case [Int(n), *rest]:
            return Int(n), rest
        case [BinOp.Sub, Int(n), *rest]:
            return Int(-n), rest
        case ["(", *rest]:
            return grouped_expr(rest)
        case [")", _]:
            return None
        case _:
            return None


def grouped_expr(tokens: list[Token]) -> tuple[Expr, list[Token]] | None:
    match pratt(0, tokens):
        case None:
            return None
        case (expr, [")", *rest]):
            return expr, rest
        case _:
            return None


def binary_op(
    left: Expr, op: BinOp, precedence: int, tokens_after_op: list[Token]
) -> tuple[Expr, list[Token]] | None:
    match pratt(precedence, tokens_after_op):
        case None:
            return None
        case (right, tokens_after_right):
            return BinExpr(op, left, right), tokens_after_right


def postfix_bang(
    left: Expr, op: BinOp, tokens_after_op: list[Token]
) -> tuple[Expr, list[Token]] | None:
    return UnaryExpr(UnaryOp.Fact, left), tokens_after_op


def pratt(prec_limit: int, tokens: list[Token]) -> tuple[Expr, list[Token]] | None:
    match prefix(tokens):
        case None:
            return None
        case (left, tokens_after_prefix):
            return pratt_loop(prec_limit, left, tokens_after_prefix)


def pratt_loop(
    prec_limit: int, left: Expr, tokens_after_left: list[Token]
) -> tuple[Expr, list[Token]] | None:
    match tokens_after_left:
        case [BinOp() as op, *tokens_after_op]:
            op_prec = precedence(op)
            final_prec = op_prec - 1 if is_right_associative(op) else op_prec
            if op_prec <= prec_limit:
                return left, tokens_after_left
            match pratt(final_prec, tokens_after_op):
                case (right, tokens_after_child):
                    new_left = BinExpr(op, left, right)
                    return pratt_loop(prec_limit, new_left, tokens_after_child)
                case None:
                    return None
        case _:
            return left, tokens_after_left


if __name__ == "__main__":
    from pprint import pprint

    tokens: list[Token] = [
        Int(1),
        BinOp.Add,
        Int(2),
        BinOp.Sub,
        Int(3),
        BinOp.Mul,
        Int(4),
        BinOp.Add,
        Int(5),
        BinOp.Div,
        Int(6),
        BinOp.Pow,
        Int(7),
        BinOp.Sub,
        Int(8),
        BinOp.Mul,
        Int(9),
    ]

    # tokens: list[lexemes.Token] = [
    #     lexemes.IntegerLiteral(
    #         integer=1,
    #         span=Span.default(),
    #     ),
    #     lexemes.Primitive(kind=PrimitiveKind.Plus, span=Span.default()),
    #     lexemes.IntegerLiteral(
    #         integer=2,
    #         span=Span.default(),
    #     ),
    #     lexemes.Primitive(kind=PrimitiveKind.Hyphen, span=Span.default()),
    #     lexemes.IntegerLiteral(
    #         integer=3,
    #         span=Span.default(),
    #     ),
    #     lexemes.Primitive(kind=PrimitiveKind.Asterisks, span=Span.default())
    #     lexemes.IntegerLiteral(
    #         integer=4,
    #         span=Span.default(),
    #     ),
    #     lexemes.IntegerLiteral(
    #         integer=5,
    #         span=Span.default(),
    #     ),
    #     lexemes.IntegerLiteral(
    #         integer=6,
    #         span=Span.default(),
    #     ),
    #     lexemes.IntegerLiteral(
    #         integer=7,
    #         span=Span.default(),
    #     ),
    #     lexemes.IntegerLiteral(
    #         integer=8,
    #         span=Span.default(),
    #     ),
    #     lexemes.IntegerLiteral(
    #         integer=9,
    #         span=Span.default(),
    #     ),
    # ]
    parsed = parse(tokens)
    pprint(parsed)
