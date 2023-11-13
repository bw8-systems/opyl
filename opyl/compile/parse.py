from . import lex
from . import nodes
from . import lexemes
from . import combinators as comb
from .combinators import Parser
from .positioning import Stream, Span, TextPosition
from .lexemes import KeywordKind as KK
from .lexemes import PrimitiveKind as PK


class OpalParser(comb.Combinator[list[nodes.Declaration]]):
    def __init__(self, source: str):
        self.stream = Stream(lex.tokenize(source))

    def __call__(self) -> list[nodes.Declaration]:
        return self.many(self.decl).parse()

    def keyword(self, kw: lexemes.KeywordKind) -> comb.Combinator[lexemes.Keyword]:
        return comb.Keyword(self.stream, kw)

    def identifier(self) -> comb.Combinator[nodes.Identifier]:
        return comb.Identifier(self.stream)

    def maybe[T](self, parser: Parser[T]) -> comb.Combinator[T | None]:
        return comb.Maybe(self.stream, parser)

    def many[T](self, parser: Parser[T]) -> comb.Combinator[list[T]]:
        return comb.Many(self.stream, parser)

    def decl(self) -> nodes.Declaration:
        return comb.Choice(
            stream=self.stream,
            choices=(
                self.const_decl,
                self.var_decl,
                self.enum_decl,
                self.struct_decl,
                self.union_decl,
                self.trait_decl,
                self.function_decl,
            ),
        ).parse()

    def const_decl(self) -> nodes.ConstDeclaration:
        (((keyword, ident), tipe), initializer), newline = (
            self.keyword(KK.Const)
            .also(self.identifier())
            .consume(PK.Colon)
            .also(self.type())
            .consume(PK.Equal)
            .also(self.lift(self.expression))
            .also(self.primitive(PK.NewLine))
        ).parse()

        return nodes.ConstDeclaration(
            span=keyword.span + newline.span,
            name=ident,
            type=tipe,
            initializer=initializer,
        )

    def var_decl(self) -> nodes.VarDeclaration:
        (((((keyword, maybe_mut), ident), tipe), initializer)), newline = (
            self.keyword(KK.Let)
            .also(self.maybe(self.keyword(KK.Mut)))
            .also(self.identifier())
            .consume(PK.Colon)
            .also(self.type())
            .consume(PK.Equal)
            .also(self.lift(self.expression))
            .also(self.primitive(PK.NewLine))
        ).parse()

        return nodes.VarDeclaration(
            span=keyword.span + newline.span,
            is_mut=maybe_mut is not None,
            name=ident,
            type=tipe,
            initializer=initializer,
        )

    def struct_decl(self) -> nodes.StructDeclaration:
        ((keyword, ident), fields), newline = (
            self.keyword(KK.Struct)
            .also(self.identifier())
            .also(
                self.between(
                    start=self.primitive(PK.LeftBrace),
                    stop=self.primitive(PK.RightBrace),
                    between=self.many(self.field),
                )
            )
            .also(self.primitive(PK.NewLine))
        ).parse()

        return nodes.StructDeclaration(
            span=keyword.span + newline.span,
            name=ident,
            fields=fields,
        )

    def enum_decl(self) -> nodes.EnumDeclaration:
        (((keyword, ident), (member, members)), newline) = (
            self.keyword(KK.Enum)
            .also(self.identifier())
            .also(
                self.between(
                    start=self.primitive(PK.LeftBrace),
                    stop=self.primitive(PK.RightBrace),
                    between=self.identifier()
                    .consume(PK.Comma)
                    .also(self.many(self.identifier().consume(PK.Comma))),
                )
            )
            .also(self.primitive(PK.NewLine))
        ).parse()

        return nodes.EnumDeclaration(
            span=keyword.span + newline.span,
            identifier=ident,
            members=[member] + members,
        )

    def union_decl(self) -> nodes.UnionDeclaration:
        ((keyword, ident), (tipe, tipes)), newline = (
            self.keyword(KK.Union)
            .also(self.identifier())
            .consume(PK.Equal)
            .also(self.type().also(self.many(self.consume_then(PK.Pipe, self.type()))))
            .also(self.primitive(PK.NewLine))
            .parse()
        )

        return nodes.UnionDeclaration(
            span=keyword.span + newline.span,
            name=ident.name,
            members=[tipe] + tipes,
        )

    def trait_decl(self) -> nodes.TraitDeclaration:
        ((keyword, ident), signatures), newline = (
            self.keyword(KK.Trait)
            .also(self.identifier())
            .also(
                self.between(
                    start=self.primitive(PK.LeftBrace),
                    stop=self.primitive(PK.RightBrace),
                    between=self.many(self.lift(self.signature).consume(PK.NewLine)),
                )
            )
            .also(self.primitive(PK.NewLine))
            .parse()
        )

        return nodes.TraitDeclaration(
            span=keyword.span + newline.span,
            name=ident.name,
            functions=signatures,
        )

    def function_decl(self) -> nodes.FunctionDeclaration:
        (signature, statements), newline = (
            self.lift(self.signature)
            .also(
                self.between(
                    start=self.primitive(PK.LeftBrace),
                    stop=self.primitive(PK.RightBrace),
                    between=self.many(self.statement),
                )
            )
            .also(self.primitive(PK.NewLine))
        ).parse()

        return nodes.FunctionDeclaration(
            span=signature.span + newline.span,
            signature=signature,
            body=statements,
        )

    def field(self) -> nodes.Field:
        (ident, tipe), newline = (
            self.identifier()
            .consume(PK.Colon)
            .also(self.type())
            .also(self.primitive(PK.NewLine))
            .parse()
        )

        return nodes.Field(span=ident.span + newline.span, name=ident.name, type=tipe)

    def type(self) -> comb.Combinator[nodes.Type]:
        return self.identifier()

    def signature(self) -> nodes.FunctionSignature:
        ...

    def statement(self) -> nodes.Statement:
        return comb.Choice(
            stream=self.stream,
            choices=(
                self.for_statement,
                self.while_statement,
                self.if_statement,
                self.when_statement,
                self.return_statement,
                self.continue_statement,
                self.break_statement,
            ),
        ).parse()

    def expression(self) -> nodes.Expression:
        return self.identifier().parse()

    def generic_specification(self) -> comb.Combinator[nodes.GenericParamSpec]:
        # self.maybe(
        #     self.between(
        #         start=self.primitive(PK.LeftBrace),
        #         stop=self.primitive(PK.RightBrace),
        #         between=self.many(self.identifier().consume(PK.Comma)),
        #     )
        # ).parse()

        # return nodes.GenericParamSpec(
        #     span=
        # )
        ...

    def parent_traits(self) -> comb.Combinator[None]:
        ...

    def if_statement(self) -> nodes.IfStatement:
        ((keyword, expression), statements), newline = (
            self.keyword(KK.If)
            .also(self.lift(self.expression))
            .also(
                self.between(
                    start=self.primitive(PK.LeftBrace),
                    stop=self.primitive(PK.RightBrace),
                    between=self.many(self.statement),
                )
            )
            .also(self.primitive(PK.NewLine))
            .parse()
        )

        return nodes.IfStatement(
            span=keyword.span + newline.span,
            if_condition=expression,
            if_statements=statements,
            else_statements=[],
        )

    def while_statement(self) -> nodes.WhileLoop:
        ((keyword, expression), statements), newline = (
            self.keyword(KK.While)
            .also(self.lift(self.expression))
            .also(
                self.between(
                    start=self.primitive(PK.LeftBrace),
                    stop=self.primitive(PK.RightBrace),
                    between=self.many(self.statement),
                )
            )
            .also(self.primitive(PK.NewLine))
            .parse()
        )

        return nodes.WhileLoop(
            span=keyword.span + newline.span,
            condition=expression,
            statements=statements,
        )

    def for_statement(self) -> nodes.ForLoop:
        (((keyword, target), iterator), statements), newline = (
            self.keyword(KK.For)
            .also(self.identifier())
            .consume(KK.In)
            .also(self.lift(self.expression))
            .also(
                self.between(
                    start=self.primitive(PK.LeftBrace),
                    stop=self.primitive(PK.RightBrace),
                    between=self.many(self.statement),
                )
            )
            .also(self.primitive(PK.NewLine))
            .parse()
        )

        return nodes.ForLoop(
            span=keyword.span + newline.span,
            target=target,
            iterator=iterator,
            statements=statements,
        )

    def when_statement(self) -> nodes.WhenStatement:
        ((keyword, expression), clauses), newline = (
            self.keyword(KK.When)
            .also(self.lift(self.expression))
            .also(
                self.between(
                    start=self.primitive(PK.LeftBrace),
                    stop=self.primitive(PK.RightBrace),
                    between=self.many(self.is_clause),
                )
            )
            .also(self.primitive(PK.NewLine))
            .parse()
        )

        return nodes.WhenStatement(
            span=keyword.span + newline.span,
            expression=expression,
            as_target=None,
            is_clauses=clauses,
        )

    def is_clause(self) -> nodes.IsClause:
        ((keyword, tipe), statements), newline = (
            self.keyword(KK.As)
            .also(self.type())
            .also(
                self.between(
                    self.primitive(PK.LeftBrace),
                    self.primitive(PK.RightBrace),
                    between=self.many(self.statement),
                )
            )
            .also(self.primitive(PK.NewLine))
            .parse()
        )

        return nodes.IsClause(
            span=keyword.span + newline.span, pattern=tipe, statements=statements
        )

    def return_statement(self) -> nodes.ReturnStatement:
        (keyword, expr), newline = (
            self.keyword(KK.Return)
            .also(self.maybe(self.lift(self.expression)))
            .also(self.primitive(PK.NewLine))
            .parse()
        )

        return nodes.ReturnStatement(span=keyword.span + newline.span, expression=expr)

    def continue_statement(self) -> nodes.ContinueStatement:
        keyword, newline = (
            self.keyword(KK.Continue).also(self.primitive(PK.NewLine)).parse()
        )
        return nodes.ContinueStatement(span=keyword.span + newline.span)

    def break_statement(self) -> nodes.BreakStatement:
        keyword, newline = (
            self.keyword(KK.Break).also(self.primitive(PK.NewLine)).parse()
        )
        return nodes.BreakStatement(span=keyword.span + newline.span)
