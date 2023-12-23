import textwrap

from opyl.compile import lex, parse
from opyl.compile.token import Basic, IntegerLiteral
from opyl.compile.ast import Field, ConstDeclaration, VarDeclaration
from opyl.compile import ast
from opyl.compile import expr
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


def test_empty_if():
    source = textwrap.dedent(
        """if args == 0 {

        }
        """
    )
    tokens = lex.tokenize(source).unwrap()[0]
    result = parse.if_stmt.parse(tokens).unwrap()[0]
    assert result == ast.IfStatement(
        if_condition=expr.BinaryExpression(
            expr.BinOp.Equal, Identifier("args"), IntegerLiteral(0)
        ),
        if_statements=[],
        else_statements=[],
    )


def test_empty_struct():
    source = "struct Arguments {}"
    tokens = lex.tokenize(source).unwrap()[0]
    result = parse.struct_decl.parse(tokens).unwrap()[0]
    assert result == ast.StructDeclaration(
        name=Identifier("Arguments"), fields=[], functions=[]
    )


def test_struct_with_field():
    source = textwrap.dedent(
        """struct Arguments {
            count: u8
        }
        """
    )
    tokens = lex.tokenize(source).unwrap()[0]
    result = parse.struct_decl.parse(tokens).unwrap()[0]
    assert result == ast.StructDeclaration(
        name=Identifier("Arguments"),
        fields=[ast.Field(name=Identifier("count"), type=Identifier("u8"))],
        functions=[],
    )


def test_struct_with_func():
    source = textwrap.dedent(
        """struct Arguments {
            def len() -> u8 {}
        }
        """
    )
    tokens = lex.tokenize(source).unwrap()[0]
    result = parse.struct_decl.parse(tokens).unwrap()[0]
    assert result == ast.StructDeclaration(
        name=Identifier("Arguments"),
        fields=[],
        functions=[
            ast.FunctionDeclaration(
                name=Identifier("len"),
                signature=ast.FunctionSignature(
                    Identifier("len"), [], Maybe.Just(Identifier("u8"))
                ),
                body=[],
            )
        ],
    )


def test_struct_with_field_and_func():
    source = textwrap.dedent(
        """struct Arguments {
            count: u8
            def len() -> u8 {}
        }
        """
    )
    tokens = lex.tokenize(source).unwrap()[0]
    result = parse.struct_decl.parse(tokens).unwrap()[0]
    assert result == ast.StructDeclaration(
        name=Identifier("Arguments"),
        fields=[ast.Field(name=Identifier("count"), type=Identifier("u8"))],
        functions=[
            ast.FunctionDeclaration(
                name=Identifier("len"),
                signature=ast.FunctionSignature(
                    Identifier("len"), [], Maybe.Just(Identifier("u8"))
                ),
                body=[],
            )
        ],
    )


def test_empty_enum():
    source = textwrap.dedent("enum Color {}")
    tokens = lex.tokenize(source).unwrap()[0]
    result = parse.enum_decl.parse(tokens).unwrap()[0]
    assert result == ast.EnumDeclaration(
        name=Identifier("Color"),
        members=[],
    )


def test_enum_single_value():
    source = textwrap.dedent("enum Color {Red}")
    tokens = lex.tokenize(source).unwrap()[0]
    result = parse.enum_decl.parse(tokens).unwrap()[0]
    assert result == ast.EnumDeclaration(
        name=Identifier("Color"),
        members=[Identifier("Red")],
    )


def test_enum_multi_value():
    source = textwrap.dedent("enum Color {Red, Green}")
    tokens = lex.tokenize(source).unwrap()[0]
    result = parse.enum_decl.parse(tokens).unwrap()[0]
    assert result == ast.EnumDeclaration(
        name=Identifier("Color"),
        members=[Identifier("Red"), Identifier("Green")],
    )


