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


# TODO: Just use enum.auto() here. Lexer does this mapping.
# Or maybe update lexer to use mapping. That way we preserve the printing utility.
class Basic(Enum):
    Plus = "+"
    Hyphen = "-"
    RightArrow = "->"
    Asterisk = "*"
    ForwardSlash = "/"
    Caret = "^"
    Percent = "%"
    At = "@"
    Ampersand2 = "&&"
    Ampersand = "&"
    BangEqual = "!="
    Bang = "!"
    Tilde = "~"
    Colon2 = "::"
    Colon = ":"
    Equal2 = "=="
    Equal = "="
    LeftBrace = "{"
    RightBrace = "}"
    LeftParenthesis = "("
    RightParenthesis = ")"
    LeftAngle2 = "<<"
    LeftAngleEqual = "<="
    LeftAngle = "<"
    RightAngle2 = ">>"
    RightAngleEqual = ">="
    RightAngle = ">"
    LeftBracket = "["
    RightBracket = "]"
    Comma = ","
    Period = "."
    Pipe2 = "||"
    Pipe = "|"
    NewLine = "\n"
    Eof = ""  # TODO


class TokenKind(Enum):
    Keyword = auto()
    Basic = auto()
    Identifier = auto()
    Integer = auto()
    String = auto()
    Character = auto()
    Whitespace = auto()
    Comment = auto()


class IntegerLiteralBase(Enum):
    Binary = auto()
    Decimal = auto()
    Hexadecimal = auto()


Whitespace: t.Final[t.Literal[TokenKind.Whitespace]] = TokenKind.Whitespace


@dataclass(eq=False)
class Identifier:
    identifier: str

    def __eq__(self, other: t.Any) -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.identifier == other.identifier


@dataclass
class StringLiteral:
    string: str


@dataclass
class IntegerLiteral:
    integer: int
    base: IntegerLiteralBase = IntegerLiteralBase.Decimal


@dataclass
class Comment:
    comment: str


@dataclass
class CharacterLiteral:
    char: str


type Token = (
    Basic | Identifier | IntegerLiteral | Keyword | StringLiteral | CharacterLiteral
)
