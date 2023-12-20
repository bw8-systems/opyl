import typing as t
from opyl.compile.token import Token, Identifier, IntegerLiteral
from opyl.compile.error import ParseError
from opyl.support.combinator import Filter, Just

filt = Filter[Token, ParseError]
just = Just[Token, ParseError]

ident = filt(lambda tok: isinstance(tok, Identifier)).map(
    lambda tok: t.cast(Identifier, tok)
)
integer = filt(lambda tok: isinstance(tok, IntegerLiteral)).map(
    lambda tok: t.cast(IntegerLiteral, tok)
)
