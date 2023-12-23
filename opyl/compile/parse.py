import typing as t

from opyl.compile import ast
from opyl.compile.token import Token, Keyword, Basic, Identifier
from opyl.compile.error import ParseError
from opyl.compile.pratt import expr
from opyl.support.stream import Stream
from opyl.support.combinator import Parser, ParseResult
from opyl.support.union import Maybe
from opyl.support.atoms import just, ident, newlines


class Statement(Parser[Token, ast.Statement, ParseError]):
    @t.override
    def parse(
        self, input: Stream[Token]
    ) -> ParseResult.Type[Token, ast.Statement, ParseError]:
        return (
            return_stmt
            | if_stmt
            | for_loop
            | while_loop
            | when_stmt
            | let_decl
            | const_decl
            | expr
        ).parse(input)


def block[
    T
](these: Parser[Token, T, ParseError], label: str = "block") -> Parser[
    Token, list[T], ParseError
]:
    return newlines.ignore_then(
        lines(these)
        .delimited_by(just(Basic.LeftBrace), just(Basic.RightBrace))
        .require(ParseError(expected="}", following=label))
    )


def block_pair[
    T, U
](
    these: Parser[Token, T, ParseError],
    those: Parser[Token, U, ParseError],
    label: str = "block",
) -> Parser[Token, tuple[list[T], list[U]], ParseError]:
    return (
        newlines.ignore_then(
            these.separated_by(newlines.at_least(1))
            .allow_leading()
            .allow_trailing()
            .then(
                those.separated_by(newlines.at_least(1))
                .allow_leading()
                .allow_trailing()
            )
        )
        .delimited_by(just(Basic.LeftBrace), just(Basic.RightBrace))
        .require(ParseError(expected="'}'", following=label))
    )


def lines[
    T
](parser: Parser[Token, T, ParseError]) -> Parser[Token, list[T], ParseError]:
    return newlines.ignore_then(
        parser.separated_by(newlines.at_least(1)).allow_leading().allow_trailing()
    )


def named_decl(keyword: Keyword) -> Parser[Token, Identifier, ParseError]:
    return just(keyword).ignore_then(
        ident.require(
            ParseError(expected="identifier", following=f"'{keyword.value}' keyword")
        )
    )


type = ident


field = ident.then(
    just(Basic.Colon).ignore_then(
        type.require(ParseError(expected="type", following="':'"))
    )
).map(lambda items: ast.Field(name=items[0], type=items[1]))

initializer = just(Basic.Equal).ignore_then(
    expr.require(ParseError(expected="expression", following="'='"))
)

const_decl = (
    just(Keyword.Const)
    .ignore_then(field)
    .then(initializer)
    .map(
        lambda items: ast.ConstDeclaration(
            name=items[0].name,
            type=items[0].type,
            initializer=items[1],
        )
    )
)

let_decl = (
    just(Keyword.Let)
    .ignore_then(just(Keyword.Mut).boolean())
    .then(field)
    .then(initializer)
    .map(
        lambda items: ast.VarDeclaration(
            is_mut=items[0][0],
            name=items[0][1].name,
            type=Maybe.Just(items[0][1].type),
            initializer=items[1],
        )
    )
)

# TODO: Error handling: Identifier should not be required if `anon` wasn't
# present because in that case the identifier is the first token of the node.
param_spec = (
    just(Keyword.Anon)
    .boolean()
    .then(ident)
    .then_ignore(just(Basic.Colon))
    .then(just(Keyword.Mut).boolean())
    .then(type)
    .map(
        lambda items: ast.ParamSpec(
            is_anon=items[0][0][0],
            ident=items[0][0][1],
            is_mut=items[0][1],
            type=items[1],
        )
    )
)

func_sig = (
    named_decl(Keyword.Def)
    .then(
        newlines.ignore_then(param_spec)
        .separated_by(just(Basic.Comma))
        .allow_trailing()
        .then_ignore(newlines)
        .delimited_by(just(Basic.LeftParenthesis), just(Basic.RightParenthesis))
    )
    .then(
        just(Basic.RightArrow)
        .ignore_then(ident.require(ParseError(expected="identifier", following="'->'")))
        .or_not()
    )
    .map(
        lambda items: ast.FunctionSignature(
            name=items[0][0],
            params=items[0][1],
            return_type=items[1],
        )
    )
)

