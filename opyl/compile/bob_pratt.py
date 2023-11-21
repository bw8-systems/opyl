import typing as t
from abc import ABC, abstractmethod
from dataclasses import dataclass

from opyl import nodes
from opyl import lexemes
from opyl.compile.positioning import Stream, Span


@dataclass
class Parser:
    tokens: Stream[lexemes.Token]

    def __post_init__(self):
        # Given a token type, these maps return a parser corresponding to it.
        self.prefix_parselets = dict[type[lexemes.Token], PrefixParselet]()
        self.infix_parselets = dict[type[lexemes.Token], InfixParselet]()

        # Now populate the
        # Define the grammar - this says that a "lexeme.Identifier" token should
        # be parsed via the "NameParselet" parser.
        self.register(lexemes.Identifier, NameParselet())

        # There is a single prefix parselet for the simple prefix arithmetic operators.
        # these calls do the same as above, but implicity map them to PrefixOperatorParselet.
        self.prefix(lexemes.PrimitiveKind.Plus)
        self.prefix(lexemes.PrimitiveKind.Hyphen)

    def register(
        self,
        token_kind: type[lexemes.Token],
        parselet: "PrefixParselet | InfixParselet",
    ):
        if isinstance(parselet, PrefixParselet):
            self.prefix_parselets[token_kind] = parselet
        if isinstance(parselet, InfixParselet):
            self.infix_parselets[token_kind] = parselet

    def prefix(self, token_kind: lexemes.PrimitiveKind):
        self.register(lexemes.Primitive, PrefixOperatorParselet())

    def expression(self) -> nodes.Expression | None:
        # Grab the next token, and locate an appropriate parselet given its value.
        # Then, use that parser to parse the left hand side of an expression (prefix expr)
        parselet = None
        match self.tokens.peek():
            case None:
                return None
            case lexemes.Identifier():
                parselet = NameParselet()

        token = self.tokens.next()
        prefix = self.prefix_parselets[type(token)]
        left = prefix.parse(self, token)

        peeked = self.tokens.peek()
        assert peeked is not None

        try:
            infix = self.infix_parselets[type(peeked)]
        except KeyError:
            infix = None

        if infix is None:
            return left

        token = self.tokens.next()
        return infix.parse(self, left, token)


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
        assert nodes.BinaryOperator.is_binary_op(token)

        right = parser.expression()
        return nodes.BinaryExpression(
            left.span + right.span,
            operator=nodes.BinaryOperator(token.kind),
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

from pprint import pprint

tokens = [
    lexemes.Identifier(identifier="foo", span=Span.default()),
    lexemes.Primitive(kind=lexemes.PrimitiveKind.Plus, span=Span.default()),
    lexemes.Identifier(identifier="bar", span=Span.default()),
]

parser = Parser(tokens=Stream(tokens))
expr = parser.expression()

pprint(expr)
print(type(expr))
