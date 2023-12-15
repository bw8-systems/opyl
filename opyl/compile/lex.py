import typing as t
from dataclasses import dataclass
from enum import Enum, auto

from compile.errors import LexError
from combinator.combinators import Filter, Just, filter, one_of


class KeywordKind(Enum):
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


class PrimitiveKind(Enum):
    Plus = "+"
    RightArrow = "->"
    Hyphen = "-"
    Asterisk = "*"
    ForwardSlash = "/"
    Caret = "^"
    Percent = "%"
    At = "@"
    Ampersand = "&"
    Exclamation = "!"
    ColonColon = "::"
    Colon = ":"
    EqualEqual = "=="
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
    Period = "."
    Pipe = "|"
    NewLine = "\n"
    Eof = ""


class TokenKind(Enum):
    Keyword = auto()
    Primitive = auto()
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
    PrimitiveKind
    | Identifier
    | IntegerLiteral
    | KeywordKind
    | StringLiteral
    | t.Literal[TokenKind.Whitespace]
    | Comment
    | CharacterLiteral
)


LexFilter = Filter[str, LexError]
LexJust = Just[str, LexError]

integer = (
    (
        LexFilter(lambda char: str.isdigit(char) and char != "0")
        .chain(filter(str.isdigit).repeated())
        .map(lambda chars: int("".join(chars)))
    )
    | Just("0").map(int)
).map(lambda either: IntegerLiteral(either.item))


identifier = (
    LexFilter(lambda char: char.isalpha() or char == "_")
    .chain(LexFilter(lambda char: char.isalnum() or char == "_").repeated())
    .map(lambda chars: "".join(chars))
).map(Identifier)

keyword = identifier.and_check(lambda ident: ident in KeywordKind).map(
    lambda char: KeywordKind(char)
)

basic = one_of("+-*/{}").map(lambda char: PrimitiveKind(char))

string = (
    LexJust('"')
    .ignore_then(LexFilter(lambda char: char not in {"\n", '"'}).repeated())
    .then_ignore(LexJust('"').require(LexError.UnterminatedStringLiteral))
    .map(lambda chars: "".join(chars))
).map(StringLiteral)

character = (
    LexJust("'")
    .ignore_then(LexFilter(lambda char: char != "'"))
    .then_ignore(LexJust("'").require(LexError.UnexpectedCharacter))
).map(CharacterLiteral)

whitespace = LexJust(" ").then(filter(str.isspace).repeated()).map(lambda _: Whitespace)

comment = (
    LexJust("#")
    .ignore_then(LexFilter(lambda char: char != "\n").repeated())
    .map(lambda chars: "".join(chars))
).map(Comment)

token = (
    integer | identifier | keyword | basic | string | character | comment | whitespace
)

tokenizer = token.repeated()