stmt = Statement()


break_stmt = just(Keyword.Break).to(ast.BreakStatement())
continue_stmt = just(Keyword.Continue).to(ast.ContinueStatement())
return_stmt = (
    just(Keyword.Return)
    .ignore_then(expr)
    .map(lambda item: ast.ReturnStatement(expression=Maybe.Just(item)))
)

func_decl = func_sig.then(block(stmt, "function definition")).map(
    lambda items: ast.FunctionDeclaration(
        name=items[0].name,
        signature=items[0],
        body=items[1],
    )
)

struct_decl = (
    named_decl(Keyword.Struct)
    .then(block_pair(field, func_decl, "struct definition"))
    .map(
        lambda items: ast.StructDeclaration(
            name=items[0],
            fields=items[1][0],
            functions=items[1][1],
        )
    )
)

enum_decl = (
    named_decl(Keyword.Enum)
    .then_ignore(just(Basic.NewLine).or_not())
    .then(
        newlines.ignore_then(ident)
        .separated_by(just(Basic.Comma).then(just(Basic.NewLine).repeated()))
        .allow_trailing()
        .delimited_by(
            start=just(Basic.LeftBrace),
            end=newlines.ignore_then(just(Basic.RightBrace)),
        )
    )
    .map(lambda items: ast.EnumDeclaration(name=items[0], members=items[1]))
)

type_def = (
    named_decl(Keyword.Type)
    .then_ignore(just(Basic.Equal))
    .then(type.separated_by(just(Basic.Pipe)).at_least(1))
).map(lambda items: ast.TypeDefinition(*items))

trait_decl = (
    just(Keyword.Trait)
    .ignore_then(
        ident.require(ParseError(expected="identifier", following="'trait' keyword"))
    )
    .then(block(func_sig, "trait definition"))
    .map(lambda items: ast.TraitDeclaration(*items))
)


else_block = just(Keyword.Else).ignore_then(block(stmt, "else block"))

if_stmt = (
    just(Keyword.If)
    .ignore_then(
        expr.require(ParseError(expected="expression", following="'if' keyword"))
    )
    .then(block(stmt))
    .then(else_block.or_else([]))
    .map(
        lambda items: ast.IfStatement(
            if_condition=items[0][0],
            if_statements=items[0][1],
            else_statements=items[1],
        )
    )
)

loop_stmt = stmt | break_stmt | continue_stmt

while_loop = (
    just(Keyword.While)
    .ignore_then(expr)
    .then(block(loop_stmt))
    .map(lambda items: ast.WhileLoop(*items))
)

for_loop = (
    named_decl(Keyword.For)
    .then_ignore(just(Keyword.In))
    .then(expr)
    .then(block(loop_stmt))
    .map(
        lambda items: ast.ForLoop(
            target=items[0][0], iterator=items[0][1], statements=items[1]
        )
    )
)

is_arm = (
    just(Keyword.Is)
    .ignore_then(type.require(ParseError(expected="type", following="'is' keyword")))
    .then(block(stmt))
    .map(lambda items: ast.IsClause(*items))
)

# TODO: Multiple else clauses should be an error. Its okay if its not a syntax errors
# however the way that this parser is constructed causes information about whether there
# were multiple else clauses is lost. I just wanted to reuse the block_pair parser
# because needing to chain newlines and allow_trailing etc is verbose and muddying.
when_stmt = (
    just(Keyword.When)
    .ignore_then(expr)
    .then(just(Keyword.As).ignore_then(ident).or_not())
    .then(
        lines(is_arm)
        .then(else_block.or_else([]))
        .delimited_by(just(Basic.LeftBrace), just(Basic.RightBrace))
    )
).map(lambda item: ast.WhenStatement(item[0][0], item[0][1], item[1][0], item[1][1]))

decl = (
    enum_decl | struct_decl | const_decl | let_decl | func_decl | type_def | trait_decl
)

decls = lines(decl)


def parse(
    stream: Stream[Token],
) -> ParseResult.Type[Token, list[ast.Declaration], ParseError]:
    return decls.parse(stream)
