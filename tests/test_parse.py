from opyl.compile import lex, parse
from opyl.compile.token import Basic, IntegerLiteral
from opyl.compile.ast import Field, ConstDeclaration, VarDeclaration
from opyl.compile.token import Identifier
from opyl.support.combinator import ParseResult, PR
from opyl.support.union import Maybe

# TODO: Use a top-level parser for top-level decl tests.


def test_zero_newline():
    tokens = lex.tokenize("").unwrap()[0]
    result = parse.newlines.parse(tokens).unwrap()
    assert result[0] == []


def test_single_newline():
    tokens = lex.tokenize("\n").unwrap()[0]
    result = parse.newlines.parse(tokens).unwrap()
    assert result[0] == [Basic.NewLine]


def test_multiple_newlines():
    tokens = lex.tokenize("\n\n").unwrap()[0]
    result = parse.newlines.parse(tokens).unwrap()
    assert result[0] == [Basic.NewLine, Basic.NewLine]


def test_field():
    tokens = lex.tokenize("name: Type").unwrap()[0]
    result = parse.field.parse(tokens).unwrap()
    assert result[0] == Field(Identifier("name"), Identifier("Type"))


def test_field_no_colon():
    tokens = lex.tokenize("name Type").unwrap()[0]
    result = parse.field.parse(tokens)
    assert isinstance(result, ParseResult.Error)


def test_field_no_type_eof():
    tokens = lex.tokenize("name: ").unwrap()[0]
    result = parse.field.parse(tokens)
    assert isinstance(result, ParseResult.Error)


def test_field_no_type():
    tokens = lex.tokenize("name: 1").unwrap()[0]
    result = parse.field.parse(tokens)
    assert isinstance(result, ParseResult.Error)


def test_no_field():
    tokens = lex.tokenize("1").unwrap()[0]
    result = parse.field.parse(tokens)
    assert result is PR.NoMatch


def test_const_decl():
    tokens = lex.tokenize("const name: Type = 5").unwrap()[0]
    result = parse.const_decl.parse(tokens).unwrap()[0]
    assert result == ConstDeclaration(
        Identifier("name"), Identifier("Type"), IntegerLiteral(5)
    )


def test_let_decl():
    tokens = lex.tokenize("let name: Type = 5").unwrap()[0]
    result = parse.let_decl.parse(tokens).unwrap()[0]
    assert result == VarDeclaration(
        Identifier("name"), False, Maybe.Just(Identifier("Type")), IntegerLiteral(5)
    )


def test_let_mut_decl():
    tokens = lex.tokenize("let mut name: Type = 5").unwrap()[0]
    result = parse.let_decl.parse(tokens).unwrap()[0]
    assert result == VarDeclaration(
        Identifier("name"), True, Maybe.Just(Identifier("Type")), IntegerLiteral(5)
    )
