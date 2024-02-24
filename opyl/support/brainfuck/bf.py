import typing as t
import enum
from pprint import pprint

from opyl.support.stream import Stream
from opyl.support.combinator import Just, Filter, one_of


class TokenKind(enum.Enum):
    LAngle = "<"
    RAngle = ">"
    Plus = "+"
    Minus = "-"
    Period = "."
    Comma = ","
    LBracket = "["
    RBracket = "]"


just = Just[str, t.Any]
filt = Filter[str, t.Any]

ws = filt(str.isspace).repeated()

token = one_of(list(iter(TokenKind))).map(TokenKind)


def tokenize(source: str) -> Stream[TokenKind]:
    tokens = (
        ws.ignore_then(token.spanned())
        .repeated()
        .parse(Stream.from_source(source))
        .unwrap()[0]
    )
    return Stream(file_handle=None, spans=tokens)


tokens = [spanned.item for spanned in tokenize("[->+<]").spans]
pprint(tokens)
