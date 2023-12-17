import typing as t

from compile import token
from compile import ast
from compile.token import Token, Keyword, Basic
from compile.error import ParseError
from compile.pratt import expression
from support.stream import Stream
from support.combinator import Parser, ParseResult
from support.union import Maybe
from support.atoms import just, ident

newlines = just(Basic.NewLine).repeated()


def block[T](item: Parser[Token, T, ParseError]) -> Parser[Token, list[T], ParseError]:
    return (
        just(Basic.LeftBrace)
        .ignore_then(item.repeated())
        .then_ignore(just(Basic.RightBrace))
    )


type = ident
expr = expression(0)

field = (
    ident.then(
        just(Basic.Colon)
        .require(ParseError.ToBeImproved)
        .ignore_then(type.require(ParseError.ToBeImproved))
    )
    .require(ParseError.ToBeImproved)
    .map(lambda items: ast.Field(name=items[0], type=items[1]))
)

const_decl = (
    just(Keyword.Const)
    .ignore_then(field)
    .then(just(Basic.Equal).ignore_then(expr).require(ParseError.ToBeImproved))
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
    .ignore_then(just(Keyword.Mut).or_not().map(lambda mut: mut is not Maybe.Nothing))
    .then(field)
    .then(just(Basic.Equal).ignore_then(expr).require(ParseError.ToBeImproved))
    .map(
        lambda items: ast.VarDeclaration(
            is_mut=items[0][0],
            name=items[0][1].name,
            type=Maybe.Just(items[0][1].type),
            initializer=items[1],
        )
    )
)

param_spec = (
    just(Keyword.Anon)
    .or_not()
    .map(lambda anon: anon is not Maybe.Nothing)
    .then(ident.require(ParseError.ToBeImproved))
    .then_ignore(just(Basic.Colon).require(ParseError.ToBeImproved))
    .then(
        just(Keyword.Mut)
        .or_not()
        .map(lambda mut: mut is not Maybe.Nothing)
        .then(type)
        .require(ParseError.ToBeImproved)
    )
    .map(
        lambda items: ast.ParamSpec(
            is_anon=items[0][0],
            ident=items[0][1],
            is_mut=items[1][0],
            type=items[1][1],
        )
    )
)

