from opyl.compile import lex, parse
from opyl.compile.token import Basic, IntegerLiteral
from opyl.compile.ast import Field, ConstDeclaration, VarDeclaration
from opyl.compile import ast
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


# TODO: I don't think an identifier without a colon following it should be considered an
# an error since a standalone identifier is a valid expression. However, I'm not positive
# that there is anywhere in the grammar where a field *and* an expression would be valid
# syntax. For the time being, this is not considered an error case.
# def test_field_no_colon():
#     tokens = lex.tokenize("name Type").unwrap()[0]
#     result = parse.field.parse(tokens)
#     assert isinstance(result, ParseResult.Error)


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


def test_func_sig_with_return():
    tokens = lex.tokenize("def some_function(param: FooBar) -> MFDoom").unwrap()[0]
    result = parse.func_sig.parse(tokens).unwrap()[0]
    assert result == ast.FunctionSignature(
        Identifier("some_function"),
        [
            ast.ParamSpec(
                is_anon=False,
                ident=Identifier("param"),
                is_mut=False,
                type=Identifier("FooBar"),
            )
        ],
        Maybe.Just(Identifier("MFDoom")),
    )


def test_func_sig_without_return():
    tokens = lex.tokenize("def some_function(param: FooBar)").unwrap()[0]
    result = parse.func_sig.parse(tokens).unwrap()[0]
    assert result == ast.FunctionSignature(
        Identifier("some_function"),
        [
            ast.ParamSpec(
                is_anon=False,
                ident=Identifier("param"),
                is_mut=False,
                type=Identifier("FooBar"),
            )
        ],
        Maybe.Nothing,
    )
