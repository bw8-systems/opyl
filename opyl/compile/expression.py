from opyl import nodes
from opyl.compile.nodes import BinaryOperator, BinaryExpression

from opyl.compile.lexemes import IntegerLiteral, Primitive, PrimitiveKind
from opyl.compile.positioning import Span, Stream

type Token = IntegerLiteral | Primitive


def parse(tokens: Stream[Token]) -> nodes.Expression | None:
    return pratt(0, tokens)


def prefix(tokens: Stream[Token]) -> nodes.Expression | None:
    peeked = tokens.peek()
    if isinstance(peeked, IntegerLiteral):
        tokens.next()
        return nodes.IntegerLiteral(peeked.span, peeked.integer)

    return None


def pratt(precedence_limit: int, tokens: Stream[Token]) -> nodes.Expression | None:
    left = prefix(tokens)
    if left is None:
        return None

    return pratt_loop(precedence_limit, left, tokens)


def pratt_loop(
    precedence_limit: int, left: nodes.Expression, tokens: Stream[Token]
) -> nodes.Expression | None:
    peeked = tokens.peek()
    if not (isinstance(peeked, Primitive) and peeked.kind in BinaryOperator.values()):
        return left

    operator = BinaryOperator(peeked.kind)
    precedence = operator.precedence()
    if precedence <= precedence_limit:
        return left

    tokens.next()
    right = pratt(precedence, tokens)
    if right is None:
        return None

    new_left = BinaryExpression(Span.default(), operator, left, right)
    return pratt_loop(precedence_limit, new_left, tokens)


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
    parsed = parse(Stream(tokens))
    pprint(parsed)
