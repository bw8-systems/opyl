from dataclasses import dataclass
import enum
from typing import Literal as Lit


@dataclass
class Span:
    """
    Represents start and end bounds of a token within source.
    """

    # TODO: Use "TextPosition" rather than raw integers.
    start: int
    end: int

    def __add__(self, other: "Span") -> "Span":
        if not isinstance(other, Span):  # type: ignore
            return NotImplemented

        return Span(self.start, other.end)


class PrimitiveKind(enum.Enum):
    Colon = ":"

    LeftBrace = "{"
    RightBrace = "}"
    LeftBracket = "["
    RightBracket = "]"
    SemiColon = ";"
    Comma = ","
    Equals = "="
    Plus = "+"


class KeywordKind(enum.Enum):
    """
    KeywordKind enumerates the keywords which are legal in Opal.
    """

    Let = "let"

    Const = "const"
    Struct = "struct"
    Enum = "enum"
    Typedef = "typedef"
    Module = "module"
    Uint = "uint"
    Int = "int"


IntegerKind = int
IdentifierKind = str

type TokenKind = PrimitiveKind | KeywordKind | IntegerKind | IdentifierKind


@dataclass
class BaseToken[Kind: TokenKind]:
    span: Span
    kind: Kind  # TODO: Is this needed?


class PrimitiveToken(BaseToken[PrimitiveKind]):
    ...


class KeywordToken(BaseToken[KeywordKind]):
    ...


@dataclass
class IntegerToken(BaseToken[IntegerKind]):
    value: int


@dataclass
class IdentifierToken(BaseToken[IdentifierKind]):
    value: str


type Token = PrimitiveToken | KeywordToken | IntegerToken | IdentifierToken
