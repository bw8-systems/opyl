import typing as t
from abc import ABC, abstractmethod
from dataclasses import dataclass

from opyl.compile import errors
from opyl.compile import nodes
from opyl.compile import lexemes
from opyl.compile.lexemes import PrimitiveKind as PK
from opyl.compile.positioning import Stream


def operator_precedence(token: lexemes.Token) -> int:
    ...


@dataclass
class Parser:
    tokens: Stream[lexemes.Token]

    def expression(self, precedence: int) -> nodes.Expression | None:
        peeked = self.tokens.peek()
        match peeked:
            case lexemes.Identifier():
                self.tokens.next()
                left = self.parse_name(peeked)
            case lexemes.Primitive(_, kind) if kind in (PK.Plus, PK.Hyphen):
                self.tokens.next()
                left = self.parse_prefix(peeked)
            case None:
                raise errors.UnexpectedEOF()
            case _:
                raise errors.UnexpectedToken()

        while precedence < operator_precedence(peeked):
            peeked = self.tokens.peek()
            match peeked:


        # peeked = self.tokens.peek()
        # assert peeked is not None

        # try:
        #     infix = self.infix_parselet(peeked)
        # except KeyError:
        #     infix = None

        # if infix is None:
        #     return left

        # token = self.tokens.next()
        # return infix.parse(self, left, token)

    def parse_name(self, token: lexemes.Identifier) -> nodes.Expression:
        ...

    def parse_prefix(self, token: lexemes.Token) -> nodes.Expression:
        ...


class PrefixParselet(ABC):
    @abstractmethod
    def parse(self, parser: Parser, token: lexemes.Token) -> nodes.Expression:
        raise NotImplementedError()

    @property
    @abstractmethod
    def precedence(self) -> int:
        raise NotImplementedError()


@dataclass
class NameParselet(PrefixParselet):
    @t.override
    def parse(self, parser: Parser, token: lexemes.Token) -> nodes.Expression:
        assert isinstance(token, lexemes.Identifier)
        return nodes.Identifier(span=token.span, name=token.identifier)

    @property
    @t.override
    def precedence(self) -> int:
        return 0


class PrefixOperatorParselet(PrefixParselet):
    @t.override
    def parse(self, parser: Parser, token: lexemes.Token) -> nodes.Expression:
        assert nodes.PrefixOperator.is_prefix_op(token)

        operand = parser.expression()
        assert operand is not None
        return nodes.PrefixExpression(
            span=token.span, operator=nodes.PrefixOperator(token.kind), expr=operand
        )

    @property
    @t.override
    def precedence(self) -> int:
        return 0


class InfixParselet(ABC):
    @abstractmethod
    def parse(
        self, parser: Parser, left: nodes.Expression, token: lexemes.Token
    ) -> nodes.Expression:
        raise NotImplementedError()

    @property
    @abstractmethod
    def precedence(self) -> int:
        raise NotImplementedError()


class BinaryOperatorParselet(InfixParselet):
    @t.override
    def parse(
        self, parser: Parser, left: nodes.Expression, token: lexemes.Token
    ) -> nodes.Expression:
        assert nodes.InfixOperator.is_binary_op(token)

        right = parser.expression()
        return nodes.InfixExpression(
            left.span + right.span,
            operator=nodes.InfixOperator(token.kind),
            left=left,
            right=right,
        )

    @property
    @t.override
    def precedence(self) -> int:
        return 0


class PostfixOperatorParselet(InfixParselet):
    @t.override
    def parse(
        self, parser: Parser, left: nodes.Expression, token: lexemes.Token
    ) -> nodes.Expression:
        assert nodes.PostfixOperator.is_postfix_op(token)

        return nodes.PostfixExpression(
            span=left.span + token.span,
            operator=nodes.PostfixOperator(token.kind),
            expr=left,
        )

    @property
    @t.override
    def precedence(self) -> int:
        return 0


# class FunctionCallParselet(InfixParselet):
#     @t.override
#     def parse(
#         self, parser: Parser, left: nodes.Expression, token: lexemes.Token
#     ) -> nodes.Expression:
#         """Left is function name, token is LeftParen"""

# from pprint import pprint

# tokens = [
#     lexemes.Identifier(identifier="foo", span=Span.default()),
#     lexemes.Primitive(kind=lexemes.PrimitiveKind.Plus, span=Span.default()),
#     lexemes.Identifier(identifier="bar", span=Span.default()),
# ]

# parser = Parser(tokens=Stream(tokens))
# expr = parser.expression()

# pprint(parser.expression())
# pprint(parser.expression())
