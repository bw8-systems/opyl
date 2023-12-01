from dataclasses import dataclass

from compile import nodes
from compile import combinators as comb
from compile.nodes import PrefixOperator, BinaryOperator
from compile.positioning import Span

# from compile import lexemes
from compile.lexemes import (
    Primitive,
    Identifier,
    IntegerLiteral,
    PrimitiveKind,
)
from compile import errors


@dataclass
class ExpressionParser(comb.Parser[nodes.Expression]):
    def parse(self) -> nodes.Expression:
        return self.expression(0)

    def expression(self, precedence: int) -> nodes.Expression:
        match self.tokens.next():
            case Primitive(span, PrimitiveKind.LeftParenthesis):
                left = self.grouped_expression()
            case Primitive(span, kind) if PrefixOperator.is_prefix_op(kind):
                prefix_operator = PrefixOperator(kind)
                left = self.prefix_operator_expression(prefix_operator, span)
            case Identifier(span, name):
                left = nodes.Identifier(span, name)
            case IntegerLiteral(span, integer):
                left = nodes.IntegerLiteral(span, integer)
            case _:
                raise errors.UnexpectedToken()

        while precedence < self.check_precedence():
            match self.tokens.next():
                case Primitive(span, kind) if BinaryOperator.is_binary_op(kind):
                    operator = BinaryOperator(kind)
                    left = self.binary_operator_expression(left, operator)
                case Primitive(_, PrimitiveKind.LeftParenthesis):
                    left = self.call_expression(left)
                case Primitive(_, PrimitiveKind.LeftBracket):
                    left = self.subscript_expression(left)
                case _:
                    raise errors.UnexpectedToken()

        return left

    def check_precedence(self) -> int:
        match self.tokens.peek():
            case Primitive(_, kind) if BinaryOperator.is_binary_op(kind):
                return BinaryOperator(kind).precedence()
            case Primitive(_, PrimitiveKind.LeftParenthesis):
                # TODO: How to represent precedence levels cleanly?
                # For now, just a high precedence level to bind calls tightly.
                return 8
            case Primitive(_, PrimitiveKind.LeftBracket):
                return 8
            case _:
                return 0

    def prefix_operator_expression(
        self,
        operator: nodes.PrefixOperator,
        start_span: Span,
    ) -> nodes.Expression:
        right = self.expression(operator.precedence())
        return nodes.PrefixExpression(
            span=start_span + right.span, operator=operator, expr=right
        )

    def binary_operator_expression(
        self,
        left: nodes.Expression,
        operator: BinaryOperator,
    ) -> nodes.Expression:
        precedence = operator.precedence()
        if operator.is_right_associative():
            precedence -= 1

        right = self.expression(precedence)
        return nodes.BinaryExpression(
            span=left.span + right.span, operator=operator, left=left, right=right
        )

    def grouped_expression(self) -> nodes.Expression:
        left = self.parse()
        closing = self.tokens.next()
        assert (
            isinstance(closing, Primitive)
            and closing.kind is PrimitiveKind.RightParenthesis
        )
        return left

    def call_expression(self, function: nodes.Expression) -> nodes.Expression:
        maybe_right_paren = self.maybe(
            comb.PrimitiveTerminal(self.tokens, PrimitiveKind.RightParenthesis)
        ).parse()

        if maybe_right_paren is not None:
            return nodes.CallExpression(
                span=function.span + maybe_right_paren.span,
                function=function,
                arguments=[],
            )

        arg = self.maybe(self).parse()
        if arg is None:
            raise errors.UnexpectedToken()

        args = self.many(
            comb.PrimitiveTerminal(self.tokens, PrimitiveKind.Comma).consume_before(
                self
            )
        ).parse()
        args.append(arg)

        right_paren = comb.PrimitiveTerminal(
            self.tokens, PrimitiveKind.RightParenthesis
        ).parse()

        return nodes.CallExpression(
            span=function.span + right_paren.span,
            function=function,
            arguments=args,
        )

    def subscript_expression(self, base: nodes.Expression) -> nodes.Expression:
        index = self.parse()
        closing_brace = comb.PrimitiveTerminal(
            self.tokens, PrimitiveKind.RightBracket
        ).parse()
        return nodes.SubscriptExpression(
            span=base.span + closing_brace.span,
            base=base,
            index=index,
        )
