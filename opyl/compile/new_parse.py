from dataclasses import dataclass
import typing as t


from . import lex
# from compile import lex


class ParseError(Exception):
    ...


class UnexpectedEOF(ParseError):
    ...


class UnexpectedToken(ParseError):
    ...


@dataclass
class VariableDeclaration:
    span: lex.Span
    name: str
    type: str  # TODO: Using strings here may be bad idea.


@dataclass
class FunctionDeclaration:
    span: lex.Span
    name: str
    return_type = str
    # TODO: etc


type TopLevelDeclaration = VariableDeclaration | FunctionDeclaration


@dataclass
class Stack:
    index: int = 0

    def __post_init__(self):
        self.stack = list[int]()

    def push(self):
        self.stack.append(self.index)

    def drop(self) -> int:
        try:
            return self.stack.pop()
        except IndexError:
            raise RuntimeError  # TODO: What kind of error is this?

    def pop(self):
        self.index = self.drop()


class Stream[T]:
    def __init__(self, stream: t.Sequence[T]):
        self.stack = Stack()
        self.stream = stream

    def peek(self) -> T | None:
        try:
            return self.stream[self.stack.index]
        except IndexError:
            return None

    def increment(self) -> None:
        self.stack.index += 1

    def next(self) -> T:
        maybe = self.peek()
        if maybe is None:
            raise UnexpectedEOF()

        # Pyright has narrowed from T | None to T via conditional above.
        # Renaming for semantic clarity.
        peeked = maybe

        self.increment()
        return peeked


@dataclass
class TokenParser:
    stream: Stream[lex.Token]

    def primitive(self, kind: lex.PrimitiveKind) -> lex.PrimitiveToken:
        peeked = self.stream.peek()
        if peeked is None:
            raise UnexpectedEOF()
        if isinstance(peeked, lex.PrimitiveToken) and peeked.kind is kind:
            self.stream.next()
            return peeked
        raise UnexpectedToken()

    def keyword(self, kind: lex.KeywordKind) -> lex.KeywordToken:
        peeked = self.stream.peek()
        if peeked is None:
            raise UnexpectedEOF()
        if isinstance(peeked, lex.KeywordToken) and peeked.kind is kind:
            self.stream.next()
            return peeked
        raise UnexpectedToken()

    def identifier(self) -> lex.IdentifierToken:
        peeked = self.stream.peek()
        if peeked is None:
            raise UnexpectedEOF()
        if isinstance(peeked, lex.IdentifierToken):
            self.stream.next()
            return peeked
        raise UnexpectedToken()

    def integer(self) -> lex.IntegerToken:
        peeked = self.stream.peek()
        if peeked is None:
            raise UnexpectedEOF()
        if isinstance(peeked, lex.IntegerToken):
            self.stream.next()
            return peeked
        raise UnexpectedToken()

    # TODO: This combinators need to be DRYd
    def whitespace(self) -> lex.WhiteSpaceToken:
        peeked = self.stream.peek()
        if peeked is None:
            raise UnexpectedEOF()
        if isinstance(peeked, lex.WhiteSpaceToken):
            self.stream.next()
            return peeked
        raise UnexpectedToken()


@dataclass
class OpalParser(TokenParser):
    def parse_variable_declaration(self) -> VariableDeclaration:
        # NOTE: Doesn't include "mut" modifier
        # NOTE: Doesn't include initializer. Opal grammar shouldn't allow declarations without initializers.
        # (ie, variables must be defined with an initial value)
        # Grammar:
        # let NAME: TYPE

        # Save initial state for backtracking in case this isn't a
        # variable declaration.
        # TODO: This maybe should be treated as infallible and throw
        # exception. Leave backtracking to caller.
        self.stream.stack.push()

        try:
            keyword = self.keyword(lex.KeywordKind.Let)
        except ParseError:
            self.stream.stack.pop()
            raise UnexpectedToken()
        else:
            self.stream.stack.drop()

        # Now that the `let` keyword has been consumed, the grammar
        # won't allow anything other than a variable declaration to occur.
        # So, no backtracking.

        self.whitespace()
        identifier = self.identifier()
        self.primitive(lex.PrimitiveKind.Colon)
        self.whitespace()

        # TODO: If builtin types (u8, char...) are considered keywords in the
        # grammar this this should be trying identifier and/or keyword with
        # valid keyword kinds (u8, char...)
        variable_type = self.identifier()

        return VariableDeclaration(
            span=lex.Span(
                start=keyword.span.start,
                stop=variable_type.span.stop,
            ),
            name=identifier.identifier,
            type=variable_type.identifier,
        )

    # def parse_function_declaration(self) -> FunctionDeclaration:
    #     ...


def parse(tokens: list[lex.Token]):
    ...
