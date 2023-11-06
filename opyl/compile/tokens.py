import enum
import dataclasses


from .stream import Span


class KeywordKind(enum.Enum):
    Trait = "trait"
    Enum = "enum"
    Def = "def"
    Let = "let"
    U8 = "u8"
    Char = "char"
    Mut = "mut"
    Anon = "anon"


class PrimitiveKind(enum.Enum):
    Colon = ":"
    Equal = "="
    LeftBrace = "{"
    RightBrace = "}"
    LeftParenthesis = "("
    RightParenthesis = ")"
    LeftAngle = "<"
    RightAngle = ">"
    LeftBracket = "["
    RightBracket = "]"
    Comma = ","
    Hyphen = "-"
    RightArrow = "->"
    NewLine = "\n"
    Eof = "\0"


@dataclasses.dataclass
class Identifier:
    span: Span
    identifier: str


@dataclasses.dataclass
class StringLiteral:
    span: Span
    string: str


@dataclasses.dataclass
class IntegerLiteral:
    span: Span
    integer: int


@dataclasses.dataclass
class Keyword:
    span: Span
    kind: KeywordKind


@dataclasses.dataclass
class Primitive:
    span: Span
    kind: PrimitiveKind


@dataclasses.dataclass
class Whitespace:
    span: Span


@dataclasses.dataclass
class Comment:
    span: Span
    comment: str


@dataclasses.dataclass
class CharacterLiteral:
    span: Span
    char: str


type Token = (
    Primitive
    | Identifier
    | IntegerLiteral
    | Keyword
    | StringLiteral
    | Whitespace
    | Comment
    | CharacterLiteral
)
