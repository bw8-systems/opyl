import typing as t
from opyl.compile.token import (
    Token,
    Identifier,
    IntegerLiteral,
    Basic,
    StringLiteral,
    CharacterLiteral,
)
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
string = filt(lambda tok: isinstance(tok, StringLiteral)).map(
    lambda tok: t.cast(StringLiteral, tok)
)
char = filt(lambda tok: isinstance(tok, CharacterLiteral)).map(
    lambda tok: t.cast(CharacterLiteral, tok)
)
newlines = just(Basic.NewLine).repeated()
