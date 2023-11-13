from dataclasses import dataclass

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
        return self.integer_literal.parse()

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
        if precedence <= precedence_limit:
            return left

        self.stream.next()

        right = self.pratt(precedence)
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