def test_enum_multi_value_linesplit():
    source = textwrap.dedent(
        """enum Color {
            Red,
            Green
        }
        """
    )
    tokens = lex.tokenize(source).unwrap()[0]
    result = parse.enum_decl.parse(tokens).unwrap()[0]
    assert result == ast.EnumDeclaration(
        name=Identifier("Color"),
        members=[Identifier("Red"), Identifier("Green")],
    )


def test_enum_trailing_comma():
    source = textwrap.dedent(
        """enum Color {
            Red,
        }
        """
    )
    tokens = lex.tokenize(source).unwrap()[0]
    result = parse.enum_decl.parse(tokens).unwrap()[0]
    assert result == ast.EnumDeclaration(
        name=Identifier("Color"),
        members=[Identifier("Red")],
    )


def test_if_stmt_no_body():
    tokens = lex.tokenize("if expr {}").unwrap()[0]
    result = parse.if_stmt.parse(tokens).unwrap()[0]
    assert result == ast.IfStatement(
        if_condition=Identifier("expr"),
        if_statements=[],
        else_statements=[],
    )


def test_if_stmt_with_body():
    source = textwrap.dedent(
        """if expr {
            1 + 2
        }
        """
    )
    tokens = lex.tokenize(source).unwrap()[0]
    result = parse.if_stmt.parse(tokens).unwrap()[0]
    assert result == ast.IfStatement(
        if_condition=Identifier("expr"),
        if_statements=[
            expr.BinaryExpression(
                expr.BinOp.Addition, IntegerLiteral(1), IntegerLiteral(2)
            )
        ],
        else_statements=[],
    )


def test_simple_type_def():
    tokens = lex.tokenize("type ParseResult = Match").unwrap()[0]
    result = parse.type_def.parse(tokens).unwrap()[0]
    assert result == ast.TypeDefinition(
        name=Identifier("ParseResult"), types=[Identifier("Match")]
    )


def test_union_type_def():
    tokens = lex.tokenize("type ParseResult = Match | NoMatch").unwrap()[0]
    result = parse.type_def.parse(tokens).unwrap()[0]
    assert result == ast.TypeDefinition(
        name=Identifier("ParseResult"),
        types=[Identifier("Match"), Identifier("NoMatch")],
    )


def test_when_stmt_empty():
    tokens = lex.tokenize("when val {}").unwrap()[0]
    result = parse.when_stmt.parse(tokens).unwrap()[0]
    assert result == ast.WhenStatement(
        expression=Identifier("val"),
        target=Maybe.Nothing,
        is_clauses=[],
        else_statements=[],
    )


def test_when_stmt_empty_with_as():
    tokens = lex.tokenize("when val as rv {}").unwrap()[0]
    result = parse.when_stmt.parse(tokens).unwrap()[0]
    assert result == ast.WhenStatement(
        expression=Identifier("val"),
        target=Maybe.Just(Identifier("rv")),
        is_clauses=[],
        else_statements=[],
    )


def test_when_stmt_populated():
    source = textwrap.dedent(
        """when val {
            is Foo {}
        }
        """
    )
    tokens = lex.tokenize(source).unwrap()[0]
    result = parse.when_stmt.parse(tokens).unwrap()[0]
    assert result == ast.WhenStatement(
        expression=Identifier("val"),
        target=Maybe.Nothing,
        is_clauses=[ast.IsClause(target=Identifier("Foo"), statements=[])],
        else_statements=[],
    )


def test_when_stmt_populated_with_as():
    source = textwrap.dedent(
        """when val as rv {
            is Foo {}
        }
        """
    )
    tokens = lex.tokenize(source).unwrap()[0]
    result = parse.when_stmt.parse(tokens).unwrap()[0]
    assert result == ast.WhenStatement(
        expression=Identifier("val"),
        target=Maybe.Just(Identifier("rv")),
        is_clauses=[ast.IsClause(target=Identifier("Foo"), statements=[])],
        else_statements=[],
    )
