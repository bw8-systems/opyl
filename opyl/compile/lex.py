import enum
import dataclasses
import contextlib
import typing as t


type Predicate[T] = t.Callable[[T], bool]
type Scanner = t.Callable[[], Token]


class LexError(Exception):
    ...


class UnexpectedCharacter(LexError):
    ...


class NoMatch(LexError):
    ...


class UnexpectedEOF(LexError):
    ...


class UnclosedStringLiteral(LexError):
    ...


class IllegalCharacter(LexError):
    ...


class KeywordKind(enum.Enum):
    Let = "let"
    U8 = "u8"
    Char = "char"


class PrimitiveKind(enum.Enum):
    Colon = ":"
    Equal = "="
    Eof = "\0"


@dataclasses.dataclass
class TextPosition:
    absolute: int = 0
    line: int = 0
    column: int = 0

    def copy(self) -> "TextPosition":
        return TextPosition(
            absolute=self.absolute,
            line=self.line,
            column=self.column,
        )

    def increment(self, newline: bool) -> t.Self:
        return TextPosition(
            absolute=self.absolute + 1,
            line=self.line + 1 if newline else self.line,
            column=0 if newline else self.column + 1,
        )

    @staticmethod
    def default() -> "TextPosition":
        return TextPosition(0, 0, 0)


@dataclasses.dataclass
class Span:
    start: TextPosition
    stop: TextPosition


@dataclasses.dataclass
class IdentifierToken:
    span: Span
    identifier: str


@dataclasses.dataclass
class StringToken:
    span: Span
    string: str


@dataclasses.dataclass
class IntegerToken:
    span: Span
    integer: int


@dataclasses.dataclass
class KeywordToken:
    span: Span
    kind: KeywordKind


@dataclasses.dataclass
class PrimitiveToken:
    span: Span
    kind: PrimitiveKind


@dataclasses.dataclass
class WhiteSpaceToken:
    span: Span


@dataclasses.dataclass
class CommentToken:
    span: Span
    comment: str


@dataclasses.dataclass
class CharacterToken:
    span: Span
    char: str


type Token = (
    IdentifierToken
    | IntegerToken
    | KeywordToken
    | PrimitiveToken
    | StringToken
    | WhiteSpaceToken
    | CommentToken
    | CharacterToken
)


class TextStream:
    def __init__(self, text: str):
        self.text = text
        self.index = TextPosition(0, 0, 0)

    def __iter__(self):
        for char in self.text[self.index.absolute :]:
            yield char

    def advance(self, *, newline: bool):
        self.index.absolute += 1
        if newline:
            self.index.line += 1
            self.index.column = 0
        else:
            self.index.column += 1

    def current(self) -> str:
        with contextlib.suppress(IndexError):
            return self.text[self.index.absolute]
        return PrimitiveKind.Eof.value


