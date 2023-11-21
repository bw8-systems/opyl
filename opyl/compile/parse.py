import typing as t

from . import lex
from . import nodes
from . import lexemes
from .positioning import Stream
from .lexemes import KeywordKind as KK
from .lexemes import PrimitiveKind as PK

from . import combinators as comb


class OpalParser(comb.Parser[list[nodes.Declaration]]):
    def __init__(self, source: str):
        super().__init__(tokens=Stream(lex.tokenize(source)))

    def parse(self) -> list[nodes.Declaration]:
        ...

    def keyword(self, kw: lexemes.KeywordKind) -> comb.KeywordTerminal:
        return comb.KeywordTerminal(self.tokens, kw)

    def identifier(self) -> comb.IdentifierTerminal:
        return comb.IdentifierTerminal(self.tokens)

    def primitive(self, kind: lexemes.PrimitiveKind) -> comb.PrimitiveTerminal:
        return comb.PrimitiveTerminal(self.tokens, kind)

    def many[T](self, parser: t.Callable[[], T]) -> comb.Repeat[T]:
        return comb.Repeat(self.tokens, comb.Lift(self.tokens, parser))

    def decl(self) -> nodes.Declaration:
        return (
            self.lift(self.const_decl)
            | self.lift(self.var_decl)
            | self.lift(self.enum_decl)
            | self.lift(self.struct_decl)
            | self.lift(self.union_decl)
            | self.lift(self.trait_decl)
            | self.lift(self.function_decl)
        ).parse()

    def const_decl(self) -> nodes.ConstDeclaration:
        parsed = (
            self.keyword(KK.Const)
            & self.identifier().consume(self.primitive(PK.Colon))
            & self.lift(self.type).consume(self.primitive(PK.Equal))
            & self.lift(self.expression)
            & self.primitive(PK.NewLine)
        ).parse()

        (((keyword, ident), tipe), initializer), newline = parsed

        return nodes.ConstDeclaration(
            span=keyword.span + newline.span,
            name=nodes.Identifier(span=ident.span, name=ident.identifier),
            type=tipe,
            initializer=initializer,
        )

    def var_decl(self) -> nodes.VarDeclaration:
        parsed = (
            self.keyword(KK.Let)
            & (self.keyword(KK.Mut) | self.empty())
            & self.identifier().consume(self.primitive(PK.Colon))
            & self.lift(self.type).consume(self.primitive(PK.Equal))
            & self.lift(self.expression)
            & self.primitive(PK.NewLine)
        ).parse()

        (
            (((((keyword, maybe_mut), ident), tipe), initializer)),
            newline,
        ) = parsed

        return nodes.VarDeclaration(
            span=keyword.span + newline.span,
            is_mut=maybe_mut is not None,
            name=nodes.Identifier(span=ident.span, name=ident.identifier),
            type=tipe,
            initializer=initializer,
        )

    def struct_decl(self) -> nodes.StructDeclaration:
        parsed = (
            self.keyword(KK.Struct)
            & (self.identifier())
            & self.primitive(PK.LeftBrace)
            .consume_before(self.many(self.field))
            .consume(self.primitive(PK.RightBrace))
            & (self.primitive(PK.NewLine))
        ).parse()

        ((keyword, ident), fields), newline = parsed

        return nodes.StructDeclaration(
            span=keyword.span + newline.span,
            name=nodes.Identifier(span=ident.span, name=ident.identifier),
            fields=fields,
            functions=[],  # TODO: parse functions AND methods
        )

    def enum_decl(self) -> nodes.EnumDeclaration:
        parsed = (
            self.keyword(KK.Enum)
            & self.identifier()
            & self.primitive(PK.LeftBrace).consume_before(self.identifier())
            & comb.Repeat(
                tokens=self.tokens,
                parser=self.primitive(PK.Comma).consume_before(self.identifier()),
            ).consume(self.primitive(PK.RightBrace))
            & self.primitive(PK.NewLine)
        ).parse()

        (
            (((keyword, ident), member), members),
            newline,
        ) = parsed

        member_node = nodes.Identifier(span=member.span, name=member.identifier)
        members_nodes = [
            nodes.Identifier(span=ident.span, name=ident.identifier)
            for ident in members
        ]

        return nodes.EnumDeclaration(
            span=keyword.span + newline.span,
            name=nodes.Identifier(span=ident.span, name=ident.identifier),
            members=[member_node, *members_nodes],
        )

    def union_decl(self) -> nodes.UnionDeclaration:
        parsed = (
            self.keyword(KK.Union)
            & self.identifier().consume(self.primitive(PK.Equal))
            & self.lift(self.type)
            & self.many(
                lambda: t.cast(
                    comb.Ok[nodes.Type],
                    self.primitive(PK.Pipe)
                    .consume_before(self.lift(self.type))
                    .parse(),
                ).item
            )
            & self.primitive(PK.NewLine)
        ).parse()

        (((keyword, ident), tipe), tipes), newline = parsed

        return nodes.UnionDeclaration(
            span=keyword.span + newline.span,
            name=nodes.Identifier(span=ident.span, name=ident.identifier),
            members=[tipe, *tipes],
        )

    def trait_decl(self) -> nodes.TraitDeclaration:
        parsed = (
            self.keyword(KK.Trait)
            & self.identifier()
            & (
                self.primitive(PK.LeftBrace).consume_before(
                    self.many(self.signature).consume(self.primitive(PK.NewLine))
                )
                & (self.primitive(PK.NewLine))
            )
        ).parse()

        (keyword, ident), (signatures, newline) = parsed

        return nodes.TraitDeclaration(
            span=keyword.span + newline.span,
            name=nodes.Identifier(span=ident.span, name=ident.identifier),
            functions=signatures,
        )

    def function_decl(self) -> nodes.FunctionDeclaration:
        parsed = (
            self.lift(self.signature)
            & self.primitive(PK.LeftBrace)
            .consume_before(self.many(self.statement))
            .consume(self.primitive(PK.RightBrace))
            & self.primitive(PK.NewLine)
        ).parse()

        (signature, statements), newline = parsed

        return nodes.FunctionDeclaration(
            span=signature.span + newline.span,
            name=signature.name,
            signature=signature,
            body=statements,
        )

    def field(self) -> nodes.Field:
        parsed = (
            self.identifier().consume(self.primitive(PK.Colon))
            & self.lift(self.type)
            & self.primitive(PK.NewLine)
        ).parse()

        (ident, tipe), newline = parsed

        return nodes.Field(
            span=ident.span + newline.span,
            name=nodes.Identifier(span=ident.span, name=ident.identifier),
            type=tipe,
        )

    def type(self) -> nodes.Identifier:
        parsed = self.identifier().parse()
        return nodes.Identifier(span=parsed.span, name=parsed.identifier)

    def signature(self) -> nodes.FunctionSignature:
        ...

    def statement(self) -> nodes.Statement:
        return (
            self.lift(self.const_decl)
            | self.lift(self.var_decl)
            | self.lift(self.for_statement)
            | self.lift(self.while_statement)
            | self.lift(self.when_statement)
            | self.lift(self.if_statement)
            | self.lift(self.return_statement)
            | self.lift(self.continue_statement)
            | self.lift(self.break_statement)
        ).parse()

    def expression(self) -> nodes.Expression:
        parsed = self.identifier().parse()
        return nodes.Identifier(span=parsed.span, name=parsed.identifier)

    def generic_specification(self) -> nodes.GenericParamSpec:
        ...

    def if_statement(self) -> nodes.IfStatement:
        parsed = (
            self.keyword(KK.If)
            & self.lift(self.expression)
            & self.primitive(PK.LeftBrace)
            .consume_before(self.many(self.statement))
            .consume(self.primitive(PK.RightBrace))
            & self.primitive(PK.NewLine)
        ).parse()

        ((keyword, expression), statements), newline = parsed

        return nodes.IfStatement(
            span=keyword.span + newline.span,
            if_condition=expression,
            if_statements=statements,
            else_statements=[],
        )

    def while_statement(self) -> nodes.WhileLoop:
        parsed = (
            self.keyword(KK.While)
            & self.lift(self.expression)
            & self.primitive(PK.LeftBrace)
            .consume_before(self.many(self.statement))
            .consume(self.primitive(PK.RightBrace))
            & self.primitive(PK.NewLine)
        ).parse()

        ((keyword, expression), statements), newline = parsed

        return nodes.WhileLoop(
            span=keyword.span + newline.span,
            condition=expression,
            statements=statements,
        )

    def for_statement(self) -> nodes.ForLoop:
        parsed = (
            self.keyword(KK.For)
            & self.identifier()
            & self.keyword(KK.In).consume_before(self.lift(self.expression))
            & self.primitive(PK.LeftBrace)
            .consume_before(self.many(self.statement))
            .consume(self.primitive(PK.RightBrace))
            & self.primitive(PK.NewLine)
        ).parse()

        (((keyword, target), iterator), statements), newline = parsed

        return nodes.ForLoop(
            span=keyword.span + newline.span,
            target=nodes.Identifier(span=target.span, name=target.identifier),
            iterator=iterator,
            statements=statements,
        )

    def when_statement(self) -> nodes.WhenStatement:
        parsed = (
            self.keyword(KK.When)
            & self.lift(self.expression)
            & self.primitive(PK.LeftBrace)
            .consume_before(self.many(self.is_clause))
            .consume(self.primitive(PK.RightBrace))
            & self.primitive(PK.NewLine)
        ).parse()

        ((keyword, expression), clauses), newline = parsed

        return nodes.WhenStatement(
            span=keyword.span + newline.span,
            expression=expression,
            as_target=None,
            is_clauses=clauses,
        )

    def is_clause(self) -> nodes.IsClause:
        parsed = (
            self.keyword(KK.Is)
            & self.lift(self.type).consume(self.primitive(PK.LeftBrace))
            & self.many(self.statement).consume(self.primitive(PK.RightBrace))
            & self.primitive(PK.NewLine)
        ).parse()

        ((keyword, tipe), statements), newline = parsed

        return nodes.IsClause(
            span=keyword.span + newline.span, target=tipe, statements=statements
        )

    def return_statement(self) -> nodes.ReturnStatement:
        parsed = (
            self.keyword(KK.Return)
            & self.lift(self.expression)
            & self.primitive(PK.NewLine)
        ).parse()

        (keyword, expr), newline = parsed

        return nodes.ReturnStatement(span=keyword.span + newline.span, expression=expr)

    def continue_statement(self) -> nodes.ContinueStatement:
        parsed = (self.keyword(KK.Continue) & self.primitive(PK.NewLine)).parse()

        keyword, newline = parsed

        return nodes.ContinueStatement(span=keyword.span + newline.span)

    def break_statement(self) -> nodes.BreakStatement:
        parsed = (self.keyword(KK.Break) & self.primitive(PK.NewLine)).parse()

        keyword, newline = parsed

        return nodes.BreakStatement(span=keyword.span + newline.span)
