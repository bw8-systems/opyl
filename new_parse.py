"""
Tools for parsing the Opal grammar.
"""
from dataclasses import dataclass
import enum
from collections.abc import Sequence
from typing import overload, Callable, NamedTuple, Self
from functools import partial

import new_types as lex
import new_types as node
from new_types import kind, token


class ParseError(enum.Enum):
    UnexpectedEOF = enum.auto()
    UnexpectedToken = enum.auto()


class ParseException(Exception):
    ...


class IllegalSyntax(ParseException):
    ...


type ParseResult[Okay] = Okay | ParseError
type Parser[T] = Callable[[], ParseResult[T]]


class Result[Okay, Error]:
    def __init__(self):
        self.ok: Okay | None = None
        self.err: Error | None = None

    @classmethod
    def Ok(cls, ok: Okay) -> Self:
        self = cls()
        cls.ok = ok
        return self

    @classmethod
    def Err(cls, err: Error) -> Self:
        self = cls()
        cls.err = err
        return self

    def and_then[U](self, op: Callable[[], "Result[U, Error]"]) -> "Result[U, Error]":
        if self.ok is not None:
            return op()
        new: Result[U, Error] = Result.Err(self.err)
        return new


class ParsedBetween[Before, After, Between](NamedTuple):
    before: Before
    after: After
    between: Between


@dataclass
class Stack:
    # TODO: Maybe should not live here.
    index: int = 0

    def __post_init__(self):
        self.stack = list[int]()

    def push(self):
        self.stack.append(self.index)

    def drop(self) -> int:
        try:
            return self.stack.pop()
        except IndexError:
            raise RuntimeError  # TODO

    def pop(self):
        self.index = self.drop()


# TODO: Probably remove.
def require[T](result: ParseResult[T]) -> T:
    if isinstance(result, ParseError):
        raise IllegalSyntax()
    return result


def attempt[T](stack: Stack, parser: Parser[T]) -> T | None:
    stack.push()

    result = parser()
    if isinstance(result, ParseError):
        stack.pop()
        return None
    item = result

    stack.drop()
    return item


def between[
    Before, Between, After
](
    parse_before: Parser[Before],
    parse_between: Parser[Between],
    parse_after: Parser[After],
) -> ParseResult[ParsedBetween[Before, After, Between]]:
    before_result = parse_before()
    if isinstance(before_result, ParseError):
        return before_result
    before = before_result

    between_result = parse_between()
    if isinstance(between_result, ParseError):
        return between_result
    between = between_result

    after_result = parse_after()
    if isinstance(after_result, ParseError):
        return after_result
    after = after_result

    return ParsedBetween(before, after, between)


# def choice[T](self, parsers: Sequence[Parser[T]]) -> ParseResult[T]:
#     for parser in parsers:
#         item_or_none = self.attempt(parser)

#         if item_or_none is not None:
#             item = item_or_none
#             return item

#     return ParseError.UnexpectedToken

# def either[T, U](self, this: Parser[T], that: Parser[U]):
#     choices = (this, that)
#     return self.choice(choices)

# def many[T](self, parser: Parser[T]) -> list[T]:
#     items: list[T] = []

#     while True:
#         item_or_none = self.attempt(parser)
#         if item_or_none is None:
#             break

#         item = item_or_none
#         items.append(item)

#     return items


class Stream[T]:
    def __init__(self, stream: Sequence[T]):
        self.stack = Stack()
        self.stream = stream

    def peek(self) -> T | None:
        try:
            current = self.stream[self.stack.index]
        except IndexError:
            return None

        return current

    def next(self) -> ParseResult[T]:
        item_or_none = self.peek()
        if item_or_none is None:
            return ParseError.UnexpectedEOF
        item = item_or_none

        self.stack.index += 1
        return item


