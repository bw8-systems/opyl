from combinator.combinators import DelimitedBy, SeparatedBy, Parser, Just
from compile.lex import Token, PrimitiveKind
from compile.errors import ParseError

type TokenParser[Out] = Parser[Token, Out, ParseError]


def block[
    Out
](parser: TokenParser[Out]) -> DelimitedBy[Token, list[Out], Token, Token, ParseError]:
    return parser.separated_by(
        Just[Token, ParseError](PrimitiveKind.NewLine).repeated().at_least(1)
    ).delimited_by(
        start=Just[Token, ParseError](PrimitiveKind.LeftParenthesis),
        end=Just[Token, ParseError](PrimitiveKind.RightParenthesis),
    )


def parens[
    Out
](parser: TokenParser[Out]) -> DelimitedBy[Token, Out, Token, Token, ParseError]:
    return parser.delimited_by(
        start=Just[Token, ParseError](PrimitiveKind.LeftParenthesis),
        end=Just[Token, ParseError](PrimitiveKind.RightParenthesis),
    )


def lines[Out](parser: TokenParser[Out]) -> SeparatedBy[Token, Out, Token, ParseError]:
    return parser.separated_by(Just[Token, ParseError](PrimitiveKind.NewLine))
