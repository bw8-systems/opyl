import functools
from opyl.compile import lex
from opyl.compile import pratt
from opyl.compile.token import IntegerLiteral, Identifier
from opyl.compile.expr import (
    PrefixExpression,
    PrefixOperator,
    BinaryExpression,
    BinOp,
    CallExpression,
    SubscriptExpression,
    MemberAccessExpression,
)
from .utils import parse_test


expr_test = functools.partial(parse_test, pratt.expr)


def test_ident():
    expr_test("foo", Identifier("foo"))


def test_integer():
    expr_test("4", IntegerLiteral(4))


def test_prefix_op_expr_minus():
    expr_test(
        "-4",
        PrefixExpression(PrefixOperator.ArithmeticMinus, IntegerLiteral(4)),
    )


def test_prefix_op_expr_ident():
    expr_test("&foo", PrefixExpression(PrefixOperator.AddressOf, Identifier("foo")))


def test_simple_grouped_expr():
    expr_test("(4)", IntegerLiteral(4))


def test_binary_expr():
    expr_test(
        "1 + 2", BinaryExpression(BinOp.Addition, IntegerLiteral(1), IntegerLiteral(2))
    )


def test_subscript_expr():
    expr_test("foo[bar]", SubscriptExpression(Identifier("foo"), Identifier("bar")))


def test_invalid_subscript_expr():
    tokens = lex.tokenize("foo[bar").unwrap()[0]
    result = pratt.expr.parse(tokens)
    item = result.unwrap_err()[0]
    assert item.expected == "']'"


def test_subscript_expr_complex_index():
    expr_test(
        "foo[1 + 2]",
        SubscriptExpression(
            Identifier("foo"),
            BinaryExpression(BinOp.Addition, IntegerLiteral(1), IntegerLiteral(2)),
        ),
    )


def test_call_expr_with_trailing_comma():
    expr_test(
        "function(foo, 1,)",
        CallExpression(Identifier("function"), [Identifier("foo"), IntegerLiteral(1)]),
    )


def test_call_expr_no_trailing_comma():
    expr_test(
        "function(foo, 1)",
        CallExpression(Identifier("function"), [Identifier("foo"), IntegerLiteral(1)]),
    )


def test_call_expr_no_args():
    expr_test("function()", CallExpression(Identifier("function"), []))


def test_invalid_call_expr():
    tokens = lex.tokenize("function(foo, 1").unwrap()[0]
    result = pratt.expr.parse(tokens)
    item = result.unwrap_err()[0]
    assert item.expected == "')'"


def test_member_access():
    expr_test("foo.bar", MemberAccessExpression(Identifier("foo"), Identifier("bar")))


def test_invalid_member_access():
    tokens = lex.tokenize("foo.5").unwrap()[0]
    result = pratt.expr.parse(tokens)
    item = result.unwrap_err()[0]
    assert item.expected == "identifier"


def test_grouped_expr_line_breaks():
    expr_test(
        """(
            5 + 2
        )
        """,
        BinaryExpression(BinOp.Addition, IntegerLiteral(5), IntegerLiteral(2)),
    )


def test_grouped_expr_nested_line_breaks():
    expr_test(
        """(
            5 + (
                2 + 3
            )
        )
        """,
        BinaryExpression(
            BinOp.Addition,
            IntegerLiteral(5),
            BinaryExpression(BinOp.Addition, IntegerLiteral(2), IntegerLiteral(3)),
        ),
    )


def test_function_call_with_line_breaks():
    expr_test(
        """function(
            alpha,
            bravo,
            charlie,
        )
        """,
        CallExpression(
            Identifier("function"),
            [Identifier("alpha"), Identifier("bravo"), Identifier("charlie")],
        ),
    )


def test_unclosed_group():
    tokens = lex.tokenize("(4 + 2").unwrap()[0]
    result = pratt.expr.parse(tokens)
    item = result.unwrap_err()[0]
    assert item.expected == "')'"
