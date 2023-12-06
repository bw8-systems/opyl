from compile import lex
from compile import lexemes
from compile import nodes
from compile.lexemes import KeywordKind as KK
from compile.lexemes import PrimitiveKind as PK
from compile.combinators import TokenStream, just, block, parens, lines, ident

type = ident
expr = ident

field = ident.then_ignore(just(PK.Colon)).then(type)

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
    .spanned()
    .map(
        lambda spanned: nodes.ConstDeclaration(
            span=spanned.span,
            name=spanned.item[0],
            type=spanned.item[1],
            initializer=spanned.item[2],
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
    .spanned()
    .map(
        lambda spanned: nodes.VarDeclaration(
            span=spanned.span,
            name=spanned.item[1],
            is_mut=spanned.item[0],
            type=spanned.item[2],
            initializer=spanned.item[3],
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
    .spanned()
    .map(
        lambda spanned: nodes.ParamSpec(
            span=spanned.span,
            is_anon=spanned.item[0][0],
            ident=spanned.item[0][1],
            is_mut=spanned.item[1][0],
            type=spanned.item[1][1],
        )
    )
)

func_sig = (
    just(KK.Def)
    .ignore_then(ident)
    .then(parens(param_spec.separated_by(just(PK.Comma)).allow_trailing()))
    # .then(just(PK.RightArrow).ignore_then(type).or_not())  # TODO: Figure out "if then" optional parsing
    .spanned()
    .map(
        lambda spanned: nodes.FunctionSignature(
            span=spanned.span,
            name=spanned.item[0],
            params=spanned.item[1],
            return_type=None,  # spanned.item[2],
        )
    )
)

stmt = ident
break_stmt = just(KK.Break)
continue_stmt = just(KK.Continue)
return_stmt = just(KK.Return).ignore_then(expr)

func_decl = func_sig.then(block(lines(stmt)))

struct_decl = just(KK.Struct).ignore_then(ident).then(block(lines(field).at_least(1)))

enum_decl = (
    just(KK.Enum)
    .ignore_then(ident)
    .then(block(ident.separated_by(just(PK.Comma)).allow_trailing().at_least(1)))
    .spanned()
    .map(
        lambda spanned: nodes.EnumDeclaration(
            span=spanned.span, name=spanned.item[0], members=spanned.item[1]
        )
    )
)

union_decl = (
    just(KK.Union)
    .ignore_then(ident)
    .then_ignore(just(PK.Equal))
    .then(type.separated_by(just(PK.Pipe)).at_least(1))
    .then(block(lines(func_decl)).or_not().map(lambda _decls: []))
    .spanned()
    .map(
        lambda spanned: nodes.UnionDeclaration(
            span=spanned.span,
            name=spanned.item[0],
            members=spanned.item[1],
            functions=[],  # spanned.item[2],  # TODO: wtf
        )
    )
)

trait_decl = just(KK.Trait).ignore_then(ident).then(block(lines(func_decl)).or_not())


if_stmt = (
    just(KK.If)
    .ignore_then(expr.expect("expected conditional expression after 'if' keyword"))
    .then(block(lines(stmt)).map(lambda _stmts: []))
    .then(just(KK.Else).or_not().ignore_then(block(lines(stmt)).map(lambda _stmts: [])))
    .spanned()
    .map(
        lambda spanned: nodes.IfStatement(
            span=spanned.span,
            if_condition=spanned.item[0],
            if_statements=spanned.item[1],
            else_statements=spanned.item[2],
        )
    )
)

loop_stmt = stmt | break_stmt | continue_stmt

while_loop = just(KK.While).ignore_then(expr).then(block(loop_stmt))

for_loop = (
    just(KK.For)
    .ignore_then(ident)
    .then_ignore(just(KK.In))
    .then(expr)
    .then(block(loop_stmt))
)

is_arm = just(KK.Is).then(type).then(block(stmt))
when_stmt = (  # Definitely needs closer look at the optional parts
    just(KK.When)
    .ignore_then(expr)
    .then(just(KK.As).ignore_then(ident).or_not())
    .then(
        block(
            is_arm.separated_by(just(PK.NewLine)).then(
                just(KK.Else).then(block(stmt)).or_not()
            )
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