func_sig = (
    just(Keyword.Def)
    .ignore_then(ident.require(ParseError.ToBeImproved))
    .then(
        newlines.ignore_then(param_spec)
        .separated_by(just(Basic.Comma).then(just(Basic.NewLine).repeated()))
        .allow_trailing()
        .delimited_by(
            start=just(Basic.LeftParenthesis),
            end=newlines.ignore_then(just(Basic.RightParenthesis)),
        )
    )
    .then(
        just(Basic.RightArrow)
        .ignore_then(ident.require(ParseError.ToBeImproved))
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


class Statement(Parser[Token, ast.Statement, ParseError]):
    @t.override
    def parse(
        self, input: Stream[token.Token]
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


stmt = Statement()

break_stmt = just(Keyword.Break).map(lambda _: ast.BreakStatement())
continue_stmt = just(Keyword.Continue).map(lambda _: ast.ContinueStatement())
return_stmt = (
    just(Keyword.Return)
    .ignore_then(expr)
    .map(lambda item: ast.ReturnStatement(expression=Maybe.Just(item)))
)

func_decl = (
    func_sig.then_ignore(just(Basic.NewLine).or_not())
    .then(
        newlines.ignore_then(stmt)
        .separated_by(just(Basic.NewLine).repeated())
        .allow_trailing()
        .delimited_by(start=just(Basic.LeftBrace), end=just(Basic.RightBrace))
    )
    .map(
        lambda items: ast.FunctionDeclaration(
            name=items[0].name,
            signature=items[0],
            body=items[1],
        )
    )
)

struct_decl = (
    just(Keyword.Struct)
    .ignore_then(ident.require(ParseError.ToBeImproved))
    .then_ignore(just(Basic.NewLine).or_not())
    .then(
        newlines.ignore_then(field)
        .separated_by(just(Basic.NewLine).repeated())
        .at_least(1)
        .allow_trailing()
        .delimited_by(
            start=just(Basic.LeftBrace),
            end=newlines.ignore_then(just(Basic.RightBrace)),
        )
    )
    .map(
        lambda items: ast.StructDeclaration(
            name=items[0],
            fields=items[1],
            functions=[],
        )
    )
)

enum_decl = (
    just(Keyword.Enum)
    .ignore_then(ident.require(ParseError.ToBeImproved))
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

union_decl = (
    just(Keyword.Union)
    .ignore_then(ident.require(ParseError.ToBeImproved))
    .then_ignore(just(Basic.Equal))
    .then(type.separated_by(just(Basic.Pipe)).at_least(2))
    .then_ignore(just(Basic.NewLine).or_not())
    .then(
        (
            just(Basic.LeftBrace)
            .ignore_then(
                newlines.ignore_then(func_decl)
                .separated_by(just(Basic.NewLine).repeated())
                .allow_leading()
                .allow_trailing()
            )
            .then_ignore(just(Basic.RightBrace))
        ).or_else([])
    )
    .map(
        lambda items: ast.UnionDeclaration(
            name=items[0][0],
            members=items[0][1],
            functions=items[1],
        )
    )
)

trait_decl = (
    just(Keyword.Trait)
    .ignore_then(ident.require(ParseError.ToBeImproved))
    .then_ignore(just(Basic.NewLine).or_not())
    .then(
        newlines.ignore_then(func_sig)
        .separated_by(just(Basic.NewLine).repeated())
        .allow_trailing()
        .delimited_by(
            start=just(Basic.LeftBrace),
            end=newlines.ignore_then(just(Basic.RightBrace)),
        )
    )
    .map(lambda items: ast.TraitDeclaration(*items))
)


if_stmt = (
    just(Keyword.If)
    .ignore_then(expr.require(ParseError.ToBeImproved))
    .then(block(stmt).map(lambda _stmts: []))
    .then(just(Keyword.Else).or_not().ignore_then(block(stmt).map(lambda _stmts: [])))
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
    .map(lambda items: ast.WhileLoop(condition=items[0], statements=items[1]))
)

for_loop = (
    just(Keyword.For)
    .ignore_then(ident)
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
    .ignore_then(type)
    .then(block(stmt))
    .map(lambda items: ast.IsClause(*items))
)

when_stmt = (  # Definitely needs closer look at the optional parts
    just(Keyword.When)
    .ignore_then(expr)
    .then(just(Keyword.As).ignore_then(ident).or_not())
    .then(
        is_arm.separated_by(just(Basic.NewLine))
        .then(
            just(Keyword.Else)
            .ignore_then(block(stmt))
            .or_not()
            .map(lambda stmts: list[ast.Statement]())  # TODO: testing only
        )
        .delimited_by(start=just(Basic.LeftBrace), end=just(Basic.RightBrace))
    )
    .map(
        lambda items: ast.WhenStatement(
            expression=items[0][0],
            target=items[0][1],
            is_clauses=items[1][0],
            else_statements=items[1][1],
        )
    )
)

decl = (
    enum_decl
    | struct_decl
    | const_decl
    | let_decl
    | func_decl
    | union_decl
    | trait_decl
)

decls = newlines.ignore_then(decl.separated_by(newlines.at_least(1)))


# def parse(source: str) -> ...:
#     tokens = lex.tokenize(source)

#     stream = Stream[lexemes.Token](
#         list(
#             filter(
#                 lambda token: not (
#                     isinstance(token, lexemes.Whitespace)
#                     or isinstance(token, lexemes.Comment)
#                 ),
#                 tokens,
#             )
#         )
#     )
