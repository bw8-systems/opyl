from opyl.compile import lex, parse
from opyl.compile.token import IntegerLiteral
from opyl.compile.op_ast import Field, ConstDeclaration, VarDeclaration
from opyl.compile import op_ast
from opyl.compile import expr
from opyl.compile.token import Identifier
from opyl.support.combinator import ParseResult, PR
from opyl.support.union import Maybe

from .utils import parse_test

# TODO: Use a top-level parser for top-level decl tests.


def test_zero_newline():
    parse_test(parse.newlines, "", [])


def test_field():
    parse_test(parse.field, "name: Type", Field(Identifier("name"), Identifier("Type")))


# TODO: I don't think an identifier without a colon following it should be considered an
# an error since a standalone identifier is a valid expression. However, I'm not positive
# that there is anywhere in the grammar where a field *and* an expression would be valid
# syntax. For the time being, this is not considered an error case.
# def test_field_no_colon():
#     tokens = lex.tokenize("name Type").unwrap()[0]
#     result = parse.field.parse(tokens)
#     assert isinstance(result, ParseResult.Error)


def test_field_no_type_eof():
    result = lex.tokenize("name: ")
    print(result)
    tokens = result.stream
    result = parse.field.parse(tokens)
    assert isinstance(result, ParseResult.Error)


def test_field_no_type():
    tokens = lex.tokenize("name: 1").stream
    result = parse.field.parse(tokens)
    assert isinstance(result, ParseResult.Error)


def test_no_field():
    tokens = lex.tokenize("1").stream
    result = parse.field.parse(tokens)
    assert result is PR.NoMatch


def test_const_decl():
    parse_test(
        parse.const_decl,
        "const name: Type = 5",
        ConstDeclaration(Identifier("name"), Identifier("Type"), IntegerLiteral(5)),
    )


def test_let_decl():
    parse_test(
        parse.let_decl,
        "let name: Type = 5",
        VarDeclaration(
            Identifier("name"), False, Maybe.Just(Identifier("Type")), IntegerLiteral(5)
        ),
    )


def test_let_mut_decl():
    parse_test(
        parse.let_decl,
        "let mut name: Type = 5",
        VarDeclaration(
            Identifier("name"), True, Maybe.Just(Identifier("Type")), IntegerLiteral(5)
        ),
    )


def test_func_sig_with_return():
    parse_test(
        parse.func_sig,
        "def some_function(param: FooBar) -> MFDoom",
        op_ast.FunctionSignature(
            Identifier("some_function"),
            [
                op_ast.ParamSpec(
                    is_anon=False,
                    ident=Identifier("param"),
                    is_mut=False,
                    type=Identifier("FooBar"),
                )
            ],
            Maybe.Just(Identifier("MFDoom")),
        ),
    )


def test_func_sig_without_return():
    parse_test(
        parse.func_sig,
        "def some_function(param: FooBar)",
        op_ast.FunctionSignature(
            Identifier("some_function"),
            [
                op_ast.ParamSpec(
                    is_anon=False,
                    ident=Identifier("param"),
                    is_mut=False,
                    type=Identifier("FooBar"),
                )
            ],
            Maybe.Nothing,
        ),
    )


def test_empty_if():
    parse_test(
        parse.if_stmt,
        """if args == 0 {

        }
        """,
        op_ast.IfStatement(
            if_condition=expr.BinaryExpression(
                expr.BinOp.Equal, Identifier("args"), IntegerLiteral(0)
            ),
            if_statements=[],
            else_statements=[],
        ),
    )


def test_empty_struct():
    parse_test(
        parse.struct_decl,
        "struct Arguments {}",
        op_ast.StructDeclaration(name=Identifier("Arguments"), fields=[], functions=[]),
    )


def test_struct_with_field():
    parse_test(
        parse.struct_decl,
        """struct Arguments {
            count: u8
        }
        """,
        op_ast.StructDeclaration(
            name=Identifier("Arguments"),
            fields=[op_ast.Field(name=Identifier("count"), type=Identifier("u8"))],
            functions=[],
        ),
    )


def test_struct_with_func():
    parse_test(
        parse.struct_decl,
        """struct Arguments {
            def len() -> u8 {}
        }
        """,
        op_ast.StructDeclaration(
            name=Identifier("Arguments"),
            fields=[],
            functions=[
                op_ast.FunctionDeclaration(
                    name=Identifier("len"),
                    signature=op_ast.FunctionSignature(
                        Identifier("len"), [], Maybe.Just(Identifier("u8"))
                    ),
                    body=[],
                )
            ],
        ),
    )


