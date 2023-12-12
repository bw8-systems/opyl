import typing as t
from pprint import pprint

from compile import lexemes
from compile import nodes
from compile import lex
from compile.lexemes import KeywordKind as KK
from compile.lexemes import PrimitiveKind as PK
from compile.combinators import (
    TokenStream,
    Parser,
    Parse,
    just,
    block,
    ident,
    newlines,
    integer,
)


type = ident
expr = (ident | integer).map(lambda item: t.cast(nodes.Expression, item))


field = (
    ident.expect("Expected identifier.")
    .then(
        just(PK.Colon)
        .expect("Expected ':' after identifier.")
        .ignore_then(type.expect("expected type after ':'"))
    )
    .expect("Expected field of form `ident: Type`")
    .map(lambda items: nodes.Field(name=items[0], type=items[1]))
)

const_decl = (
    just(KK.Const)
    .ignore_then(field)
    .then(
        just(PK.Equal)
        .ignore_then(expr)
        .expect("Expected initializer after type annotation.")
    )
    .map(
        lambda items: nodes.ConstDeclaration(
            name=items[0].name,
            type=items[0].type,
            initializer=items[1],
        )
    )
)

let_decl = (
    just(KK.Let)
    .ignore_then(just(KK.Mut).or_not().map(lambda mut: mut is not None))
    .then(field)
    .then(
        just(PK.Equal)
        .ignore_then(expr)
        .expect("Expected initializer after type annotation.")
    )
    .map(
        lambda items: nodes.VarDeclaration(
            is_mut=items[0][0],
            name=items[0][1].name,
            type=items[0][1].type,
            initializer=items[1],
        )
    )
)

param_spec = (
    just(KK.Anon)
    .or_not()
    .map(lambda anon: anon is not None)
    .then(ident.expect("expected parameter name"))
    .then_ignore(just(PK.Colon).expect("Expected colon after identifier."))
    .then(
        just(KK.Mut)
        .or_not()
        .map(lambda mut: mut is not None)
        .then(type)
        .expect("expected parameter type")
    )
    .map(
        lambda items: nodes.ParamSpec(
            is_anon=items[0][0],
            ident=items[0][1],
            is_mut=items[1][0],
            type=items[1][1],
        )
    )
)

func_sig = (
    just(KK.Def)
    .ignore_then(ident.expect("Expected identifier after 'def' keyword."))
    .then(
        newlines.ignore_then(param_spec)
        .separated_by(just(PK.Comma).then(just(PK.NewLine).repeated()))
        .allow_trailing()
        .delimited_by(
            start=just(PK.LeftParenthesis),
            end=newlines.ignore_then(just(PK.RightParenthesis)),
        )
    )
    .then(
        just(PK.RightArrow)
        .ignore_then(ident.expect("Expected type name after '->' token."))
        .or_not()
    )
    .map(
        lambda items: nodes.FunctionSignature(
            name=items[0][0],
            params=items[0][1],
            return_type=items[1],
        )
    )
)


class Statement(Parser[nodes.Statement]):
    @t.override
    def parse(self, input: TokenStream) -> Parse.Result[nodes.Statement]:
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

break_stmt = just(KK.Break).map(lambda _: nodes.BreakStatement())
continue_stmt = just(KK.Continue).map(lambda _: nodes.ContinueStatement())
return_stmt = (
    just(KK.Return)
    .ignore_then(expr)
    .map(lambda item: nodes.ReturnStatement(expression=item))
)

func_decl = (
    func_sig.then_ignore(just(PK.NewLine).or_not())
    .then(
        newlines.ignore_then(stmt)
        .separated_by(just(PK.NewLine).repeated())
        .allow_trailing()
        .delimited_by(start=just(PK.LeftBrace), end=just(PK.RightBrace))
    )
    .map(
        lambda items: nodes.FunctionDeclaration(
            name=items[0].name,
            signature=items[0],
            body=items[1],
        )
    )
)

struct_decl = (
    just(KK.Struct)
    .ignore_then(ident.expect("expected identifier after 'struct' keyword."))
    .then_ignore(just(PK.NewLine).or_not())
    .then(
        newlines.ignore_then(field)
        .separated_by(just(PK.NewLine).repeated())
        .at_least(1)
        .allow_trailing()
        .delimited_by(
            start=just(PK.LeftBrace), end=newlines.ignore_then(just(PK.RightBrace))
        )
    )
    .map(
        lambda items: nodes.StructDeclaration(
            name=items[0],
            fields=items[1],
            functions=[],
        )
    )
)

enum_decl = (
    just(KK.Enum)
    .ignore_then(ident.expect("expected identifier after 'enum' keyword."))
    .then_ignore(just(PK.NewLine).or_not())
    .then(
        newlines.ignore_then(ident)
        .separated_by(just(PK.Comma).then(just(PK.NewLine).repeated()))
        .allow_trailing()
        .delimited_by(
            start=just(PK.LeftBrace), end=newlines.ignore_then(just(PK.RightBrace))
        )
    )
    .map(lambda items: nodes.EnumDeclaration(name=items[0], members=items[1]))
)

