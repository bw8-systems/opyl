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
        return self.many(self.many(PK.NewLine).consume_before(self.decl)).parse()

    def keyword(self, kw: lexemes.KeywordKind) -> comb.KeywordTerminal:
        return comb.KeywordTerminal(self.tokens, kw)

    def identifier(self) -> comb.IdentifierTerminal:
        return comb.IdentifierTerminal(self.tokens)

    def primitive(self, kind: lexemes.PrimitiveKind) -> comb.PrimitiveTerminal:
        return comb.PrimitiveTerminal(self.tokens, kind)

    def integer(self) -> comb.IntegerLiteralTerminal:
        return comb.IntegerLiteralTerminal(self.tokens)

    def decl(self) -> nodes.Declaration:
        return (
            self.lift(self.const_decl)
            | self.var_decl
            | self.enum_decl
            | self.struct_decl
            | self.union_decl
            | self.trait_decl
            | self.function_decl
        ).parse()

    def const_decl(self) -> nodes.ConstDeclaration:
        # const NAME: Type = initializer\n

        parsed = (
            KK.Const
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
        # let [mut]? Name: Type = initializer\n

        parsed = (
            KK.Let
            & self.maybe(KK.Mut)
            & self.identifier() >> PK.Colon
            & self.lift(self.type) >> PK.Equal
            & self.lift(self.expression)
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
            & self.field
            & self.many(self.lift(self.field).after_newlines()) >> PK.RightBrace
            & PK.NewLine
        ).parse()

        (((keyword, ident), field), fields), newline = parsed

        return nodes.StructDeclaration(
            span=keyword.span + newline.span,
            name=ident,
            fields=[field, *fields],
            functions=[],  # TODO: parse functions AND methods
        )

    def enum_decl(self) -> nodes.EnumDeclaration:
        # enum Name {
        #     [Identifier],\n*
        # }\n

        parsed = (
            KK.Enum
            & self.identifier() >> self.primitive(PK.LeftBrace).newlines()
            & self.identifier()
            & self.many(
                self.primitive(PK.Comma)
                .consume_before(self.many(PK.NewLine))
                .consume_before(self.identifier().newlines())
            )
            >> self.maybe(PK.Comma).newlines()
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
            & self.maybe(
                self.primitive(PK.LeftBrace).consume_before(
                    self.many(self.lift(self.function_decl).after_newlines())
                )
                >> PK.RightBrace
            )
            & PK.NewLine
        ).parse()

        ((((keyword, ident), tipe), tipes), maybe_functions), newline = parsed

        functions = [] if maybe_functions is None else maybe_functions

        return nodes.UnionDeclaration(
            span=keyword.span + newline.span,
            name=ident,
            members=[tipe, *tipes],
            functions=functions,
        )

    def trait_decl(self) -> nodes.TraitDeclaration:
        parsed = (
            KK.Trait
            & self.identifier().newlines() >> self.primitive(PK.LeftBrace).newlines()
            & self.many(self.lift(self.signature) >> PK.NewLine) >> PK.RightBrace
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
            >> self.primitive(PK.LeftBrace).newlines()
            & self.many(self.lift(self.statement).newlines()) >> PK.RightBrace
            & PK.NewLine
        ).parse()

        (signature, statements), newline = parsed

        return nodes.FunctionDeclaration(
            span=signature.span + newline.span,
            name=signature.name,
            signature=signature,
            body=statements,
        )

    def field(self) -> nodes.Field:
        ident, tipe = (self.identifier() >> PK.Colon & self.type).parse()

        return nodes.Field(
            span=ident.span + tipe.span,
            name=ident,
            type=tipe,
        )

    def type(self) -> nodes.Type:
        return self.identifier().parse()

    def signature(self) -> nodes.FunctionSignature:
        parsed = (
            KK.Def
            & self.identifier() >> PK.LeftParenthesis
            & self.maybe(self.param_spec)
            & self.many(self.primitive(PK.Comma).consume_before(self.param_spec))
            & PK.RightParenthesis
            & self.maybe(self.primitive(PK.RightAngle).consume_before(self.type))
        ).parse()

        (
            ((((keyword, ident), maybe_param), params), right_paren),
            maybe_return_type,
        ) = parsed

        if maybe_return_type is not None:
            return_type = maybe_return_type
            end = maybe_return_type
        else:
            return_type = None
            end = right_paren

        if maybe_param is not None:
            params.insert(0, maybe_param)

        return nodes.FunctionSignature(
            span=keyword.span + end.span,
            name=ident,
            params=params,
            return_type=return_type,
        )

    def param_spec(self) -> nodes.ParamSpec:
        parsed = (
            self.maybe(KK.Anon)
            & self.identifier() >> PK.Colon
            & self.maybe(KK.Mut)
            & self.type
        ).parse()

        ((maybe_anon, ident), maybe_mut), tipe = parsed

        start = ident if maybe_anon is None else maybe_anon

        return nodes.ParamSpec(
            span=start.span + tipe.span,
            is_anon=maybe_anon is not None,
            ident=ident,
            is_mut=maybe_mut is not None,
            type=tipe,
        )

    def statement(self) -> nodes.Statement:
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
            | self.expression
        ).parse()

    def expression(self) -> nodes.Expression:
        return (self.identifier() | self.integer()).parse()

    def generic_specification(self) -> nodes.GenericParamSpec:
        ...

    def if_statement(self) -> nodes.IfStatement:
        parsed = (
            KK.If
            & self.lift(self.expression).newlines()
            >> self.primitive(PK.LeftBrace).newlines()
            & self.many(self.lift(self.statement).after_newlines())
            >> self.many(PK.NewLine)
            >> PK.RightBrace
            & self.maybe(self.else_clause)
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
            & self.lift(self.expression).newlines() >> PK.LeftBrace
            & self.many(self.lift(self.statement).after_newlines())
            >> self.primitive(PK.RightBrace).after_newlines()
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
            & self.lift(self.expression).newlines()
            >> self.primitive(PK.LeftBrace).newlines()
            & self.many(self.lift(self.statement).after_newlines()) >> PK.RightBrace
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
            & self.expression
            & self.maybe(self.as_clause).newlines() >> PK.LeftBrace
            & self.many(self.lift(self.is_clause).after_newlines())
            & self.maybe(self.else_clause).after_newlines()
            >> self.primitive(PK.RightBrace).after_newlines()
            & PK.NewLine
        ).parse()

        (
            (
                (((keyword, expr), maybe_target), is_clauses),
                maybe_else_statements,
            ),
            newline,
        ) = parsed

        else_statements = [] if maybe_else_statements is None else maybe_else_statements

        return nodes.WhenStatement(
            span=keyword.span + newline.span,
            expression=expr,
            target=maybe_target,
            is_clauses=is_clauses,
            else_statements=else_statements,
        )

    def is_clause(self) -> nodes.IsClause:
        parsed = (
            KK.Is
            & self.lift(self.type).newlines() >> PK.LeftBrace
            & self.many(self.lift(self.statement).after_newlines())
            >> self.primitive(PK.RightBrace).after_newlines()
            & PK.NewLine
        ).parse()

        ((keyword, tipe), statements), newline = parsed

        return nodes.IsClause(
            span=keyword.span + newline.span, target=tipe, statements=statements
        )

    def as_clause(self) -> nodes.Identifier:
        return self.keyword(KK.As).consume_before(self.identifier()).parse()

    def else_clause(self) -> list[nodes.Statement]:
        return (
            self.keyword(KK.Else)
            .newlines()
            .consume_before(PK.LeftBrace)
            .newlines()
            .consume_before(self.many(self.statement))
            .newlines()
            >> PK.RightBrace
        ).parse()

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
