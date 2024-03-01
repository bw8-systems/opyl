import typing as t
from enum import Enum, auto
from dataclasses import dataclass


class Keyword(Enum):
    Trait = "trait"
    Enum = "enum"
    Struct = "struct"
    Type = "type"
    Let = "let"
    Const = "const"
    Def = "def"
    Meth = "meth"
    While = "while"
    For = "for"
    In = "in"
    If = "if"
    Else = "else"
    When = "when"
    Is = "is"
    As = "as"
    Return = "return"
    Break = "break"
    Continue = "continue"
    Mut = "mut"
    Anon = "anon"
    U8 = "u8"
    I8 = "i8"
    U16 = "u16"
    I16 = "i16"
    U32 = "u32"
    I32 = "i32"
    Str = "str"
    Char = "char"
    Bool = "bool"
    True_ = "true"
    False_ = "false"


class Basic(Enum):
    Plus = auto()
    PlusEqual = auto()
    Hyphen = auto()
    HyphenEqual = auto()
    RightArrow = auto()
    Asterisk = auto()
    AsteriskEqual = auto()
    ForwardSlash = auto()
    ForwardSlashEqual = auto()
    Caret = auto()
    Percent = auto()
    At = auto()
    Ampersand2 = auto()
    Ampersand = auto()
    BangEqual = auto()
    Bang = auto()
    Tilde = auto()
    Colon2 = auto()
    Colon = auto()
    Equal2 = auto()
    Equal = auto()
    LeftBrace = auto()
    RightBrace = auto()
    LeftParenthesis = auto()
    RightParenthesis = auto()
    LeftAngle2 = auto()
    LeftAngleEqual = auto()
    LeftAngle = auto()
    RightAngle2 = auto()
    RightAngleEqual = auto()
    RightAngle = auto()
    LeftBracket = auto()
    RightBracket = auto()
    Comma = auto()
    Period = auto()
    Pipe2 = auto()
    Pipe = auto()
    NewLine = auto()
    Eof = auto()  # TODO


class TokenKind(Enum):
    Keyword = auto()
    Basic = auto()
    Identifier = auto()
    Integer = auto()
    String = auto()
    Character = auto()
    Whitespace = auto()
    Comment = auto()


type IntegerLiteralBase = t.Literal[2] | t.Literal[10] | t.Literal[16]


Whitespace: t.Final[t.Literal[TokenKind.Whitespace]] = TokenKind.Whitespace


@dataclass()
class Identifier:
    identifier: str

    # def __eq__(self, other: t.Any) -> bool:
    #     if not isinstance(other, self.__class__):
    #         return NotImplemented
    #     return self.identifier == other.identifier


@dataclass
class StringLiteral:
    string: str


@dataclass
class IntegerLiteral:
    integer: int
    base: IntegerLiteralBase = 10


@dataclass
class Comment:
    comment: str


@dataclass
class CharacterLiteral:
    char: str


type Token = (
    Basic | Identifier | IntegerLiteral | Keyword | StringLiteral | CharacterLiteral
)
