from opyl import lexemes
from opyl import lex
from opyl import nodes
from opyl import errors
from opyl.compile.nodes import Expression
from opyl.compile.positioning import Stream, Span
from opyl.compile.lexemes import PrimitiveKind

type Token = lexemes.Identifier | lexemes.IntegerLiteral | lexemes.Primitive


def expr(tokens: Stream[Token]) -> Expression:
    return expr_bp(tokens, 0)


def expr_bp(tokens: Stream[Token], min_bp: int) -> Expression:
    lhs: nodes.Expression

    match tokens.peek():
        case lexemes.IntegerLiteral(span, lit):
            lhs = nodes.IntegerLiteral(span, lit)
        case lexemes.Identifier(span, lit):
            lhs = nodes.Identifier(span, lit)
        case lexemes.Primitive(span, kind) if nodes.UnaryOperator.is_unyop(kind):
            _, right_bp = prefix_binding_power(nodes.UnaryOperator(kind))
        case _:
            raise errors.UnexpectedToken(tokens.peek())

    tokens.next()

    while True:
        peeked = tokens.peek()
        if peeked is None:
            break

        if not nodes.BinaryOperator.is_binop(peeked):
            raise errors.UnexpectedToken()

        tokens.next()
        operator = nodes.BinaryOperator(peeked.kind)

        left_bp, right_bp = infix_binding_power(operator)
        if left_bp < min_bp:
            break

        rhs = expr_bp(tokens, right_bp)
        lhs = nodes.BinaryExpression(
            span=Span.default(),
            operator=operator,
            left=lhs,
            right=rhs,
        )

    return lhs


def prefix_binding_power(operator: nodes.UnaryOperator) -> tuple[None, int]:
    try:
        return {
            nodes.UnaryOperator.Pos: (None, 5),
            nodes.UnaryOperator.Neg: (None, 5),
        }[operator]
    except KeyError:
        raise errors.UnexpectedToken(operator)


def infix_binding_power(operator: nodes.BinaryOperator) -> tuple[int, int]:
    try:
        return {
            nodes.BinaryOperator.Add: (1, 2),
            nodes.BinaryOperator.Sub: (1, 2),
            nodes.BinaryOperator.Mul: (3, 4),
            nodes.BinaryOperator.Div: (3, 4),
            nodes.BinaryOperator.Compose: (8, 7),
        }[operator]
    except KeyError:
        raise errors.UnexpectedToken(operator)


if __name__ == "__main__":
    from pprint import pprint

    tokens: list[Token] = [
        lexemes.Identifier(
            identifier="f",
            span=Span.default(),
        ),
        lexemes.Primitive(kind=PrimitiveKind.Period, span=Span.default()),
        lexemes.Identifier(
            identifier="g",
            span=Span.default(),
        ),
        lexemes.Primitive(kind=PrimitiveKind.Period, span=Span.default()),
        lexemes.Identifier(
            identifier="h",
            span=Span.default(),
        ),
    ]

    pprint(expr(Stream(tokens)))
