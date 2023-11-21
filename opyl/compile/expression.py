from dataclasses import dataclass

from opyl import errors
from opyl import nodes
from opyl.compile.nodes import BinaryOperator, BinaryExpression

from opyl import combinators as comb
from opyl.compile.lexemes import IntegerLiteral, Primitive, PrimitiveKind
from opyl.compile.positioning import Span, Stream

type Token = IntegerLiteral | Primitive


@dataclass
class ExpressionParser(comb.Combinator[nodes.Expression]):
    def __post_init__(self):
        self.integer_literal = comb.IntegerLiteral(self.stream)

    def __call__(self) -> nodes.Expression:
        return self.pratt(0)

    def prefix(self) -> nodes.Expression:
        peeked = self.stream.peek()
        if peeked is None:
            raise errors.UnexpectedEOF()

        if isinstance(peeked, IntegerLiteral):
            self.stream.advance_by(1)
            return nodes.IntegerLiteral(peeked.span, peeked.integer)

        if isinstance(peeked, Primitive):
            match peeked.kind:
                case PrimitiveKind.Hyphen:
                    self.stream.advance_by(2)
                    lit = self.integer_literal()
                    return nodes.IntegerLiteral(lit.span, lit.integer)
                case PrimitiveKind.LeftParenthesis:
                    self.stream.advance_by(1)
                    return self.grouped_expression()
                case _:
                    pass

        raise errors.UnexpectedToken()

    def grouped_expression(self) -> nodes.Expression:
        expr = self.pratt(0)

        peeked = self.stream.peek()
        if (
            isinstance(peeked, Primitive)
            and peeked.kind is PrimitiveKind.RightParenthesis
        ):
            self.stream.advance_by(1)
            return expr

        raise errors.UnexpectedToken()

    def binary_op(
        self, left: nodes.Expression, op: BinaryOperator, precedence: int
    ) -> nodes.Expression:
        right = self.pratt(precedence)
        return BinaryExpression(
            span=left.span + right.span, operator=op, left=left, right=right
        )

    def postfix_bang(
        self, left: nodes.Expression, op: nodes.UnaryOperator
    ) -> nodes.Expression:
        return nodes.UnaryExpression(span=Span.default(), operator=op, expr=left)

    def pratt(self, precedence_limit: int) -> nodes.Expression:
        return self.pratt_loop(precedence_limit, self.prefix())

    def pratt_loop(
        self, precedence_limit: int, left: nodes.Expression
    ) -> nodes.Expression:
        peeked = self.stream.peek()
        if not (
            isinstance(peeked, Primitive) and peeked.kind in BinaryOperator.values()
        ):
            return left

        operator = BinaryOperator(peeked.kind)
        precedence = operator.precedence()
        final_precedence = (
            precedence - 1 if operator.is_right_associative() else precedence
        )
        if precedence <= precedence_limit:
            return left

        self.stream.next()

        right = self.pratt(final_precedence)
        new_left = BinaryExpression(Span.default(), operator, left, right)
        return self.pratt_loop(precedence_limit, new_left)


if __name__ == "__main__":
    from pprint import pprint

    tokens: list[Token] = [
        IntegerLiteral(
            integer=1,
            span=Span.default(),
        ),
        Primitive(kind=PrimitiveKind.Plus, span=Span.default()),
        IntegerLiteral(
            integer=2,
            span=Span.default(),
        ),
        Primitive(kind=PrimitiveKind.Hyphen, span=Span.default()),
        IntegerLiteral(
            integer=3,
            span=Span.default(),
        ),
        Primitive(kind=PrimitiveKind.Asterisk, span=Span.default()),
        IntegerLiteral(
            integer=4,
            span=Span.default(),
        ),
        Primitive(kind=PrimitiveKind.Plus, span=Span.default()),
        IntegerLiteral(
            integer=5,
            span=Span.default(),
        ),
        Primitive(kind=PrimitiveKind.ForwardSlash, span=Span.default()),
        IntegerLiteral(
            integer=6,
            span=Span.default(),
        ),
        Primitive(kind=PrimitiveKind.Caret, span=Span.default()),
        IntegerLiteral(
            integer=7,
            span=Span.default(),
        ),
        Primitive(kind=PrimitiveKind.Hyphen, span=Span.default()),
        IntegerLiteral(
            integer=8,
            span=Span.default(),
        ),
        Primitive(kind=PrimitiveKind.Asterisk, span=Span.default()),
        IntegerLiteral(
            integer=9,
            span=Span.default(),
        ),
    ]

    parser = ExpressionParser(Stream(tokens))
    pprint(parser())
