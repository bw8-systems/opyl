import typing as t
from dataclasses import dataclass

from opyl.compile.error import ParseError
from opyl.compile.expr import (
    Expression,
    PrefixOperator,
    BinaryOperator,
    BinaryExpression,
    PrefixExpression,
    SubscriptExpression,
    CallExpression,
)
from opyl.support.combinator import Parser, ParseResult
from opyl.support.stream import Stream
from opyl.support.span import Span

from opyl.compile.token import (
    Token,
    Identifier,
    IntegerLiteral,
    Basic,
)


@dataclass
class ExpressionParser(Parser[Token, Expression, ParseError]):
    @t.override
    def parse(
        self, input: Stream[Token]
    ) -> ParseResult.Type[Token, Expression, ParseError]:
        return self.expression(input, 0)

    def expression(
        self, input: Stream[Token], precedence: int
    ) -> ParseResult.Type[Token, Expression, ParseError]:
        match input.next():
            case Basic(span, Basic.LeftParenthesis):
                left = self.grouped_expression(input)
            case Basic(span, kind) if PrefixOperator.is_prefix_op(kind):
                prefix_operator = PrefixOperator(kind)
                left = self.prefix_operator_expression(input, prefix_operator, span)
            case Identifier(_, name):
                left = Identifier(name)
            case IntegerLiteral(_, integer):
                left = IntegerLiteral(integer)
            case _:
                return ParseResult.NoMatch

        while precedence < self.check_precedence(input):
            match input.next():
                case Basic(span, kind) if BinaryOperator.is_binary_op(kind):
                    operator = BinaryOperator(kind)
                    left = self.binary_operator_expression(input, left.item, operator)
                case Basic(_, Basic.LeftParenthesis):
                    left = self.call_expression(input, left)
                case Primitive(_, Basic.LeftBracket):
                    left = self.subscript_expression(input, left)
                case _:
                    return ParseResult.NoMatch

        return ParseResult.Match(left)

    def check_precedence(self, input: Stream[Token]) -> int:
        match input.peek():
            case Basic(_, kind) if BinaryOperator.is_binary_op(kind):
                return BinaryOperator(kind).precedence()
            case Basic(_, Basic.LeftParenthesis):
                # TODO: How to represent precedence levels cleanly?
                # For now, just a high precedence level to bind calls tightly.
                return 8
            case Basic(_, Basic.LeftBracket):
                return 8
            case _:
                return 0

    def prefix_operator_expression(
        self,
        input: Stream[Token],
        operator: PrefixOperator,
        start_span: Span,
    ) -> Expression:
        right = self.expression(input, operator.precedence())
        return PrefixExpression(
            span=start_span + right.span, operator=operator, expr=right
        )

    def binary_operator_expression(
        self,
        input: Stream[Token],
        left: Expression,
        operator: BinaryOperator,
    ) -> Expression:
        precedence = operator.precedence()
        if operator.is_right_associative():
            precedence -= 1

        right = self.expression(input, precedence)
        return BinaryExpression(
            span=left.span + right.span, operator=operator, left=left, right=right
        )

    def grouped_expression(self, input: Stream[Token]) -> ParseResult.Type[Expression]:
        left = self.parse(input)
        closing = input.next()
        assert closing is Basic.RightParenthesis
        return left

    def call_expression(
        self, input: Stream[Token], function: Expression
    ) -> ParseResult.Type[Expression]:
        maybe_right_paren = self.maybe(
            comb.PrimitiveTerminal(self.tokens, PrimitiveKind.RightParenthesis)
        ).parse()

        if maybe_right_paren is not None:
            return CallExpression(
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

        return CallExpression(
            span=function.span + right_paren.span,
            function=function,
            arguments=args,
        )

    def subscript_expression(
        self, input: Stream[Token], base: Expression
    ) -> ParseResult.Type[Expression]:
        index = self.parse(input)
        closing_brace = comb.PrimitiveTerminal(
            self.tokens, PrimitiveKind.RightBracket
        ).parse()
        return SubscriptExpression(
            span=base.span + closing_brace.span,
            base=base,
            index=index,
        )
