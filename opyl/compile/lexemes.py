import enum
import dataclasses


from compile.positioning import Span


class KeywordKind(enum.Enum):
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


class PrimitiveKind(enum.Enum):
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