union_decl = (
    just(KK.Union)
    .ignore_then(ident.expect("expected identifier after 'union' keyword."))
    .then_ignore(just(PK.Equal))
    .then(type.separated_by(just(PK.Pipe)).at_least(2))
    .then_ignore(just(PK.NewLine).or_not())
    .then(
        (
            just(PK.LeftBrace)
            .ignore_then(
                newlines.ignore_then(func_decl)
                .separated_by(just(PK.NewLine).repeated())
                .allow_leading()
                .allow_trailing()
            )
            .then_ignore(just(PK.RightBrace))
        ).or_else([])
    )
    .map(
        lambda items: nodes.UnionDeclaration(
            name=items[0][0],
            members=items[0][1],
            functions=items[1],
        )
    )
)

trait_decl = (
    just(KK.Trait)
    .ignore_then(ident.expect("Expected identifier after 'trait' keyword."))
    .then_ignore(just(PK.NewLine).or_not())
    .then(
        newlines.ignore_then(func_sig)
        .separated_by(just(PK.NewLine).repeated())
        .allow_trailing()
        .delimited_by(
            start=just(PK.LeftBrace), end=newlines.ignore_then(just(PK.RightBrace))
        )
    )
    .map(lambda items: nodes.TraitDeclaration(*items))
)


if_stmt = (
    just(KK.If)
    .ignore_then(expr.expect("expected conditional expression after 'if' keyword"))
    .then(block(stmt).map(lambda _stmts: []))
    .then(just(KK.Else).or_not().ignore_then(block(stmt).map(lambda _stmts: [])))
    .map(
        lambda items: nodes.IfStatement(
            if_condition=items[0][0],
            if_statements=items[0][1],
            else_statements=items[1],
        )
    )
)

loop_stmt = stmt | break_stmt | continue_stmt

while_loop = (
    just(KK.While)
    .ignore_then(expr)
    .then(block(loop_stmt))
    .map(lambda items: nodes.WhileLoop(condition=items[0], statements=items[1]))
)

for_loop = (
    just(KK.For)
    .ignore_then(ident)
    .then_ignore(just(KK.In))
    .then(expr)
    .then(block(loop_stmt))
    .map(
        lambda items: nodes.ForLoop(
            target=items[0][0], iterator=items[0][1], statements=items[1]
        )
    )
)

is_arm = (
    just(KK.Is)
    .ignore_then(type)
    .then(block(stmt))
    .map(lambda items: nodes.IsClause(*items))
)

when_stmt = (  # Definitely needs closer look at the optional parts
    just(KK.When)
    .ignore_then(expr)
    .then(just(KK.As).ignore_then(ident).or_not())
    .then(
        is_arm.separated_by(just(PK.NewLine))
        .then(
            just(KK.Else)
            .ignore_then(block(stmt))
            .or_not()
            .map(lambda stmts: list[nodes.Statement]())  # TODO: testing only
        )
        .delimited_by(start=just(PK.LeftBrace), end=just(PK.RightBrace))
    )
    .map(
        lambda items: nodes.WhenStatement(
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


def split_stream(stream: TokenStream) -> list[tuple[int, int]]:
    nesting_level = 0
    delimiters = list[tuple[int, int]]()
    start = 0

    for idx, token in enumerate(stream.tokens):
        match token:
            case lexemes.Primitive(_, PK.LeftBrace):
                nesting_level += 1
            case lexemes.Primitive(_, PK.RightBrace):
                nesting_level -= 1
                if nesting_level == 0:
                    delimiters.append((start, idx))
                    start = idx
            case _:
                continue

    return delimiters


def parse(source: str) -> ...:
    tokens = lex.tokenize(source)

    stream = TokenStream(
        list(
            filter(
                lambda token: not (
                    isinstance(token, lexemes.Whitespace)
                    or isinstance(token, lexemes.Comment)
                ),
                tokens,
            )
        )
    )

    pairs = split_stream(stream)
    first = pairs[0]
    print(first)
    # print(
    #     source[
    #         stream.tokens[first[0]].span.start.absolute : stream.tokens[
    #             first[1]
    #         ].span.stop.absolute
    #     ]
    # )

    print(stream.tokens[first[1]])
    pprint(decls.parse(TokenStream(stream.tokens[first[0] : first[1] + 1])))
    # success = 0
    # for pair in pairs:
    #     result = decls.parse(TokenStream(stream.tokens[pair[0] : pair[1]]))
    #     if isinstance(result, Parse.Errors):
    #         pprint(result.errors)
    #         print(stream.tokens[result.errors[0][0] - 1])
    #         print()
    #     elif isinstance(result, Parse.Match):
    #         success += 1
    #         pprint(result.item)

    # # if success ==