class OpalParser(Stream[token.Token]):
    @overload
    def parse_token(
        self, kind: kind.PrimitiveKind
    ) -> ParseResult[token.PrimitiveToken]:
        ...

    @overload
    def parse_token(self, kind: kind.KeywordKind) -> ParseResult[token.KeywordToken]:
        ...

    @overload
    def parse_token(self, kind: kind.IntegerKind) -> ParseResult[token.IntegerToken]:
        ...

    @overload
    def parse_token(
        self, kind: kind.IdentifierKind
    ) -> ParseResult[token.IdentifierToken]:
        ...

    def parse_token(self, kind: kind.TokenKind) -> ParseResult[token.Token]:
        peeked = self.peek()
        if peeked is None:
            return ParseError.UnexpectedEOF
        if peeked.kind != kind:
            return ParseError.UnexpectedToken

        return self.next()

    def parse_keyword(self, keyword: kind.KeywordKind) -> ParseResult[node.KeywordNode]:
        result = self.parse_token(keyword)
        if isinstance(result, ParseError):
            return result
        token = result

        return node.KeywordNode(span=token.span, keyword=keyword)

    def parse_identifier(self) -> ParseResult[node.IdentifierNode]:
        result = self.parse_token(lex.Identifier)
        if isinstance(result, ParseError):
            return result
        token = result

        return node.IdentifierNode(span=token.span, name=token.value)

    def parse_integer(self) -> ParseResult[node.IntegerNode]:
        result = self.parse_token(lex.Integer)
        if isinstance(result, ParseError):
            return result
        token = result

        return node.IntegerNode(span=token.span, value=token.value)

    def parse_type(self) -> ParseResult[node.TypeNode]:
        raise NotImplementedError

    def parse_expression(self) -> ParseResult[node.ExpressionNode]:
        raise NotImplementedError

    def parse_constant_decl(self) -> ParseResult[node.ConstantNode]:
        # const name: type = val

        keyword_result = self.parse_keyword(kind.KeywordKind.Const)
        if isinstance(keyword_result, ParseError):
            return keyword_result
        keyword = keyword_result

        ident = require(self.parse_identifier())
        require(self.parse_token(kind.PrimitiveKind.Colon))
        type = require(self.parse_type())
        require(self.parse_token(kind.PrimitiveKind.Equals))
        expr = require(self.parse_expression())

        return node.ConstantNode(
            span=keyword.span + expr.span,
            name=ident.name,
            type=type,
            expr=expr,
        )

    def parse_variable_decl(self) -> ParseResult[node.VariableDeclarationNode]:
        # TODO: With type inference, this statement has more variation.
        # let name: type = expr

        # Parser fails if keyword isn't present. That is okay syntactically.
        keyword_result = self.parse_keyword(kind.KeywordKind.Let)
        if isinstance(keyword_result, ParseError):
            return keyword_result
        keyword = keyword_result

        # ParsING fails if these tokens aren't present. This is a syntax error.
        # throw an exception to immediately exit context. Exception is implied
        # by the `require` function.
        ident = require(self.parse_identifier())
        require(self.parse_token(kind.PrimitiveKind.Colon))
        type = require(self.parse_type())

        # Variable declaration is optionally followed by an initializer. Save/restore
        # state to mitigate case where initializer isn't present. Parsing is okay
        # regardless of whether the initializer is present or not.
        equals_or_none = attempt(
            self.stack, parser=partial(self.parse_token, kind=kind.PrimitiveKind.Equals)
        )

        # If equals is present, then expression must be present - otherwise its a
        # syntax error.
        expr = None
        if equals_or_none is not None:
            expr = require(self.parse_expression())

        return node.VariableDeclarationNode(
            span=keyword.span + type.span,
            name=ident.name,
            type=type,
            expr=expr,
        )

    def parse_enum_decl(self) -> ParseResult[node.EnumDeclarationNode]:
        keyword_result = self.parse_keyword(kind.KeywordKind.Enum)
        if isinstance(keyword_result, ParseError):
            return keyword_result
        _keyword = keyword_result

        # ident = require(self.parse_identifier())

        # # between(
        # #     parse_before=lambda: self.parse_token(kind.PrimitiveKind.LeftBrace),
        # #     parse_after=lambda: self.parse_token(kind.PrimitiveKind.RightBrace),
        # #     parse_between=
        # # )

        # return node.EnumDeclarationNode(
        #     span=keyword.span,
        #     name="Foo",
        #     members=[],
        # )
