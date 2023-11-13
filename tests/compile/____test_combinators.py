import typing as t
from abc import ABC, abstractmethod

from dataclasses import dataclass

import pytest

from opyl import lex
from opyl import lexemes
from opyl import nodes
from opyl import parse
from opyl import combinators
from opyl import positioning
from opyl import errors
from opyl.compile.positioning import Span, TextPosition, Stream
from opyl.compile.lexemes import PrimitiveKind as PK
from opyl.compile.lexemes import KeywordKind as KK

source = """
let foo: Foo = 5

union Token = Primitive | Keyword {
    def foo() {}
    def bar() {}
    def baz() {}
}

struct TextPosition {
    absolute: u32
    line: u32
    column: u32
}

struct Span {
    start: TextPosition
    stop: TextPosition
}
"""


class TestSimpleKeyword:
    def test_single_keyword(self):
        keyword = combinators.Keyword(
            stream=positioning.Stream(lex.tokenize("const")),
            kind=lexemes.KeywordKind.Const,
        ).parse()

        assert isinstance(keyword, lexemes.Keyword)
        assert keyword.kind == lexemes.KeywordKind.Const
        assert keyword.span.start == positioning.TextPosition.default()
        assert keyword.span.stop == positioning.TextPosition(
            absolute=5, line=0, column=5
        )

    def test_multiple_keyword(self):
        stream = positioning.Stream(lex.tokenize("let mut"))

        let = combinators.Keyword(
            stream=stream,
            kind=lexemes.KeywordKind.Let,
        ).parse()

        assert isinstance(let, lexemes.Keyword)
        assert let.kind == lexemes.KeywordKind.Let
        assert let.span.start == positioning.TextPosition.default()
        assert let.span.stop == positioning.TextPosition(absolute=3, line=0, column=3)

        mut = combinators.Keyword(
            stream=stream,
            kind=lexemes.KeywordKind.Mut,
        ).parse()

        assert isinstance(mut, lexemes.Keyword)
        assert mut.kind == lexemes.KeywordKind.Mut
        assert mut.span.start == positioning.TextPosition(absolute=4, line=0, column=4)
        assert mut.span.stop == positioning.TextPosition(absolute=7, line=0, column=7)


def test_separator():
    keyword = (
        combinators.Keyword(
            stream=positioning.Stream(lex.tokenize("const, ")),
            kind=lexemes.KeywordKind.Const,
        )
        .followed_by(lexemes.PrimitiveKind.Comma)
        .parse()
    )

    assert isinstance(keyword, lexemes.Keyword)
    assert keyword.kind == lexemes.KeywordKind.Const
    assert keyword.span.start == positioning.TextPosition.default()
    assert keyword.span.stop == positioning.TextPosition(absolute=5, line=0, column=5)


def test_and_also():
    parsed = (
        combinators.Keyword(
            stream=positioning.Stream(lex.tokenize("const, ")),
            kind=lexemes.KeywordKind.Const,
        )
        .and_also(lambda: "foo")
        .parse()
    )

    assert parsed == (
        lexemes.Keyword(
            span=positioning.Span(
                positioning.TextPosition(0, 0, 0), positioning.TextPosition(5, 0, 5)
            ),
            kind=lexemes.KeywordKind.Const,
        ),
        "foo",
    )


def test_const():
    source = "const FOO: Foo = 5\n"
    const = parse.OpalParser.from_source(source).constant_declaration()

    assert const == nodes.ConstDeclaration(
        span=Span(
            start=TextPosition(absolute=0, line=0, column=0),
            stop=TextPosition(absolute=19, line=1, column=0),
        ),
        name=nodes.Identifier(
            span=Span(
                start=TextPosition(absolute=6, line=0, column=6),
                stop=TextPosition(absolute=9, line=0, column=9),
            ),
            name="FOO",
        ),
        type=nodes.Identifier(
            span=Span(
                start=TextPosition(absolute=11, line=0, column=11),
                stop=TextPosition(absolute=14, line=0, column=14),
            ),
            name="Foo",
        ),
        initializer=nodes.IntegerLiteral(
            span=Span(
                start=TextPosition(absolute=17, line=0, column=17),
                stop=TextPosition(absolute=18, line=0, column=18),
            ),
            integer=5,
        ),
    )


type Parser[T] = t.Callable[[], T]


def test_proto():
    source = "const Foo"

    _val = OpalParser(source)
