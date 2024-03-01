from opyl.compile import typecheck
from opyl.compile import parse
from opyl.compile import lex
from opyl.compile import types
from opyl.support.union import Maybe


class TestTypeCheck:
    def test_int_literal(self):
        tokens = lex.tokenize("5").stream
        literal = parse.expr.parse(tokens).unwrap()[0]
        assert typecheck.check_expression(literal).unwrap() is types.Primitive.UInt16

    def test_str_literal(self):
        tokens = lex.tokenize('"Hello, World!"').stream
        literal = parse.expr.parse(tokens).unwrap()[0]
        assert typecheck.check_expression(literal).unwrap() is types.Primitive.Str

    def test_char_literal(self):
        tokens = lex.tokenize("'c'").stream
        literal = parse.expr.parse(tokens).unwrap()[0]
        assert typecheck.check_expression(literal).unwrap() is types.Primitive.Char

    def test_bin_op(self):
        tokens = lex.tokenize("4 + 2").stream
        bin_expr = parse.expr.parse(tokens).unwrap()[0]
        assert typecheck.check_expression(bin_expr).unwrap() is types.Primitive.UInt16

    def test_invalid_str_bin_op(self):
        tokens = lex.tokenize('"Foo" + 2').stream
        bin_expr = parse.expr.parse(tokens).unwrap()[0]
        assert typecheck.check_expression(bin_expr) is Maybe.Nothing

    def test_invalid_str_bin_op_reverse(self):
        tokens = lex.tokenize('2 + "Foo"').stream
        bin_expr = parse.expr.parse(tokens).unwrap()[0]
        assert typecheck.check_expression(bin_expr) is Maybe.Nothing

    def test_invalid_char_bin_op(self):
        tokens = lex.tokenize("'F' + 2").stream
        bin_expr = parse.expr.parse(tokens).unwrap()[0]
        assert typecheck.check_expression(bin_expr) is Maybe.Nothing
