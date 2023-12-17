import typing as t
from compile.token import Token, Identifier, IntegerLiteral, Basic
from compile.error import ParseError
from support.combinator import Filter, Just, OneOf

filt = Filter[Token, ParseError]
just = Just[Token, ParseError]
one_of = OneOf[Token, ParseError]

ident = filt(lambda tok: isinstance(tok, Identifier)).map(
    lambda tok: t.cast(Identifier, tok)
)
integer = filt(lambda tok: isinstance(tok, IntegerLiteral)).map(
    lambda tok: t.cast(IntegerLiteral, tok)
)


def identity(basic: Basic) -> Filter[Token, ParseError]:
    return filt(lambda tok: tok is basic)
