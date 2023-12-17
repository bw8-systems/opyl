import typing as t
from enum import Enum, auto
from dataclasses import dataclass


class Keyword(Enum):
    Trait = "trait"
    Enum = "enum"
    Struct = "struct"
    Union = "union"
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
    Char = "char"
    Mut = "mut"
    Anon = "anon"


class Basic(Enum):
    Plus = "+"
    RightArrow = "->"
    Hyphen = "-"
    Asterisk = "*"
    ForwardSlash = "/"
    Caret = "^"
    Percent = "%"
    At = "@"
    Ampersand = "&"
    Ampersand2 = "&&"
    Bang = "!"
    BangEqual = "!="
    Tilde = "~"
    Colon2 = "::"
    Colon = ":"
    Equal2 = "=="
    Equal = "="
    LeftBrace = "{"
    RightBrace = "}"
    LeftParenthesis = "("
    RightParenthesis = ")"
    LeftAngle = "<"
    LeftAngle2 = "<<"
    LeftAngleEqual = "<="
    RightAngle = ">"
    RightAngle2 = ">>"
    RightAngleEqual = ">="
    LeftBracket = "["
    RightBracket = "]"
    Comma = ","
    Period = "."
    Pipe = "|"
    Pipe2 = "||"
    NewLine = "\n"
    Eof = ""


class TokenKind(Enum):
    Keyword = auto()
    Basic = auto()
    Identifier = auto()
    Integer = auto()
    String = auto()
    Character = auto()
    Whitespace = auto()
    Comment = auto()


Whitespace: t.Final[t.Literal[TokenKind.Whitespace]] = TokenKind.Whitespace


@dataclass(unsafe_hash=True, frozen=True)
class Identifier:
    identifier: str


@dataclass
class StringLiteral:
    string: str


@dataclass
class IntegerLiteral:
    integer: int


@dataclass
class Comment:
    comment: str


@dataclass
class CharacterLiteral:
    char: str


type Token = (
    Basic
    | Identifier
    | IntegerLiteral
    | Keyword
    | StringLiteral
    | t.Literal[TokenKind.Whitespace]
    | Comment
    | CharacterLiteral
)
