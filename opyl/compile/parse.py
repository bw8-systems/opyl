from dataclasses import dataclass
import typing as t

from . import nodes
from . import stream
from . import combinators as comb
from .combinators import parse
from .tokens import KeywordKind, PrimitiveKind, GroupingPair


@dataclass
class OpalParser(comb.BaseTokenParser):
    def constant_declaration(self) -> nodes.ConstDeclaration:
        # "const" Identifier ":" Type "=" Expression "\n"

        (((keyword, identifier), type), initializer), newline = parse(
            self.keyword[KeywordKind.Const]
            .and_also(self.identifier)
            .followed_by(self.primitive[PrimitiveKind.Colon])
            .and_also(self.type)
            .followed_by(self.primitive[PrimitiveKind.Equal])
            .and_also(self.expression)
            .and_also(self.primitive[PrimitiveKind.NewLine])
        )

        return nodes.ConstDeclaration(
            span=keyword.span + newline.span,
            name=identifier.name,
            type=type,
            initializer=initializer,
        )

    def variable_declaration(self) -> nodes.VarDeclaration:
        # "let" ("mut")? Identifier ":" Type "=" Expression "\n"

        (((((keyword, maybe_mut), identifier), type), initializer), newline) = parse(
            self.keyword[KeywordKind.Let]
            .and_also(self.one_or_none(self.keyword[KeywordKind.Mut]))
            .and_also(self.identifier)
            .followed_by(self.primitive[PrimitiveKind.Colon])
            .and_also(self.type)
            .followed_by(self.primitive[PrimitiveKind.Equal])
            .and_also(self.expression)
            .and_also(self.primitive[PrimitiveKind.NewLine])
        )

        return nodes.VarDeclaration(
            span=keyword.span + newline.span,
            maybe_mut=maybe_mut,
            name=identifier.name,
            type=type,
            initializer=initializer,
        )

    def struct_declaration(self) -> nodes.StructDeclaration:
        # "struct" Identifier GenericSpec? TraitBaseSpec? "{" ( Field "\n")* CallableDefinition* "}"

        (
            (((keyword, identifier), generic_specs), trait_bases),
            (_left_brace, right_brace, (fields, (functions, methods))),
        ) = parse(
            self.keyword[KeywordKind.Struct]
            .and_also(self.identifier)
            .and_also(self.generic_spec)
            .and_also(self.trait_bases)
            .and_also(
                this=self.between_pair(
                    pair=GroupingPair.Brace,
                    between=self.zero_or_more(
                        comb.Lift(self.field).followed_by(PrimitiveKind.NewLine)
                    ).and_also(
                        this=self.many_either(
                            left=self.function,
                            right=self.method,
                            filter=lambda item: t.cast(
                                t.TypeGuard[nodes.FunctionDeclaration],
                                isinstance(item, nodes.FunctionDeclaration),
                            ),
                        )
                    ),
                )
            )
        )

        return nodes.StructDeclaration(
            span=keyword.span + right_brace.span,
            name=identifier.name,
            generic_params=generic_specs,
            trait_impls=trait_bases,
            fields=fields,
            methods=methods,
            functions=functions,
        )

    def union_declaration(self) -> nodes.UnionDeclaration:
        # "union" Identifier GenericSpec? TraitBaseSpec? "=" Type ("|" Type)+ ("{" CallableDefinition* "}")?

        keyword = parse(self.keyword[KeywordKind.Union])
        identifier = parse(self.identifier)

        generic_specs = parse(self.generic_spec)
        trait_bases = parse(self.trait_bases)

        parse(self.primitive[PrimitiveKind.Equal])

        members = [parse(self.type)]
        members.extend(
            parse(self.one_or_more(self.primitive[PrimitiveKind.Pipe].then(self.type)))
        )

        span = keyword.span + members[-1].span

        functions = list[nodes.FunctionDeclaration]()
        methods = list[nodes.MethodDeclaration]()

        maybe_functions_and_methods = parse(
            self.one_or_none(
                self.between_pair(
                    pair=GroupingPair.Brace,
                    between=self.many_either(
                        left=self.function,
                        right=self.method,
                        filter=lambda item: t.cast(
                            t.TypeGuard[nodes.FunctionDeclaration],
                            isinstance(item, nodes.FunctionDeclaration),
                        ),
                    ),
                )
            )
        )

        if maybe_functions_and_methods is not None:
            (
                _left_brace,
                right_brace,
                functions_and_methods,
            ) = maybe_functions_and_methods
            functions, methods = functions_and_methods
            span += right_brace.span

        return nodes.UnionDeclaration(
            span=span,
            name=identifier.name,
            members=members,
            generic_params=generic_specs,
            trait_impls=trait_bases,
            methods=methods,
            functions=functions,
        )

    def enum_declaration(self) -> nodes.EnumDeclaration:
        # "enum" Identifier "{" Identifier ("," Identifier)* "}"
        keyword = parse(self.keyword[KeywordKind.Enum])
        identifier = parse(self.identifier)

        members = [parse(self.primitive[PrimitiveKind.LeftBrace].then(self.identifier))]
        members.extend(
            parse(
                self.zero_or_more(
                    self.primitive[PrimitiveKind.Comma].then(self.identifier)
                )
            )
        )

        right_brace = parse(self.primitive[PrimitiveKind.RightBrace])

        return nodes.EnumDeclaration(
            span=keyword.span + right_brace.span,
            identifier=identifier.name,
            members=[member.name for member in members],
        )

    def trait_declaration(self) -> nodes.TraitDeclaration:
        # "trait" Identifier GenericSpec? TraitBaseSpec? "{" CallableSignature+ "}"
        # keyword = parse(self.keyword[KeywordKind.Trait])
        # identifier = parse(self.identifier)
        # generic_specs = parse(self.generic_spec_parser)
        # trait_bases = parse(self.trait_bases_parser)

        ...

    def expression(self) -> nodes.Expression:
        ...

    def type(self) -> nodes.Type:
        ...

    def trait_bases(self) -> list[str]:
        ...

    def generic_spec(self) -> nodes.GenericParamSpec:
        ...

    def function(self) -> nodes.FunctionDeclaration:
        ...

    def method(self) -> nodes.MethodDeclaration:
        ...

    def field(self) -> nodes.Field:
        ...

    def statement(self) -> nodes.Statement:
        ...

    def paramspec(self) -> nodes.ParamSpec:
        # NOTE: that "mut type" is part of the type not the paramspec. So this
        # parser does not check for "mut". The type parser should do that.
        # Syntax:
        # anon name: type,
        anon = parse(self.one_or_none(self.keyword[KeywordKind.Anon]))
        identifier = self.identifier()
        parse(self.primitive[PrimitiveKind.Colon])
        param_type = self.type()
        comma = parse(self.primitive[PrimitiveKind.Comma])

        if anon is not None:
            start_span = anon.span
        else:
            start_span = identifier.span

        return nodes.ParamSpec(
            span=start_span + comma.span,
            is_anon=bool(anon),
            field=nodes.Field(
                span=stream.Span(
                    start=identifier.span.start, stop=param_type.span.stop
                ),
                name=identifier.name,
                type=param_type,
            ),
        )

    def generic_paramspec(self) -> nodes.GenericParamSpec:
        ...

    def function_signature(self) -> nodes.FunctionSignature:
        # def foo(anon name: mut type, ...) -> type
        keyword = parse(self.keyword[KeywordKind.Def])
        identifier = self.identifier()

        _left, right, params = parse(
            self.between(
                open=self.primitive[PrimitiveKind.LeftParenthesis],
                close=self.primitive[PrimitiveKind.RightParenthesis],
                between=self.zero_or_more(self.paramspec),
            )
        )

        return_type = None
        return_arrow = parse(self.one_or_none(self.primitive[PrimitiveKind.RightArrow]))

        # TODO: Type could be keyword or identifier
        if return_arrow is not None:
            return_type = self.identifier()

        if return_type is None:
            stop_span = right.span
        else:
            stop_span = return_type.span
            return_type = return_type.name

        return nodes.FunctionSignature(
            span=keyword.span + stop_span,
            name=identifier.name,
            params=params,
            return_type=return_type,
        )

    def method_signature(self) -> nodes.MethodSignature:
        ...

    # def function(self) -> nodes.FunctionDeclaration:
    #     signature = self.parse_function_signature()
    #     _opening, closing, body = parse(
    #         self.between_pair(
    #             pair=GroupingPair.Parenthesis,
    #             between=self.zero_or_more(self.parse_statement),
    #         )
    #     )

    #     return nodes.FunctionDeclaration(
    #         span=signature.span + closing.span,
    #         signature=signature,
    #         body=body,
    #     )

    # def parse_trait_declaration(self) -> nodes.TraitDeclaration:
    #     keyword = parse(self.keyword[KeywordKind.Trait])
    #     identifier = parse(comb.Whitespace(self.stream).then(self.identifier))

    #     generic_params = []
    #     if (
    #         parse(self.one_or_none(self.primitive[PrimitiveKind.LeftBracket]))
    #         is not None
    #     ):
    #         generic_params = parse(
    #             self.zero_or_more(
    #                 comb.Lift(self.parse_generic_paramspec).then(
    #                     self.primitive[PrimitiveKind.Comma]
    #                 )
    #             ).then(self.primitive[PrimitiveKind.RightBracket])
    #         )

    #     trait_bases = parse(
    #         self.one_or_none(self.primitive[PrimitiveKind.LeftParenthesis])
    #         .then(
    #             self.zero_or_more(
    #                 self.identifier.followed_by(self.primitive[PrimitiveKind.Comma])
    #             )
    #         )
    #         .followed_by(self.primitive[PrimitiveKind.RightParenthesis])
    #     )

    #     return nodes.TraitDeclaration(
    #         span=stream.Span(
    #             start=keyword.span.start, stop=stream.TextPosition.default()
    #         ),
    #         name=identifier.name,
    #         bases=trait_bases,
    #         generic_params=generic_params,
    #         methods=[],
    #         functions=[],
    #     )
