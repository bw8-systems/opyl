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
)


def test_ident():
    tokens = lex.tokenize("foo").unwrap()[0]
    result = pratt.expr.parse(tokens).unwrap()
    assert result[0] == Identifier("foo")


def test_integer():
    tokens = lex.tokenize("4").unwrap()[0]
    result = pratt.expr.parse(tokens).unwrap()
    assert result[0] == IntegerLiteral(4)


def test_prefix_op_expr_minus():
    tokens = lex.tokenize("-4").unwrap()[0]
    result = pratt.expr.parse(tokens).unwrap()
    assert result[0] == PrefixExpression(
        PrefixOperator.ArithmeticMinus, IntegerLiteral(4)
    )


def test_prefix_op_expr_ident():
    tokens = lex.tokenize("&foo").unwrap()[0]
    result = pratt.expr.parse(tokens).unwrap()
    assert result[0] == PrefixExpression(PrefixOperator.AddressOf, Identifier("foo"))


def test_simple_grouped_expr():
    tokens = lex.tokenize("(4)").unwrap()[0]
    result = pratt.expr.parse(tokens).unwrap()
    assert result[0] == IntegerLiteral(4)


def test_binary_expr():
    tokens = lex.tokenize("1 + 2").unwrap()[0]
    result = pratt.expr.parse(tokens)
    item = result.unwrap()[0]
    assert item == BinaryExpression(
        BinOp.Addition, IntegerLiteral(1), IntegerLiteral(2)
    )


def test_subscript_expr():
    tokens = lex.tokenize("foo[bar]").unwrap()[0]
    result = pratt.expr.parse(tokens)
    item = result.unwrap()[0]
    assert item == SubscriptExpression(Identifier("foo"), Identifier("bar"))


def test_subscript_expr_complex_index():
    tokens = lex.tokenize("foo[1 + 2]").unwrap()[0]
    result = pratt.expr.parse(tokens)
    item = result.unwrap()[0]
    assert item == SubscriptExpression(
        Identifier("foo"),
        BinaryExpression(BinOp.Addition, IntegerLiteral(1), IntegerLiteral(2)),
    )


def test_call_expr():
    # TODO: Although trailing commas are allowed here, they shouldn't be required.
    # Parser isn't flexible to that right now because SeparatedBy is not available.
    tokens = lex.tokenize("function(foo, 1,)").unwrap()[0]
    result = pratt.expr.parse(tokens)
    item = result.unwrap()[0]
    assert item == CallExpression(
        Identifier("function"), [Identifier("foo"), IntegerLiteral(1)]
    )


def test_call_expr_no_args():
    tokens = lex.tokenize("function()").unwrap()[0]
    result = pratt.expr.parse(tokens)
    item = result.unwrap()[0]
    assert item == CallExpression(Identifier("function"), [])


def test_grouped_expr_line_breaks():
    tokens = lex.tokenize(
        """(
            5 + 2
        )
        """
    ).unwrap()[0]
    result = pratt.expr.parse(tokens)
    item = result.unwrap()[0]
    assert item == BinaryExpression(
        BinOp.Addition, IntegerLiteral(5), IntegerLiteral(2)
    )


def test_grouped_expr_nested_line_breaks():
    tokens = lex.tokenize(
        """(
            5 + (
                2 + 3
            )
        )
        """
    ).unwrap()[0]
    result = pratt.expr.parse(tokens)
    item = result.unwrap()[0]
    assert item == BinaryExpression(
        BinOp.Addition,
        IntegerLiteral(5),
        BinaryExpression(BinOp.Addition, IntegerLiteral(2), IntegerLiteral(3)),
    )


def test_function_call_with_line_breaks():
    tokens = lex.tokenize(
        """function(
            alpha,
            bravo,
            charlie,
        )
        """
    ).unwrap()[0]
    result = pratt.expr.parse(tokens)
    item = result.unwrap()[0]
    assert item == CallExpression(
        Identifier("function"),
        [Identifier("alpha"), Identifier("bravo"), Identifier("charlie")],
    )
