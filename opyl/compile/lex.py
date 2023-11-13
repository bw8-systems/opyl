import typing as t

from . import lexemes
from .positioning import TextStream, Span
from . import errors

type Predicate[T] = t.Callable[[T], bool]
type Scanner = t.Callable[[], lexemes.Token]


class Tokenizer:
    def __init__(self, data: str):
        self.stream = TextStream(data)

    def next_token(self) -> lexemes.Token:
        current = self.stream.current()
        scanners_and_predicates: list[tuple[Scanner, Predicate[str]]] = [
            (self.tokenize_whitespace, lambda char: char in {" ", "\r", "\t"}),
            (self.tokenize_comment, lambda char: char == "#"),
            (self.tokenize_string, lambda char: char == '"'),
            (self.tokenize_character, lambda char: char == "'"),
            (self.tokenize_integer, str.isdigit),
            (self.tokenize_identifier_or_keyword, str.isalpha),
            (self.tokenize_primitive, lambda _char: True),
        ]

        for scanner, predicate in scanners_and_predicates:
            if predicate(current):
                return scanner()

        raise errors.IllegalCharacter(current)

    def take_while(self, predicate: Predicate[str]) -> str:
        start = self.stream.index.copy()

        for char in self.stream:
            if not predicate(char):
                break

            self.stream.advance(newline=char == "\n")

        if self.stream.index == start:
            self.stream.index = start
            raise errors.NoMatch(self.stream.current())

        return self.stream.text[start.absolute : self.stream.index.absolute]

    def tokenize_primitive(self):
        start = self.stream.index.copy()

        for kind in lexemes.PrimitiveKind:
            lexeme = kind.value

            if self.stream.startswith(lexeme):
                self.stream.advance_for(lexeme)

                return lexemes.Primitive(
                    span=Span(
                        start=start,
                        stop=self.stream.index.copy(),
                    ),
                    kind=lexemes.PrimitiveKind(lexeme),
                )

        raise errors.UnexpectedCharacter(self.stream.current())

    def tokenize_whitespace(self) -> lexemes.Whitespace:
        start = self.stream.index.copy()

        self.take_while(lambda char: char in {" ", "\r", "\t"})
        return lexemes.Whitespace(span=Span(start=start, stop=self.stream.index.copy()))

    def tokenize_comment(self) -> lexemes.Comment:
        start = self.stream.index.copy()
        current = self.stream.current()
        if current == "":
            raise errors.UnexpectedEOF()

        if current != "#":
            raise errors.UnexpectedCharacter(current)

        self.stream.advance(newline=False)
        try:
            comment = self.take_while(lambda char: char != "\n")
        except errors.NoMatch:
            comment = ""

        return lexemes.Comment(
            span=Span(start=start, stop=self.stream.index.copy()), comment=comment
        )

    def tokenize_integer(self) -> lexemes.IntegerLiteral:
        start = self.stream.index.copy()

        try:
            integer_string = self.take_while(str.isdigit)
        except errors.NoMatch:
            raise errors.UnexpectedCharacter(self.stream.current())

        return lexemes.IntegerLiteral(
            span=Span(start=start, stop=self.stream.index.copy()),
            integer=int(integer_string),
        )

    def tokenize_identifier_or_keyword(self) -> lexemes.Identifier | lexemes.Keyword:
        start = self.stream.index.copy()
        current = self.stream.current()
        if current == lexemes.PrimitiveKind.Eof.value:
            raise errors.UnexpectedEOF()

        if not (current.isalpha() or current == "_"):
            raise errors.UnexpectedCharacter(current)

        name = self.take_while(
            lambda char: char == "_" or char.isalpha() or char.isalnum()
        )

        span = Span(start=start, stop=self.stream.index.copy())
        try:
            return lexemes.Keyword(span=span, kind=lexemes.KeywordKind(name))
        except ValueError:
            return lexemes.Identifier(span=span, identifier=name)

    def tokenize_string(self):
        start = self.stream.index.copy()
        current = self.stream.current()
        if current == "":
            raise errors.UnexpectedEOF()

        if current != '"':
            raise errors.UnexpectedCharacter(current)

        self.stream.advance(newline=False)
        for char in self.stream:
            if char == "\n":
                self.stream.index = start
                raise errors.UnexpectedCharacter(char)

            self.stream.advance(newline=False)

            if char == '"':
                return lexemes.StringLiteral(
                    span=Span(start=start, stop=self.stream.index.copy()),
                    string=self.stream.text[
                        start.absolute + 1 : self.stream.index.absolute - 1
                    ],
                )

        raise errors.UnclosedStringLiteral(
            self.stream.text[start.absolute : self.stream.index.absolute]
        )

    def tokenize_character(self) -> lexemes.CharacterLiteral:
        start = self.stream.index.copy()
        current = self.stream.current()
        if current is lexemes.PrimitiveKind.Eof.value:
            raise errors.UnexpectedEOF()

        if current != "'":
            raise errors.UnexpectedCharacter(current)

        self.stream.advance(newline=False)
        char = self.stream.current()

        self.stream.advance(newline=False)
        closing = self.stream.current()
        self.stream.advance(newline=False)
        if closing != "'":
            raise errors.UnexpectedCharacter(closing)

        return lexemes.CharacterLiteral(
            span=Span(
                start=start,
                stop=self.stream.index.copy(),
            ),
            char=char,
        )


def tokenize(source: str) -> list[lexemes.Token]:
    scanner = Tokenizer(source)
    tokenized = list[lexemes.Token]()

    while True:
        token = scanner.next_token()
        if (
            isinstance(token, lexemes.Primitive)
            and token.kind is lexemes.PrimitiveKind.Eof
        ):
            break

        tokenized.append(token)

    return tokenized
