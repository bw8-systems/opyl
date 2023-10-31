"""
Tools for parsing the Opal grammar.
"""
from dataclasses import dataclass
from typing import Callable, Sequence, Any
from functools import partial

from compile import token, node

from support.split_monad import Result, Okay, Error, Option, Nil, Some


class ParseException(ValueError):
    ...


class UnexpectedEOF(ParseException):
    ...


class UnexpectedToken(ParseException):
    ...


type ParseResult[T] = Result[T, ParseException]
type Parser[T] = Callable[[], ParseResult[T]]


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


def attempt[T](stack: Stack, parser: Parser[T]) -> ParseResult[T]:
    stack.push()
    return parser().exit(stack.drop, stack.pop)


def between[Before, Between, After](
    parse_before: Parser[Before],
    parse_between: Parser[Between],
    parse_after: Parser[After],
) -> ParseResult[Between]:
    between = parse_before().and_then(lambda _: parse_between())
    if between.is_err():
        return between

    after = parse_after()
    if after.is_err():
        return Error(after.unwrap_err())

    return between


def choice[T](stack: Stack, parsers: Sequence[Parser[T]]) -> ParseResult[T]:
    for parser in parsers:
        option = attempt(stack, parser)

        if option.is_some():
            return Okay(option.unwrap())

    return Error(UnexpectedToken())


def either[T, U](
    stack: Stack, this: Parser[T], that: Parser[U]
) -> ParseResult[T] | ParseResult[U]:
    match this():
        case Okay(ok):
            return Okay(ok)
        case _:
            return that()


def many[T](stack: Stack, parser: Parser[T]) -> list[T]:
    items: list[T] = []

    while True:
        match attempt(stack, parser):
            case Nil():
                break
            case Some(item):
                items.append(item)

    return items


class Stream[T]:
    def __init__(self, stream: Sequence[T]):
        self.stack = Stack()
        self.stream = stream

    def __getitem__(self, idx: int) -> Option[T]:
        try:
            return Some(self.stream[self.stack.index])
        except IndexError:
            return Nil()

    def peek(self) -> Option[T]:
        return self[self.stack.index]

    def increment(self) -> None:
        self.stack.index += 1

    def next(self) -> ParseResult[T]:
        return (
            self.peek()
            .and_then(lambda item: self.increment() or Some(item))
            .ok_or(UnexpectedEOF())
        )


class TokenParser(Stream[token.Token]):
    def primitive(
        self,
        kind: token.PrimitiveKind,
    ) -> ParseResult[token.PrimitiveToken]:
        match self.peek():
            case Nil():
                return Error(UnexpectedEOF())
            case Some(token.PrimitiveToken(k) as tok) if k is kind:
                self.next()
                return Okay(tok)
            case _:
                return Error(UnexpectedToken())

    def keyword(self, keyword: token.KeywordKind) -> ParseResult[node.Keyword]:
        match self.peek():
            case Nil():
                return Error(UnexpectedEOF())
            case Some(token.KeywordToken() as tok):
                self.next()
                return Okay(node.Keyword(span=tok.span, kind=keyword))
            case _:
                return Error(UnexpectedToken())

    def identifier(self) -> ParseResult[node.IdentifierNode]:
        match self.peek():
            case Nil():
                return Error(UnexpectedEOF())
            case Some(token.IdentifierToken() as tok):
                self.next()
                return Okay(node.IdentifierNode(span=tok.span, name=tok.value))
            case _:
                return Error(UnexpectedToken())

    def integer(self) -> ParseResult[node.IntegerNode]:
        match self.peek():
            case Nil():
                return Error(UnexpectedEOF())
            case Some(token.IntegerToken() as tok):
                self.next()
                return Okay(node.IntegerNode(span=tok.span, value=tok.value))
            case _:
                return Error(UnexpectedToken())


@dataclass
class OpalParser(TokenParser):
    def parse_variable_declaration(self) -> ParseResult[Any]:
        match attempt(
            self.stack, partial(self.keyword, token.KeywordKind.Let)
        ).and_then(
            lambda keyword: self.identifier().and_then(
                lambda identifier: Okay((keyword, identifier))
            )
        ):
            case Error(err):
                return Error(err)
            case Okay((keyword, identifier)):
                self.primitive(token.PrimitiveKind.Colon).and_then(
                    lambda _: self.identifier()
                ).and_then(
                    lambda type_name: self.primitive(token.PrimitiveKind.Equals).ok()
                )

        return NotImplemented

    def parse_expression(self) -> ParseResult[Any]:
        ...
