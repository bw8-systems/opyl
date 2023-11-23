import typing as t

from compile import lex
from compile import nodes
from compile import lexemes
from compile.positioning import Stream
from compile.lexemes import KeywordKind as KK
from compile.lexemes import PrimitiveKind as PK

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
            self.lift(self.const_decl)
            | self.var_decl
            | self.enum_decl
            | self.struct_decl
            | self.union_decl
            | self.trait_decl
            | self.function_decl
        )

    def statement(self) -> comb.Parser[nodes.Statement]:
        return (
            self.lift(self.const_decl)
            | self.var_decl
            | self.for_statement
            | self.while_statement
            | self.when_statement
            | self.if_statement
            | self.return_statement
            | self.continue_statement
            | self.break_statement
            | self.expression_statement
        )

    def const_decl(self) -> nodes.ConstDeclaration:
        # const NAME: Type = initializer\n

        parsed = (
            KK.Const
            & self.identifier() >> PK.Colon
            & self.type() >> PK.Equal
            & self.expression()
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
        # let [mut]? Name: Type = initializer\n

        parsed = (
            KK.Let
            & self.maybe(KK.Mut)
            & self.identifier() >> PK.Colon
            & self.type() >> PK.Equal
            & self.expression()
            & PK.NewLine
        ).parse()

        ((((keyword, maybe_mut), ident), tipe), initializer), newline = parsed

        return nodes.VarDeclaration(
            span=keyword.span + newline.span,
            is_mut=maybe_mut is not None,
            name=ident,
            type=tipe,
            initializer=initializer,
        )

    def struct_decl(self) -> nodes.StructDeclaration:
        # struct Name {
        #     [Field]\n*
        # }\n

        parsed = (
            KK.Struct
            & self.identifier() >> self.primitive(PK.LeftBrace).newlines()
            & self.field().list(PK.NewLine) >> PK.RightBrace
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
            & self.identifier() >> self.primitive(PK.LeftBrace).newlines()
            & self.identifier().list(self.primitive(PK.Comma).newlines())
            >> self.maybe(PK.Comma).newlines()
            >> PK.RightBrace
            & PK.NewLine
        ).parse()

        (
            ((keyword, ident), members),
            newline,
        ) = parsed

        return nodes.EnumDeclaration(
            span=keyword.span + newline.span,
            name=ident,
            members=members,
        )

    def union_decl(self) -> nodes.UnionDeclaration:
        # TODO: Unions should be required to have atleast two types.
        parsed = (
            KK.Union
            & self.identifier() >> PK.Equal
            & self.type().list(PK.Pipe)
            & self.maybe(self.block(self.function_decl))
            & PK.NewLine
        ).parse()

        (((keyword, ident), tipes), maybe_functions), newline = parsed

        functions = [] if maybe_functions is None else maybe_functions

        return nodes.UnionDeclaration(
            span=keyword.span + newline.span,
            name=ident,
            members=tipes,
            functions=functions,
        )

    def trait_decl(self) -> nodes.TraitDeclaration:
        parsed = (
            KK.Trait
            & self.identifier().newlines()
            & self.block(self.signature)
            & PK.NewLine
        ).parse()

        ((keyword, ident), signatures), newline = parsed

        return nodes.TraitDeclaration(
            span=keyword.span + newline.span,
            name=ident,
            functions=signatures,
        )

    def function_decl(self) -> nodes.FunctionDeclaration:
        parsed = (
            self.lift(self.signature).newlines()
            & self.block(self.statement())
            & PK.NewLine
        ).parse()

        (signature, statements), newline = parsed

        return nodes.FunctionDeclaration(
            span=signature.span + newline.span,
            name=signature.name,
            signature=signature,
            body=statements,
        )

    def expression_statement(self) -> nodes.Expression:
        return self.expression().parse()

    def if_statement(self) -> nodes.IfStatement:
        parsed = (
            KK.If
            & self.expression().newlines()
            & self.block(self.statement())
            & self.maybe(self.else_clause())
            & PK.NewLine
        ).parse()

        (((keyword, condition), if_statements), maybe_else_statements), newline = parsed

        if maybe_else_statements is None:
            else_statements = []
        else:
            else_statements = maybe_else_statements

        return nodes.IfStatement(
            span=keyword.span + newline.span,
            if_condition=condition,
            if_statements=if_statements,
            else_statements=else_statements,
        )

    def while_statement(self) -> nodes.WhileLoop:
        parsed = (
            KK.While
            & self.expression().newlines()
            & self.block(self.statement())
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
            & self.expression().newlines()
            & self.block(self.statement())
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
            KK.When
            & self.expression()
            & self.maybe(self.as_clause()).newlines() >> PK.LeftBrace
            & self.many(self.is_clause().after_newlines())
            & self.maybe(self.else_clause()).after_newlines()
            >> self.primitive(PK.RightBrace).after_newlines()
            & PK.NewLine
        ).parse()

        (
            (
                (((kw, expr), target), is_clauses),
                maybe_else,
            ),
            newline,
        ) = parsed

        else_statements = [] if maybe_else is None else maybe_else

        return nodes.WhenStatement(
            span=kw.span + newline.span,
            expression=expr,
            target=target,
            is_clauses=is_clauses,
            else_statements=else_statements,
        )

    def return_statement(self) -> nodes.ReturnStatement:
        (keyword, expr), newline = (
            self.keyword(KK.Return) & self.expression() & PK.NewLine
        ).parse()

        return nodes.ReturnStatement(span=keyword.span + newline.span, expression=expr)

    def continue_statement(self) -> nodes.ContinueStatement:
        keyword, newline = (self.keyword(KK.Continue) & PK.NewLine).parse()
        return nodes.ContinueStatement(span=keyword.span + newline.span)

    def break_statement(self) -> nodes.BreakStatement:
        keyword, newline = (self.keyword(KK.Break) & PK.NewLine).parse()
        return nodes.BreakStatement(span=keyword.span + newline.span)

    ##################
    # Helper Parsers
    ##################

    def keyword(self, kw: lexemes.KeywordKind) -> comb.KeywordTerminal:
        return comb.KeywordTerminal(self.tokens, kw)

    def identifier(self) -> comb.IdentifierTerminal:
        return comb.IdentifierTerminal(self.tokens)

    def primitive(self, kind: lexemes.PrimitiveKind) -> comb.PrimitiveTerminal:
        return comb.PrimitiveTerminal(self.tokens, kind)

    def integer(self) -> comb.IntegerLiteralTerminal:
        return comb.IntegerLiteralTerminal(self.tokens)

    def expression(self) -> comb.Parser[nodes.Expression]:
        return self.identifier() | self.integer()

    def block[U](
        self, parser: comb.Parser[U] | t.Callable[[], U]
    ) -> comb.Parser[list[U]]:
        match parser:
            case comb.Parser():
                lifted = parser
            case _:
                lifted = self.lift(parser)

        return (
            self.primitive(PK.LeftBrace)
            .newlines()
            .consume_before(self.many(lifted.newlines()))
            >> PK.RightBrace
        )

    def is_clause(self) -> comb.Parser[nodes.IsClause]:
        def is_clause_builder(
            parsed: tuple[
                tuple[tuple[lexemes.Keyword, nodes.Type], list[nodes.Statement]],
                lexemes.Primitive,
            ],
        ) -> nodes.IsClause:
            ((keyword, tipe), statements), newline = parsed
            return nodes.IsClause(
                span=keyword.span + newline.span,
                target=tipe,
                statements=statements,
            )

        return (
            KK.Is & self.type().newlines() & self.block(self.statement()) & PK.NewLine
        ).into(is_clause_builder)

    def as_clause(self) -> comb.Parser[nodes.Identifier]:
        return self.keyword(KK.As).consume_before(self.identifier())

    def else_clause(self) -> comb.Parser[list[nodes.Statement]]:
        return (
            self.keyword(KK.Else)
            .newlines()
            .consume_before(self.block(self.statement()))
        )

    def generic_specification(self) -> nodes.GenericParamSpec:
        ...

    def field(self) -> comb.Parser[nodes.Field]:
        def field_builder(parsed: tuple[nodes.Identifier, nodes.Type]):
            ident, tipe = parsed
            return nodes.Field(
                span=ident.span + tipe.span,
                name=ident,
                type=tipe,
            )

        return (self.identifier() >> PK.Colon & self.type()).into(field_builder)

    def type(self) -> comb.Parser[nodes.Type]:
        return self.identifier()

    def signature(self) -> nodes.FunctionSignature:
        parsed = (
            KK.Def
            & self.identifier() >> PK.LeftParenthesis
            & self.maybe(self.param_spec().list(PK.Comma))
            & PK.RightParenthesis
            & self.maybe(self.primitive(PK.RightArrow).consume_before(self.type()))
        ).parse()

        (
            (((keyword, ident), params), right_paren),
            maybe_return_type,
        ) = parsed

        if maybe_return_type is not None:
            return_type = maybe_return_type
            end = maybe_return_type
        else:
            return_type = None
            end = right_paren

        return nodes.FunctionSignature(
            span=keyword.span + end.span,
            name=ident,
            params=params if params is not None else [],
            return_type=return_type,
        )

    def param_spec(self) -> comb.Parser[nodes.ParamSpec]:
        def param_spec_builder(
            parsed: tuple[
                tuple[
                    tuple[lexemes.Keyword | None, nodes.Identifier],
                    lexemes.Keyword | None,
                ],
                nodes.Type,
            ],
        ):
            ((maybe_anon, ident), maybe_mut), tipe = parsed
            start = ident if maybe_anon is None else maybe_anon
            return nodes.ParamSpec(
                span=start.span + tipe.span,
                is_anon=maybe_anon is not None,
                ident=ident,
                is_mut=maybe_mut is not None,
                type=tipe,
            )

        return (
            self.maybe(KK.Anon)
            & self.identifier() >> PK.Colon
            & self.maybe(KK.Mut)
            & self.type()
        ).into(param_spec_builder)
