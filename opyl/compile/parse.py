import typing as t

from compile import lex
from compile import nodes
from compile import lexemes
from compile.positioning import Stream
from compile.lexemes import KeywordKind as KK
from compile.lexemes import PrimitiveKind as PK
from compile import pratt
from compile import combinators as comb


class OpalParser(comb.Parser[list[nodes.Declaration]]):
    def __init__(self, source: str):
        tokens = list(
            filter(
                lambda token: not isinstance(token, lexemes.Whitespace),
                lex.tokenize(source),
            )
        )
        super().__init__(tokens=Stream(tokens))

    def parse(self) -> list[nodes.Declaration]:
        return self.many(self.declaration().after_newlines()).parse()

    def declaration(self) -> comb.Parser[nodes.Declaration]:
        return (
            self.const_decl()
            | self.var_decl()
            | self.enum_decl()
            | self.struct_decl()
            | self.union_decl()
            | self.trait_decl()
            | self.function_decl()
        )

    def statement(self) -> comb.Parser[nodes.Statement]:
        return (
            self.const_decl()
            | self.var_decl()
            | self.when_statement()
            | self.if_statement()
            | self.return_statement()
            | self.for_statement()
            | self.while_statement()
            | self.expression_statement()
        )

    def const_decl(self) -> comb.Parser[nodes.ConstDeclaration]:
        # const NAME: Type = initializer\n

        return (
            (
                self.keyword(KK.Const)
                & self.identifier() >> self.primitive(PK.Colon)
                & self.type() >> self.primitive(PK.Equal)
                & self.expression()
                & self.primitive(PK.NewLine)
            )
            .into(
                lambda parsed: t.NamedTuple(
                    "Parsed",
                    (
                        ("const", lexemes.Keyword),
                        ("ident", nodes.Identifier),
                        ("type", nodes.Type),
                        ("itor", nodes.Expression),
                        ("newline", lexemes.Primitive),
                    ),
                )(*parsed)
            )
            .into(
                lambda parsed: nodes.ConstDeclaration(
                    span=parsed.const.span + parsed.newline.span,
                    name=parsed.ident,
                    type=parsed.type,
                    initializer=parsed.itor,
                )
            )
        )

    def var_decl(self) -> comb.Parser[nodes.VarDeclaration]:
        # let [mut]? Name: Type = initializer\n

        return (
            (
                self.keyword(KK.Let)
                & self.maybe(self.keyword(KK.Mut))
                & self.identifier() >> self.primitive(PK.Colon)
                & self.type() >> self.primitive(PK.Equal)
                & self.expression()
                & self.primitive(PK.NewLine)
            )
            .into(
                lambda parsed: t.NamedTuple(
                    "Parsed",
                    (
                        ("let", lexemes.Keyword),
                        ("mut", lexemes.Keyword | None),
                        ("ident", nodes.Identifier),
                        ("type", nodes.Type),
                        ("expr", nodes.Expression),
                        ("newline", lexemes.Primitive),
                    ),
                )(*parsed)
            )
            .into(
                lambda parsed: nodes.VarDeclaration(
                    span=parsed.let.span + parsed.newline.span,
                    name=parsed.ident,
                    is_mut=bool(parsed.mut),
                    type=parsed.type,
                    initializer=parsed.expr,
                )
            )
        )

    def struct_decl(self) -> comb.Parser[nodes.StructDeclaration]:
        # struct Name {
        #     [Field]\n*
        # }\n

        return (
            (
                self.keyword(KK.Struct)
                & self.identifier() >> self.primitive(PK.LeftBrace).newlines()
                & self.list(self.field(), separated_by=self.primitive(PK.NewLine))
                >> self.primitive(PK.RightBrace)
                & self.primitive(PK.NewLine)
            )
            .into(
                lambda parsed: t.NamedTuple(
                    "Parsed",
                    (
                        ("kw", lexemes.Keyword),
                        ("ident", nodes.Identifier),
                        ("fields", list[nodes.Field]),
                        ("newline", lexemes.Primitive),
                    ),
                )(*parsed)
            )
            .into(
                lambda parsed: nodes.StructDeclaration(
                    span=parsed.kw.span + parsed.newline.span,
                    name=parsed.ident,
                    fields=parsed.fields,
                    functions=[],
                )
            )
        )

    def enum_decl(self) -> comb.Parser[nodes.EnumDeclaration]:
        return (
            (
                self.keyword(KK.Enum)
                & self.identifier() >> self.primitive(PK.LeftBrace).newlines()
                & self.list(
                    self.identifier(), separated_by=self.primitive(PK.Comma).newlines()
                )
                >> self.maybe(self.primitive(PK.Comma)).newlines()
                >> self.primitive(PK.RightBrace)
                & self.primitive(PK.NewLine)
            )
            .into(
                lambda parsed: t.NamedTuple(
                    "Parsed",
                    (
                        ("kw", lexemes.Keyword),
                        ("ident", nodes.Identifier),
                        ("members", list[nodes.Identifier]),
                        ("newline", lexemes.Primitive),
                    ),
                )(*parsed)
            )
            .into(
                lambda parsed: nodes.EnumDeclaration(
                    span=parsed.kw.span + parsed.newline.span,
                    name=parsed.ident,
                    members=parsed.members,
                )
            )
        )

    def union_decl(self) -> comb.Parser[nodes.UnionDeclaration]:
        # TODO: Unions should be required to have atleast two types.
        return (
            (
                self.keyword(KK.Union)
                & self.identifier() >> self.primitive(PK.Equal)
                & self.list(self.type(), separated_by=self.primitive(PK.Pipe))
                & self.maybe(self.block(self.function_decl))
                & self.primitive(PK.NewLine)
            )
            .into(
                lambda parsed: t.NamedTuple(
                    "Parsed",
                    (
                        ("kw", lexemes.Keyword),
                        ("ident", nodes.Identifier),
                        ("types", list[nodes.Type]),
                        ("functions", list[nodes.FunctionDeclaration] | None),
                        ("newline", lexemes.Primitive),
                    ),
                )(*parsed)
            )
            .into(
                lambda parsed: nodes.UnionDeclaration(
                    span=parsed.kw.span + parsed.newline.span,
                    name=parsed.ident,
                    members=parsed.types,
                    functions=parsed.functions if parsed.functions is not None else [],
                )
            )
        )

    def trait_decl(self) -> comb.Parser[nodes.TraitDeclaration]:
        return (
            (
                self.keyword(KK.Trait)
                & self.identifier().newlines()
                & self.block(self.signature)
                & self.primitive(PK.NewLine)
            )
            .into(
                lambda parsed: t.NamedTuple(
                    "Parsed",
                    (
                        ("kw", lexemes.Keyword),
                        ("ident", nodes.Identifier),
                        ("signatures", list[nodes.FunctionSignature]),
                        ("newline", lexemes.Primitive),
                    ),
                )(*parsed)
            )
            .into(
                lambda parsed: nodes.TraitDeclaration(
                    span=parsed.kw.span + parsed.newline.span,
                    name=parsed.ident,
                    functions=parsed.signatures,
                )
            )
        )

    def function_decl(self) -> comb.Parser[nodes.FunctionDeclaration]:
        return (
            (
                self.signature().newlines()
                & self.block(self.statement)
                & self.primitive(PK.NewLine)
            )
            .into(
                lambda parsed: t.NamedTuple(
                    "Parsed",
                    (
                        ("signature", nodes.FunctionSignature),
                        ("body", list[nodes.Statement]),
                        ("newline", lexemes.Primitive),
                    ),
                )(*parsed)
            )
            .into(
                lambda parsed: nodes.FunctionDeclaration(
                    span=parsed.signature.span + parsed.newline.span,
                    name=parsed.signature.name,
                    signature=parsed.signature,
                    body=parsed.body,
                )
            )
        )

    def expression_statement(self) -> comb.Parser[nodes.Expression]:
        return self.expression()

    def if_statement(self) -> comb.Parser[nodes.IfStatement]:
        # if expr { [statement]* } [else { [statement]* }]?

        return (
            (
                self.keyword(KK.If)
                & self.expression().newlines()
                & self.block(self.statement)
                & self.maybe(self.else_clause())
                & self.primitive(PK.NewLine)
            )
            .into(
                lambda parsed: t.NamedTuple(
                    "Parsed",
                    (
                        ("kw", lexemes.Keyword),
                        ("expr", nodes.Expression),
                        ("body", list[nodes.Statement]),
                        ("else_clause", list[nodes.Statement] | None),
                        ("newline", lexemes.Primitive),
                    ),
                )(*parsed)
            )
            .into(
                lambda parsed: nodes.IfStatement(
                    span=parsed.kw.span + parsed.newline.span,
                    if_condition=parsed.expr,
                    if_statements=parsed.body,
                    else_statements=parsed.else_clause
                    if parsed.else_clause is not None
                    else [],
                )
            )
        )

    def while_statement(self) -> comb.Parser[nodes.WhileLoop]:
        # while expr { [statement]* }

        return (
            (
                self.keyword(KK.While)
                & self.expression().newlines()
                & self.block(
                    self.statement
                )  # TODO: Update to allow break and continue statements. They have been removed from the base statement parser.
                & self.primitive(PK.NewLine)
            )
            .into(
                lambda parsed: t.NamedTuple(
                    "Parsed",
                    [
                        ("kw", lexemes.Keyword),
                        ("expr", nodes.Expression),
                        ("block", list[nodes.Statement]),
                        ("newline", lexemes.Primitive),
                    ],
                )(*parsed)
            )
            .into(
                lambda parsed: nodes.WhileLoop(
                    span=parsed.kw.span + parsed.newline.span,
                    condition=parsed.expr,
                    statements=parsed.block,
                )
            )
        )

    def for_statement(self) -> comb.Parser[nodes.ForLoop]:
        # for name in expr { [statement]* }

        return (
            (
                self.keyword(KK.For)
                & self.identifier() >> self.keyword(KK.In)
                & self.expression().newlines()
                & self.block(
                    self.statement
                )  # TODO: Update to allow break and continue statements. They have been removed from the base statement parser.
                & self.primitive(PK.NewLine)
            )
            .into(
                lambda parsed: t.NamedTuple(
                    "Parsed",
                    (
                        ("kw", lexemes.Keyword),
                        ("ident", nodes.Identifier),
                        ("expr", nodes.Expression),
                        ("body", list[nodes.Statement]),
                        ("newline", lexemes.Primitive),
                    ),
                )(*parsed)
            )
            .into(
                lambda parsed: nodes.ForLoop(
                    span=parsed.kw.span + parsed.newline.span,
                    target=parsed.ident,
                    iterator=parsed.expr,
                    statements=parsed.body,
                )
            )
        )

    def when_statement(self) -> comb.Parser[nodes.WhenStatement]:
        # when expr [as name]? {
        #     [is type { [statement]* }]*
        #     [else { [statement]* }]?
        # }

        return (
            (
                self.keyword(KK.When)
                & self.expression()
                & self.maybe(self.as_clause()).newlines()
                >> self.primitive(PK.LeftBrace)
                & self.many(self.is_clause().after_newlines())
                & self.maybe(self.else_clause()).after_newlines()
                >> self.primitive(PK.RightBrace).after_newlines()
                & self.primitive(PK.NewLine)
            )
            .into(
                lambda parsed: t.NamedTuple(
                    "Parsed",
                    (
                        ("when", lexemes.Keyword),
                        ("expr", nodes.Expression),
                        ("as_clause", nodes.Identifier | None),
                        ("is_clauses", list[nodes.IsClause]),
                        ("else_clause", list[nodes.Statement] | None),
                        ("newline", lexemes.Primitive),
                    ),
                )(*parsed)
            )
            .into(
                lambda parsed: nodes.WhenStatement(
                    span=parsed.when.span + parsed.newline.span,
                    expression=parsed.expr,
                    target=parsed.as_clause,
                    is_clauses=parsed.is_clauses,
                    else_statements=parsed.else_clause
                    if parsed.else_clause is not None
                    else [],
                )
            )
        )

    def return_statement(self) -> comb.Parser[nodes.ReturnStatement]:
        # return expr

        return (
            (self.keyword(KK.Return) & self.expression() & self.primitive(PK.NewLine))
            .into(
                lambda parsed: t.NamedTuple(
                    "Parsed",
                    (
                        ("kw", lexemes.Keyword),
                        ("expr", nodes.Expression),
                        ("newline", lexemes.Primitive),
                    ),
                )(*parsed)
            )
            .into(
                lambda parsed: nodes.ReturnStatement(
                    span=parsed.kw.span + parsed.newline.span, expression=parsed.expr
                )
            )
        )

    def continue_statement(self) -> comb.Parser[nodes.ContinueStatement]:
        # continue

        return (
            (self.keyword(KK.Continue) & self.primitive(PK.NewLine))
            .into(
                lambda parsed: t.NamedTuple(
                    "Parsed", (("kw", lexemes.Keyword), ("newline", lexemes.Primitive))
                )(*parsed)
            )
            .into(
                lambda parsed: nodes.ContinueStatement(
                    span=parsed.kw.span + parsed.newline.span,
                )
            )
        )

    def break_statement(self) -> comb.Parser[nodes.BreakStatement]:
        # break

        return (
            (self.keyword(KK.Break) & self.primitive(PK.NewLine))
            .into(
                lambda parsed: t.NamedTuple(
                    "Parsed", (("kw", lexemes.Keyword), ("newline", lexemes.Primitive))
                )(*parsed)
            )
            .into(
                lambda parsed: nodes.BreakStatement(
                    span=parsed.kw.span + parsed.newline.span
                )
            )
        )

    def keyword(self, kw: lexemes.KeywordKind) -> comb.KeywordTerminal:
        return comb.KeywordTerminal(self.tokens, kw)

    def identifier(self) -> comb.IdentifierTerminal:
        return comb.IdentifierTerminal(self.tokens)

    def primitive(self, kind: lexemes.PrimitiveKind) -> comb.PrimitiveTerminal:
        return comb.PrimitiveTerminal(self.tokens, kind)

    def integer(self) -> comb.IntegerLiteralTerminal:
        return comb.IntegerLiteralTerminal(self.tokens)

    def expression(self) -> comb.Parser[nodes.Expression]:
        return pratt.ExpressionParser(self.tokens)

    def block[U](
        self, parser_factory: t.Callable[[], comb.Parser[U]]
    ) -> comb.Parser[list[U]]:
        # { [items]* }

        return self.primitive(PK.LeftBrace).newlines().consume_before(
            self.many(self.defer(parser_factory).newlines())
        ) >> self.primitive(PK.RightBrace)

    def is_clause(self) -> comb.Parser[nodes.IsClause]:
        # is type { [statement]* }

        return (
            (
                self.keyword(KK.Is)
                & self.type().newlines()
                & self.block(self.statement)
                & self.primitive(PK.NewLine)
            )
            .into(
                lambda parsed: t.NamedTuple(
                    "Parsed",
                    (
                        ("kw", lexemes.Keyword),
                        ("type", nodes.Type),
                        ("statements", list[nodes.Statement]),
                        ("newline", lexemes.Primitive),
                    ),
                )(*parsed)
            )
            .into(
                lambda parsed: nodes.IsClause(
                    span=parsed.kw.span + parsed.newline.span,
                    target=parsed.type,
                    statements=parsed.statements,
                )
            )
        )

    def as_clause(self) -> comb.Parser[nodes.Identifier]:
        # as name

        return (
            (self.keyword(KK.As) & self.identifier())
            .into(
                lambda parsed: t.NamedTuple(
                    "Parsed", (("kw", lexemes.Keyword), ("ident", nodes.Identifier))
                )(*parsed)
            )
            .into(lambda parsed: parsed.ident)
        )

    def else_clause(self) -> comb.Parser[list[nodes.Statement]]:
        # else { [statement]* }

        return (
            self.keyword(KK.Else).newlines().consume_before(self.block(self.statement))
        )

    def generic_specification(self) -> nodes.GenericParamSpec:
        ...

    def field(self) -> comb.Parser[nodes.Field]:
        # name: type

        return (
            (self.identifier() >> self.primitive(PK.Colon) & self.type())
            .into(
                lambda parsed: t.NamedTuple(
                    "Parsed", (("ident", nodes.Identifier), ("type", nodes.Type))
                )(*parsed)
            )
            .into(
                lambda parsed: nodes.Field(
                    span=parsed.ident.span + parsed.type.span,
                    name=parsed.ident,
                    type=parsed.type,
                )
            )
        )

    def type(self) -> comb.Parser[nodes.Type]:
        return self.identifier()

    def signature(self) -> comb.Parser[nodes.FunctionSignature]:
        # def name([param_spec]*) -> type

        return (
            (
                self.keyword(KK.Def)
                & self.identifier() >> self.primitive(PK.LeftParenthesis)
                & self.maybe(
                    self.list(self.param_spec(), separated_by=self.primitive(PK.Comma))
                )
                & self.primitive(PK.RightParenthesis)
                & self.maybe(self.primitive(PK.RightArrow).consume_before(self.type()))
            )
            .into(
                lambda parsed: t.NamedTuple(
                    "Parsed",
                    (
                        ("kw", lexemes.Keyword),
                        ("ident", nodes.Identifier),
                        ("maybe_params", list[nodes.ParamSpec] | None),
                        ("r_paren", lexemes.Primitive),
                        ("ret_type", nodes.Type | None),
                    ),
                )(*parsed)
            )
            .into(
                lambda parsed: nodes.FunctionSignature(
                    span=parsed.kw.span
                    + (
                        parsed.ret_type
                        if parsed.ret_type is not None
                        else parsed.r_paren
                    ).span,
                    name=parsed.ident,
                    params=[] if parsed.maybe_params is None else parsed.maybe_params,
                    return_type=parsed.ret_type,
                )
            )
        )

    def param_spec(self) -> comb.Parser[nodes.ParamSpec]:
        # [anon]? name: [mut]? type

        return (
            (
                self.maybe(self.keyword(KK.Anon))
                & self.identifier() >> self.primitive(PK.Colon)
                & self.maybe(self.keyword(KK.Mut))
                & self.type()
            )
            .into(
                lambda parsed: t.NamedTuple(
                    "Parsed",
                    (
                        ("maybe_anon", lexemes.Keyword | None),
                        ("ident", nodes.Identifier),
                        ("maybe_mut", lexemes.Keyword | None),
                        ("type", nodes.Type),
                    ),
                )(*parsed)
            )
            .into(
                lambda parsed: nodes.ParamSpec(
                    span=(
                        parsed.ident if parsed.maybe_anon is None else parsed.maybe_anon
                    ).span
                    + parsed.type.span,
                    is_anon=bool(parsed.maybe_anon),
                    ident=parsed.ident,
                    is_mut=not bool(parsed.maybe_mut),
                    type=parsed.type,
                )
            )
        )
