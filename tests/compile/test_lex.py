from opyl.compile import lex


def test_keyword():
    assert lex.tokenize("struct") == [
        lex.Token(kind=lex.KeywordTokenKind.Struct, span=lex.Span(0, 6))
    ]


def test_single_identifier():
    assert lex.tokenize("foo") == [
        lex.Token(kind=lex.IdentifierTokenValue(identifier="foo"), span=lex.Span(0, 3))
    ]


def test_single_identifier_with_underscore():
    assert lex.tokenize("foo_bar") == [
        lex.Token(
            kind=lex.IdentifierTokenValue(identifier="foo_bar"), span=lex.Span(0, 7)
        )
    ]


def test_double_identifier():
    assert lex.tokenize("foo bar") == [
        lex.Token(kind=lex.IdentifierTokenValue(identifier="foo"), span=lex.Span(0, 3)),
        lex.Token(kind=lex.IdentifierTokenValue(identifier="bar"), span=lex.Span(4, 7)),
    ]


def test_primitive():
    assert lex.tokenize("+") == [
        lex.Token(kind=lex.PrimitiveTokenKind.Plus, span=lex.Span(0, 1))
    ]


def test_integer():
    assert lex.tokenize("5") == [
        lex.Token(kind=lex.IntegerTokenValue(5), span=lex.Span(0, 1))
    ]
