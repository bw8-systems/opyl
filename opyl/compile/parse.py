import typing as t
from dataclasses import dataclass

from compile import lex
from compile import nodes
from compile import lexemes
from compile.positioning import Stream, Span
from compile.lexemes import KeywordKind as KK
from compile.lexemes import PrimitiveKind as PK
from compile import pratt
from compile import combinators as comb


@dataclass
class Spanned[T]:
    span: Span
    item: T


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
        return comb.ListTwo(
            self.tokens,
            self.declaration().after_newlines(),
            separator=self.primitive(PK.NewLine).newlines(),
        ).parse()

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
            | self.for_loop()
            | self.while_loop()
            | self.expression_statement()
        )

    def loop_statement(self) -> comb.Parser[nodes.LoopStatement]:
        return self.statement() | self.continue_statement() | self.break_statement()

    def const_decl(self) -> comb.Parser[nodes.ConstDeclaration]:
        @dataclass
        class ConstItems:
            const: lexemes.Keyword
            ident: nodes.Identifier
            type: nodes.Type
            itor: nodes.Expression

        return (
            (
                self.keyword(KK.Const)
                & self.identifier() >> self.primitive(PK.Colon)
                & self.type() >> self.primitive(PK.Equal)
                & self.expression()
            )
            .into(lambda p: ConstItems(*p))
            .into(
                lambda p: nodes.ConstDeclaration(
                    span=p.const.span + p.itor.span,
                    name=p.ident,
                    type=p.type,
                    initializer=p.itor,
                )
            )
        )

    def var_decl(self) -> comb.Parser[nodes.VarDeclaration]:
        @dataclass
        class VarItems:
            let: lexemes.Keyword
            mut: lexemes.Keyword | None
            ident: nodes.Identifier
            type: nodes.Type
            expr: nodes.Expression

        return (
            (
                self.keyword(KK.Let)
                & self.maybe(self.keyword(KK.Mut))
                & self.identifier() >> self.primitive(PK.Colon)
                & self.type() >> self.primitive(PK.Equal)
                & self.expression()
            )
            .into(lambda p: VarItems(*p))
            .into(
                lambda p: nodes.VarDeclaration(
                    span=p.let.span + p.expr.span,
                    name=p.ident,
                    is_mut=bool(p.mut),
                    type=p.type,
                    initializer=p.expr,
                )
            )
        )

    def struct_decl(self) -> comb.Parser[nodes.StructDeclaration]:
        @dataclass
        class StructItems:
            struct: lexemes.Keyword
            ident: nodes.Identifier
            fields: list[nodes.Field]

        return (
            (
                self.keyword(KK.Struct)
                & self.identifier() >> self.primitive(PK.LeftBrace).newlines()
                & comb.ListTwo(
                    self.tokens, self.field(), separator=self.primitive(PK.NewLine)
                )
                >> self.primitive(PK.RightBrace)
            )
            .into(lambda p: StructItems(*p))
            .into(
                lambda p: nodes.StructDeclaration(
                    span=p.struct.span
                    + (
                        p.fields[-1].span if len(p.fields) else p.ident.span
                    ),  # TODO: Span is not correct when there are zero fields.
                    name=p.ident,
                    fields=p.fields,
                    functions=[],
                )
            )
        )

    def enum_decl(self) -> comb.Parser[nodes.EnumDeclaration]:
        @dataclass
        class EnumItems:
            enum: lexemes.Keyword
            ident: nodes.Identifier
            members: list[nodes.Identifier]

        return (
            (
                self.keyword(KK.Enum)
                & self.identifier() >> self.primitive(PK.LeftBrace).newlines()
                & self.list(
                    self.identifier(), separated_by=self.primitive(PK.Comma).newlines()
                )
                >> self.maybe(self.primitive(PK.Comma)).newlines()
                >> self.primitive(PK.RightBrace)
            )
            .into(lambda p: EnumItems(*p))
            .into(
                lambda p: nodes.EnumDeclaration(
                    span=p.enum.span + p.members[-1].span,
                    name=p.ident,
                    members=p.members,
                )
            )
        )

    def union_decl(self) -> comb.Parser[nodes.UnionDeclaration]:
        @dataclass
        class UnionItems:
            union: lexemes.Keyword
            ident: nodes.Identifier
            types: list[nodes.Type]
            functions: list[
                nodes.FunctionDeclaration
            ] | None  # TODO: "or_else" combinator for defaults

        # TODO: Unions should be required to have atleast two types.
        return (
            (
                self.keyword(KK.Union)
                & self.identifier() >> self.primitive(PK.Equal)
                & self.list(self.type(), separated_by=self.primitive(PK.Pipe))
                & self.if_then(
                    if_this=self.primitive(PK.LeftBrace),
                    then_require=self.list(
                        self.function_decl(), separated_by=self.primitive(PK.NewLine)
                    )
                    >> self.primitive(PK.RightBrace),
                )
            )
            .into(lambda p: UnionItems(*p))
            .into(
                lambda p: nodes.UnionDeclaration(
                    span=p.union.span
                    + (
                        p.types[-1].span
                        if p.functions is None
                        else p.functions[-1].span
                    ),
                    name=p.ident,
                    members=p.types,
                    functions=p.functions if p.functions is not None else [],
                )
            )
        )

    def trait_decl(self) -> comb.Parser[nodes.TraitDeclaration]:
        @dataclass
        class TraitItems:
            trait: lexemes.Keyword
            ident: nodes.Identifier
            sigs: Spanned[list[nodes.FunctionSignature]]

        return (
            (
                self.keyword(KK.Trait)
                & self.identifier().newlines()
                & self.block(self.signature)
            )
            .into(lambda p: TraitItems(*p))
            .into(
                lambda p: nodes.TraitDeclaration(
                    span=p.trait.span + p.sigs.span,
                    name=p.ident,
                    functions=p.sigs.item,
                )
            )
        )

    def function_decl(self) -> comb.Parser[nodes.FunctionDeclaration]:
        @dataclass
        class FunctionItems:
            sig: nodes.FunctionSignature
            body: Spanned[list[nodes.Statement]]

        return (
            (self.signature().newlines() & self.block(self.statement))
            .into(lambda p: FunctionItems(*p))
            .into(
                lambda p: nodes.FunctionDeclaration(
                    span=p.sig.span + p.body.span,
                    name=p.sig.name,
                    signature=p.sig,
                    body=p.body.item,
                )
            )
        )

    def expression_statement(self) -> comb.Parser[nodes.Expression]:
        return self.expression()

    def if_statement(self) -> comb.Parser[nodes.IfStatement]:
        @dataclass
        class IfItems:
            kw: lexemes.Keyword
            cond: nodes.Expression
            if_body: Spanned[list[nodes.Statement]]
            else_body: Spanned[
                list[nodes.Statement]
            ] | None  # TODO: "or_else" combinator for defaults

        return (
            (
                self.keyword(KK.If)
                & self.expression().newlines()
                & self.block(self.statement)
                & self.else_block()
            )
            .into(lambda p: IfItems(*p))
            .into(
                lambda p: nodes.IfStatement(
                    span=p.kw.span
                    + (p.else_body.span if p.else_body is not None else p.if_body.span),
                    if_condition=p.cond,
                    if_statements=p.if_body.item,
                    else_statements=p.else_body.item if p.else_body is not None else [],
                )
            )
        )

    def while_loop(self) -> comb.Parser[nodes.WhileLoop]:
        @dataclass
        class WhileItems:
            kw: lexemes.Keyword
            cond: nodes.Expression
            block: Spanned[list[nodes.LoopStatement]]

        return (
            (
                self.keyword(KK.While)
                & self.expression().newlines()
                & self.block(self.loop_statement)
            )
            .into(lambda p: WhileItems(*p))
            .into(
                lambda p: nodes.WhileLoop(
                    span=p.kw.span + p.block.span,
                    condition=p.cond,
                    statements=p.block.item,
                )
            )
        )

    def for_loop(self) -> comb.Parser[nodes.ForLoop]:
        @dataclass
        class ForItems:
            kw: lexemes.Keyword
            ident: nodes.Identifier
            expr: nodes.Expression
            body: Spanned[list[nodes.LoopStatement]]

        return (
            (
                self.keyword(KK.For)
                & self.identifier() >> self.keyword(KK.In)
                & self.expression().newlines()
                & self.block(self.loop_statement)
            )
            .into(lambda p: ForItems(*p))
            .into(
                lambda p: nodes.ForLoop(
                    span=p.kw.span + p.body.span,
                    target=p.ident,
                    iterator=p.expr,
                    statements=p.body.item,
                )
            )
        )

    def when_statement(self) -> comb.Parser[nodes.WhenStatement]:
        @dataclass
        class WhenItems:
            when: lexemes.Keyword
            expr: nodes.Expression
            bind: nodes.Identifier | None
            arms: list[nodes.IsClause]
            default: Spanned[list[nodes.Statement]] | None

        return (
            (
                self.keyword(KK.When)
                & self.expression()
                & self.as_binding().newlines() >> self.primitive(PK.LeftBrace)
                & self.list(self.is_arm(), separated_by=self.primitive(PK.NewLine))
                & self.else_block().after_newlines()
                >> self.primitive(PK.RightBrace).after_newlines()
            )
            .into(lambda p: WhenItems(*p))
            .into(
                lambda p: nodes.WhenStatement(
                    span=p.when.span + Span.default(),  # TODO: "end span" utils
                    expression=p.expr,
                    target=p.bind,
                    is_clauses=p.arms,
                    else_statements=p.default.item if p.default is not None else [],
                )
            )
        )

    def return_statement(self) -> comb.Parser[nodes.ReturnStatement]:
        return (self.keyword(KK.Return) & self.expression()).into(
            lambda p: nodes.ReturnStatement(span=p[0].span + p[1].span, expression=p[1])
        )

    def continue_statement(self) -> comb.Parser[nodes.ContinueStatement]:
        return self.keyword(KK.Continue).into(
            lambda p: nodes.ContinueStatement(span=p.span)
        )

    def break_statement(self) -> comb.Parser[nodes.BreakStatement]:
        return self.keyword(KK.Break).into(lambda p: nodes.BreakStatement(span=p.span))

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
    ) -> comb.Parser[Spanned[list[U]]]:
        return (
            self.primitive(PK.LeftBrace).newlines()
            & self.many(self.defer(parser_factory).newlines())
            & self.primitive(PK.RightBrace)
        ).into(lambda items: Spanned(span=items[0].span + items[2].span, item=items[1]))

    def is_arm(self) -> comb.Parser[nodes.IsClause]:
        @dataclass
        class IsItems:
            kw: lexemes.Keyword
            type: nodes.Type
            body: Spanned[list[nodes.Statement]]

        return (
            (self.keyword(KK.Is) & self.type().newlines() & self.block(self.statement))
            .into(lambda p: IsItems(*p))
            .into(
                lambda p: nodes.IsClause(
                    span=p.kw.span + (p.body.span if p.body else p.type.span),
                    target=p.type,
                    statements=p.body.item,
                )
            )
        )

    def as_binding(self) -> comb.IfThen[nodes.Identifier]:
        # TODO: Why isn't Parser[Identifier | None] valid?
        return self.if_then(if_this=self.keyword(KK.As), then_require=self.identifier())

    def else_block(self) -> comb.IfThen[Spanned[list[nodes.Statement]]]:
        return self.if_then(
            if_this=self.keyword(KK.Else),
            then_require=self.block(self.statement),
        )

    def field(self) -> comb.Parser[nodes.Field]:
        @dataclass
        class FieldItems:
            ident: nodes.Identifier
            type: nodes.Type

        return (
            (self.identifier() >> self.primitive(PK.Colon) & self.type())
            .into(lambda p: FieldItems(*p))
            .into(
                lambda p: nodes.Field(
                    span=p.ident.span + p.type.span,
                    name=p.ident,
                    type=p.type,
                )
            )
        )

    def type(self) -> comb.Parser[nodes.Type]:
        return self.identifier()

    def signature(self) -> comb.Parser[nodes.FunctionSignature]:
        @dataclass
        class SigItems:
            kw: lexemes.Keyword
            ident: nodes.Identifier
            maybe_params: list[nodes.ParamSpec]
            r_paren: lexemes.Primitive
            ret_type: nodes.Type | None

        return (
            (
                self.keyword(KK.Def)
                & self.identifier() >> self.primitive(PK.LeftParenthesis)
                & self.list(self.param_spec(), separated_by=self.primitive(PK.Comma))
                & self.primitive(PK.RightParenthesis)
                & self.if_then(
                    if_this=self.primitive(PK.RightArrow), then_require=self.type()
                )
            )
            .into(lambda p: SigItems(*p))
            .into(
                lambda p: nodes.FunctionSignature(
                    span=p.kw.span
                    + (p.ret_type if p.ret_type is not None else p.r_paren).span,
                    name=p.ident,
                    params=p.maybe_params,
                    return_type=p.ret_type,
                )
            )
        )

    def param_spec(self) -> comb.Parser[nodes.ParamSpec]:
        @dataclass
        class ParamSpecItems:
            maybe_anon: lexemes.Keyword | None
            ident: nodes.Identifier
            maybe_mut: lexemes.Keyword | None
            type: nodes.Type

        return (
            (
                self.maybe(self.keyword(KK.Anon))
                & self.identifier() >> self.primitive(PK.Colon)
                & self.maybe(self.keyword(KK.Mut))
                & self.type()
            )
            .into(lambda p: ParamSpecItems(*p))
            .into(
                lambda p: nodes.ParamSpec(
                    span=(p.ident if p.maybe_anon is None else p.maybe_anon).span
                    + p.type.span,
                    is_anon=bool(p.maybe_anon),
                    ident=p.ident,
                    is_mut=not bool(p.maybe_mut),
                    type=p.type,
                )
            )
        )