def test_struct_with_field_and_func():
    parse_test(
        parse.struct_decl,
        """struct Arguments {
            count: u8
            def len() -> u8 {}
        }
        """,
        op_ast.StructDeclaration(
            name=Identifier("Arguments"),
            fields=[op_ast.Field(name=Identifier("count"), type=Identifier("u8"))],
            functions=[
                op_ast.FunctionDeclaration(
                    name=Identifier("len"),
                    signature=op_ast.FunctionSignature(
                        Identifier("len"), [], Maybe.Just(Identifier("u8"))
                    ),
                    body=[],
                )
            ],
        ),
    )


def test_empty_enum():
    parse_test(
        parse.enum_decl,
        "enum Color {}",
        op_ast.EnumDeclaration(
            name=Identifier("Color"),
            members=[],
        ),
    )


def test_enum_single_value():
    parse_test(
        parse.enum_decl,
        "enum Color {Red}",
        op_ast.EnumDeclaration(
            name=Identifier("Color"),
            members=[Identifier("Red")],
        ),
    )


def test_enum_multi_value():
    parse_test(
        parse.enum_decl,
        "enum Color {Red, Green}",
        op_ast.EnumDeclaration(
            name=Identifier("Color"),
            members=[Identifier("Red"), Identifier("Green")],
        ),
    )


def test_enum_multi_value_linesplit():
    parse_test(
        parse.enum_decl,
        """enum Color {
            Red,
            Green
        }
        """,
        op_ast.EnumDeclaration(
            name=Identifier("Color"),
            members=[Identifier("Red"), Identifier("Green")],
        ),
    )


def test_enum_trailing_comma():
    parse_test(
        parse.enum_decl,
        """enum Color {
            Red,
        }
        """,
        op_ast.EnumDeclaration(
            name=Identifier("Color"),
            members=[Identifier("Red")],
        ),
    )


def test_if_stmt_no_body():
    parse_test(
        parse.if_stmt,
        "if expr {}",
        op_ast.IfStatement(
            if_condition=Identifier("expr"),
            if_statements=[],
            else_statements=[],
        ),
    )


def test_if_stmt_with_body():
    parse_test(
        parse.if_stmt,
        """if expr {
            1 + 2
        }
        """,
        op_ast.IfStatement(
            if_condition=Identifier("expr"),
            if_statements=[
                expr.BinaryExpression(
                    expr.BinOp.Addition, IntegerLiteral(1), IntegerLiteral(2)
                )
            ],
            else_statements=[],
        ),
    )


def test_simple_type_def():
    parse_test(
        parse.type_def,
        "type ParseResult = Match",
        op_ast.TypeDefinition(
            name=Identifier("ParseResult"), types=[Identifier("Match")]
        ),
    )


def test_union_type_def():
    parse_test(
        parse.type_def,
        "type ParseResult = Match | NoMatch",
        op_ast.TypeDefinition(
            name=Identifier("ParseResult"),
            types=[Identifier("Match"), Identifier("NoMatch")],
        ),
    )


def test_when_stmt_empty():
    parse_test(
        parse.when_stmt,
        "when val {}",
        op_ast.WhenStatement(
            expression=Identifier("val"),
            target=Maybe.Nothing,
            is_clauses=[],
            else_statements=[],
        ),
    )


def test_when_stmt_empty_with_as():
    parse_test(
        parse.when_stmt,
        "when val as rv {}",
        op_ast.WhenStatement(
            expression=Identifier("val"),
            target=Maybe.Just(Identifier("rv")),
            is_clauses=[],
            else_statements=[],
        ),
    )


def test_when_stmt_populated():
    parse_test(
        parse.when_stmt,
        """when val {
            is Foo {}
        }
        """,
        op_ast.WhenStatement(
            expression=Identifier("val"),
            target=Maybe.Nothing,
            is_clauses=[op_ast.IsClause(target=Identifier("Foo"), statements=[])],
            else_statements=[],
        ),
    )


def test_when_stmt_populated_with_as():
    parse_test(
        parse.when_stmt,
        """when val as rv {
            is Foo {}
        }
        """,
        op_ast.WhenStatement(
            expression=Identifier("val"),
            target=Maybe.Just(Identifier("rv")),
            is_clauses=[op_ast.IsClause(target=Identifier("Foo"), statements=[])],
            else_statements=[],
        ),
    )


# def test_when_stmt_with_else():
#     source = textwrap.dedent(
#         """when val {
#             else {}
#         }
#         """
#     )
#     tokens = lex.tokenize(source).unwrap()[0]
#     result = parse.when_stmt.parse(tokens).unwrap()[0]
#     assert result == ast.WhenStatement(
#         expression=Identifier("val"),
#         target=Maybe.Nothing,
#         is_clauses=[],
#         else_statements=[],
#     )