class Tokenizer:
    def __init__(self, data: str):
        self.stream = TextStream(data)

    def next_token(self) -> Token:
        current = self.stream.current()

        scanners_and_predicates: tuple[tuple[Scanner, Predicate[str]], ...] = (
            (self.tokenize_whitespace, str.isspace),
            (self.tokenize_comment, lambda char: char == "#"),
            (self.tokenize_string, lambda char: char == '"'),
            (self.tokenize_character, lambda char: char == "'"),
            (self.tokenize_integer, str.isdigit),
            (self.tokenize_identifier_or_keyword, str.isalpha),
            (self.tokenize_primitive, lambda _char: True),
        )

        for scanner, predicate in scanners_and_predicates:
            if predicate(current):
                return scanner()

        raise IllegalCharacter()

    def take_while(self, predicate: Predicate[str]) -> str:
        start = self.stream.index.copy()

        for char in self.stream:
            if not predicate(char):
                break

            self.stream.advance(newline=char == "\n")

        if self.stream.index == start:
            self.stream.index = start
            raise NoMatch()

        return self.stream.text[start.absolute : self.stream.index.absolute]

    def tokenize_primitive(self):
        start = self.stream.index.copy()
        current = self.stream.current()
        try:
            kind = PrimitiveKind(current)
        except ValueError:
            raise UnexpectedCharacter()

        self.stream.advance(newline=False)

        return PrimitiveToken(
            span=Span(
                start=start,
                stop=self.stream.index.copy(),
            ),
            kind=kind,
        )

    def tokenize_whitespace(self) -> WhiteSpaceToken:
        start = self.stream.index.copy()
        self.take_while(str.isspace)

        return WhiteSpaceToken(span=Span(start=start, stop=self.stream.index.copy()))

    def tokenize_comment(self) -> CommentToken:
        start = self.stream.index.copy()
        current = self.stream.current()
        if current is PrimitiveKind.Eof.value:
            raise UnexpectedEOF()

        if current != "#":
            raise UnexpectedCharacter()

        self.stream.advance(newline=False)
        try:
            comment = self.take_while(lambda char: char != "\n")
        except NoMatch:
            comment = ""

        return CommentToken(
            span=Span(start=start, stop=self.stream.index), comment=comment
        )

    def tokenize_integer(self) -> IntegerToken:
        start = self.stream.index.copy()

        try:
            integer_string = self.take_while(str.isdigit)
        except NoMatch:
            raise UnexpectedCharacter

        return IntegerToken(
            span=Span(start=start, stop=self.stream.index.copy()),
            integer=int(integer_string),
        )

    def tokenize_identifier_or_keyword(self) -> IdentifierToken | KeywordToken:
        start = self.stream.index.copy()
        current = self.stream.current()
        if current == PrimitiveKind.Eof.value:
            raise UnexpectedEOF()

        if not (current.isalpha() or current == "_"):
            raise UnexpectedCharacter()

        name = self.take_while(
            lambda char: char == "_" or char.isalpha() or char.isalnum()
        )

        span = Span(start=start, stop=self.stream.index)
        try:
            return KeywordToken(span=span, kind=KeywordKind(name))
        except ValueError:
            return IdentifierToken(span=span, identifier=name)

    def tokenize_string(self):
        start = self.stream.index.copy()
        current = self.stream.current()
        if current is PrimitiveKind.Eof.value:
            raise UnexpectedEOF()

        if current != '"':
            raise UnexpectedCharacter()

        self.stream.advance(newline=False)
        for char in self.stream:
            if char == "\n":
                self.stream.index = start
                raise UnexpectedCharacter()

            self.stream.advance(newline=False)

            if char == '"':
                return StringToken(
                    span=Span(start=start, stop=self.stream.index.copy()),
                    string=self.stream.text[
                        start.absolute + 1 : self.stream.index.absolute - 1
                    ],
                )

        raise UnclosedStringLiteral()

    def tokenize_character(self) -> CharacterToken:
        start = self.stream.index.copy()
        current = self.stream.current()
        if current is PrimitiveKind.Eof.value:
            raise UnexpectedEOF()

        if current != "'":
            raise UnexpectedCharacter()

        self.stream.advance(newline=False)
        char = self.stream.current()

        self.stream.advance(newline=False)
        closing = self.stream.current()
        self.stream.advance(newline=False)
        if closing != "'":
            raise UnexpectedCharacter()

        return CharacterToken(
            span=Span(
                start=start,
                stop=self.stream.index.copy(),
            ),
            char=char,
        )


def tokenize(source: str) -> list[Token]:
    tokenizer = Tokenizer(source)
    tokens = list[Token]()

    while True:
        # print(f"start = {tokenizer.stream.index}")
        token = tokenizer.next_token()
        # print(token)
        # print(f"span = {token.span}")
        if isinstance(token, PrimitiveToken) and token.kind is PrimitiveKind.Eof:
            break

        tokens.append(token)
        # print(f"stop = {tokenizer.stream.index}")
        # pprint(tokens)
        # print()

    return tokens
