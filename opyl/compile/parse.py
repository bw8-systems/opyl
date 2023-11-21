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
        return self.choice(
            self.const_decl,
            self.var_decl,
            self.enum_decl,
            self.struct_decl,
            self.union_decl,
            self.trait_decl,
            self.function_decl,
        ).parse()

    def const_decl(self) -> nodes.ConstDeclaration:
        parsed = (
            self.keyword(KK.Const)
            & self.identifier() >> PK.Colon
            & self.lift(self.type) >> PK.Equal
            & self.expression
            & PK.NewLine
        ).parse()

        (((keyword, ident), tipe), initializer), newline = parsed

        return nodes.ConstDeclaration(
            span=keyword.span + newline.span,
            name=ident,
            type=tipe,
            initializer=initializer,
        )

    def var_decl(self) -> nodes.VarDeclaration:
        parsed = (
            KK.Let
            & (self.keyword(KK.Mut) | self.empty())
            & self.identifier() >> PK.Colon
            & self.lift(self.type) >> PK.Equal
            & self.expression
            & PK.NewLine
        ).parse()

        (
            (((((keyword, maybe_mut), ident), tipe), initializer)),
            newline,
        ) = parsed

        return nodes.VarDeclaration(
            span=keyword.span + newline.span,
            is_mut=maybe_mut is not None,
            name=ident,
            type=tipe,
            initializer=initializer,
        )

    def struct_decl(self) -> nodes.StructDeclaration:
        parsed = (
            KK.Struct
            & self.identifier()
            & self.primitive(PK.LeftBrace).consume_before(self.many(self.field))
            >> PK.RightBrace
            & PK.NewLine
        ).parse()

        ((keyword, ident), fields), newline = parsed

        return nodes.StructDeclaration(
            span=keyword.span + newline.span,
            name=ident,
            fields=fields,
            functions=[],  # TODO: parse functions AND methods
        )

    def enum_decl(self) -> nodes.EnumDeclaration:
        parsed = (
            KK.Enum
            & self.identifier()
            & self.primitive(PK.LeftBrace).consume_before(self.identifier())
            & comb.Repeat(
                tokens=self.tokens,
                parser=self.primitive(PK.Comma).consume_before(self.identifier()),
            )
            >> PK.RightBrace
            & PK.NewLine
        ).parse()

        (
            (((keyword, ident), member), members),
            newline,
        ) = parsed

        return nodes.EnumDeclaration(
            span=keyword.span + newline.span,
            name=ident,
            members=[member, *members],
        )

    def union_decl(self) -> nodes.UnionDeclaration:
        parsed = (
            KK.Union
            & self.identifier() >> PK.Equal
            & self.type
            & self.many(self.primitive(PK.Pipe).consume_before(self.type))
            & PK.NewLine
        ).parse()

        (((keyword, ident), tipe), tipes), newline = parsed

        return nodes.UnionDeclaration(
            span=keyword.span + newline.span,
            name=ident,
            members=[tipe, *tipes],
        )

    def trait_decl(self) -> nodes.TraitDeclaration:
        parsed = (
            KK.Trait
            & self.identifier()
            & (
                self.primitive(PK.LeftBrace).consume_before(
                    self.many(self.signature) >> PK.NewLine
                )
                & PK.NewLine
            )
        ).parse()

        (keyword, ident), (signatures, newline) = parsed

        return nodes.TraitDeclaration(
            span=keyword.span + newline.span,
            name=ident,
            functions=signatures,
        )

    def function_decl(self) -> nodes.FunctionDeclaration:
        (signature, statements), newline = (
            self.signature
            & self.primitive(PK.LeftBrace).consume_before(self.many(self.statement))
            >> PK.RightBrace
            & PK.NewLine
        ).parse()

        return nodes.FunctionDeclaration(
            span=signature.span + newline.span,
            name=signature.name,
            signature=signature,
            body=statements,
        )

    def field(self) -> nodes.Field:
        (ident, tipe), newline = (
            self.identifier() >> PK.Colon & self.type & PK.NewLine
        ).parse()

        return nodes.Field(
            span=ident.span + newline.span,
            name=ident,
            type=tipe,
        )

    def type(self) -> nodes.Identifier:
        return self.identifier().parse()

    def signature(self) -> nodes.FunctionSignature:
        ...

    def statement(self) -> nodes.Statement:
        return self.choice(
            self.const_decl,
            self.var_decl,
            self.for_statement,
            self.while_statement,
            self.when_statement,
            self.if_statement,
            self.return_statement,
            self.continue_statement,
            self.break_statement,
        ).parse()

    def expression(self) -> nodes.Expression:
        return self.identifier().parse()

    def generic_specification(self) -> nodes.GenericParamSpec:
        ...

    def if_statement(self) -> nodes.IfStatement:
        parsed = (
            self.keyword(KK.If)
            & self.expression
            & self.primitive(PK.LeftBrace).consume_before(self.many(self.statement))
            >> PK.RightBrace
            & PK.NewLine
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
            & self.expression
            & self.primitive(PK.LeftBrace).consume_before(self.many(self.statement))
            >> PK.RightBrace
            & PK.NewLine
        ).parse()

        ((keyword, expression), statements), newline = parsed

        return nodes.WhileLoop(
            span=keyword.span + newline.span,
            condition=expression,
            statements=statements,
        )

    def for_statement(self) -> nodes.ForLoop:
        parsed = (
            KK.For
            & self.identifier() >> self.keyword(KK.In)
            & self.lift(self.expression) >> self.primitive(PK.LeftBrace)
            & self.many(self.statement) >> PK.RightBrace
            & PK.NewLine
        ).parse()

        (((keyword, target), iterator), statements), newline = parsed

        return nodes.ForLoop(
            span=keyword.span + newline.span,
            target=target,
            iterator=iterator,
            statements=statements,
        )

    def when_statement(self) -> nodes.WhenStatement:
        parsed = (
            self.keyword(KK.When)
            & self.lift(self.expression) >> self.primitive(PK.LeftBrace)
            & self.many(self.is_clause) >> PK.RightBrace
            & PK.NewLine
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
            KK.Is
            & self.lift(self.type) >> PK.LeftBrace
            & self.many(self.statement) >> PK.RightBrace
            & PK.NewLine
        ).parse()

        ((keyword, tipe), statements), newline = parsed

        return nodes.IsClause(
            span=keyword.span + newline.span, target=tipe, statements=statements
        )

    def return_statement(self) -> nodes.ReturnStatement:
        (keyword, expr), newline = (
            self.keyword(KK.Return) & self.expression & PK.NewLine
        ).parse()

        return nodes.ReturnStatement(span=keyword.span + newline.span, expression=expr)

    def continue_statement(self) -> nodes.ContinueStatement:
        keyword, newline = (self.keyword(KK.Continue) & PK.NewLine).parse()
        return nodes.ContinueStatement(span=keyword.span + newline.span)

    def break_statement(self) -> nodes.BreakStatement:
        keyword, newline = (self.keyword(KK.Break) & PK.NewLine).parse()
        return nodes.BreakStatement(span=keyword.span + newline.span)
