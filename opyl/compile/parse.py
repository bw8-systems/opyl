import typing as t

from compile import lex
from compile import lexemes
from compile import nodes
from compile.lexemes import KeywordKind as KK
from compile.lexemes import PrimitiveKind as PK
from compile.combinators import (
    TokenStream,
    Parser,
    ParseResult,
    just,
    block,
    parens,
    lines,
    ident,
)

type = ident
expr = ident.map(lambda item: t.cast(nodes.Expression, item))

field = (
    ident.then_ignore(just(PK.Colon))
    .then(type)
    .map(lambda items: nodes.Field(name=items[0], type=items[1]))
)

const_decl = (
    just(KK.Const)
    .ignore_then(ident.expect("expected identifier after 'const'"))
    .then_ignore(just(PK.Colon).expect("expected ':' after identifier"))
    .then(type.expect("const declarations expect type after ':'"))
    .then(
        just(PK.Equal)
        .ignore_then(expr)
        .expect("const declaration requires initializer after type")
    )
    .map(
        lambda items: nodes.ConstDeclaration(
            name=items[0],
            type=items[1],
            initializer=items[2],
        )
    )
)

let_decl = (
    just(KK.Let)
    .ignore_then(just(KK.Mut).or_not().map(lambda mut: mut is not None))
    .then(ident.expect("expected identifier after 'let' keyword"))
    .then(just(PK.Colon).ignore_then(type).or_not())
    .then(
        just(PK.Equal)
        .ignore_then(expr)
        .expect("expected required initializer after variable declaration")
    )
    .map(
        lambda items: nodes.VarDeclaration(
            name=items[1],
            is_mut=items[0],
            type=items[2],
            initializer=items[3],
        )
    )
)

param_spec = (
    just(KK.Anon)
    .or_not()
    .map(lambda anon: anon is not None)
    .then(ident.expect("expected parameter name"))
    .then_ignore(just(PK.Colon))
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
    .ignore_then(ident)
    .then(parens(param_spec.separated_by(just(PK.Comma)).allow_trailing()))
    # .then(just(PK.RightArrow).ignore_then(type).or_not())  # TODO: Figure out "if then" optional parsing
    .map(
        lambda items: nodes.FunctionSignature(
            name=items[0],
            params=items[1],
            return_type=None,  # spanned.item[2],
        )
    )
)


class Statement(Parser[nodes.Statement]):
    @t.override
    def parse(self, input: TokenStream) -> ParseResult[nodes.Statement]:
        ...
        # return (
        #     return_stmt
        #     | if_stmt
        #     | for_loop
        #     | while_loop
        #     | when_stmt
        #     | let_decl
        #     | const_decl
        #     | expr
        # ).parse(input)


stmt = Statement()

break_stmt = just(KK.Break).map(lambda _: nodes.BreakStatement())
continue_stmt = just(KK.Continue).map(lambda _: nodes.ContinueStatement())
return_stmt = (
    just(KK.Return)
    .ignore_then(expr)
    .map(lambda item: nodes.ReturnStatement(expression=item))
)

func_decl = func_sig.then(block(lines(stmt))).map(
    lambda items: nodes.FunctionDeclaration(
        name=items[0].name,
        signature=items[0],
        body=items[1],
    )
)

struct_decl = (
    just(KK.Struct)
    .ignore_then(ident)
    .then(block(lines(field).at_least(1)))
    .map(
        lambda items: nodes.StructDeclaration(
            name=items[0],
            fields=items[1],
            functions=[],  # TODO
        )
    )
)

enum_decl = (
    just(KK.Enum)
    .ignore_then(ident)
    .then(block(ident.separated_by(just(PK.Comma)).allow_trailing().at_least(1)))
    .map(lambda items: nodes.EnumDeclaration(name=items[0], members=items[1]))
    .spanned()
)

union_decl = (
    just(KK.Union)
    .ignore_then(ident)
    .then_ignore(just(PK.Equal))
    .then(type.separated_by(just(PK.Pipe)).at_least(1))
    .then(block(lines(func_decl)).or_not().map(lambda _decls: []))
    .map(
        lambda items: nodes.UnionDeclaration(
            name=items[0],
            members=items[1],
            functions=[],  # spanned.item[2],  # TODO: wtf
        )
    )
)

trait_decl = (
    just(KK.Trait)
    .ignore_then(ident)
    .then(block(lines(func_decl)).or_not().map(lambda _decls: []))
    .map(lambda items: nodes.TraitDeclaration(*items))
)


if_stmt = (
    just(KK.If)
    .ignore_then(expr.expect("expected conditional expression after 'if' keyword"))
    .then(block(lines(stmt)).map(lambda _stmts: []))
    .then(just(KK.Else).or_not().ignore_then(block(lines(stmt)).map(lambda _stmts: [])))
    .map(lambda items: nodes.IfStatement(*items))
)

loop_stmt = stmt | break_stmt | continue_stmt

while_loop = (
    just(KK.While)
    .ignore_then(expr)
    .then(block(lines(loop_stmt)))
    .map(lambda items: nodes.WhileLoop(condition=items[0], statements=items[1]))
)

for_loop = (
    just(KK.For)
    .ignore_then(ident)
    .then_ignore(just(KK.In))
    .then(expr)
    .then(block(lines(loop_stmt)))
    .map(lambda items: nodes.ForLoop(*items))
)

is_arm = (
    just(KK.Is)
    .ignore_then(type)
    .then(block(lines(stmt)))
    .map(lambda items: nodes.IsClause(*items))
)

when_stmt = (  # Definitely needs closer look at the optional parts
    just(KK.When)
    .ignore_then(expr)
    .then(just(KK.As).ignore_then(ident).or_not())
    .then(
        block(
            is_arm.separated_by(just(PK.NewLine)).then(
                just(KK.Else)
                .ignore_then(block(lines(stmt)))
                .or_not()
                .map(lambda stmts: list[nodes.Statement]())  # TODO: testing only
            )
        )
    )
    .map(
        lambda items: nodes.WhenStatement(
            expression=items[0],
            target=items[1],
            is_clauses=items[2][0],
            else_statements=items[2][1],
        )
    )
)

decl = (
    (
        const_decl
        | let_decl
        | func_decl
        | struct_decl
        | enum_decl
        | union_decl
        | trait_decl
    )
    .expect(
        "expected top level declaration: const, let, func, struct, enum, union, trait"
    )
    .spanned()
    .separated_by(just(PK.NewLine))
    .allow_leading()
    .allow_trailing()
)


def parse(source: str):
    tokens = lex.tokenize(source)
    tokens = TokenStream(
        list(filter(lambda token: not isinstance(token, lexemes.Whitespace), tokens))
    )

    # pprint(tokens)
    # print(just(KK.Const))
    # print(tokens.tokens[0])
    result = let_decl(tokens)
    return result
