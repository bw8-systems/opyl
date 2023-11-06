from dataclasses import dataclass
import typing as t


from . import lex
from . import tokens
from . import nodes
from . import stream
from . import combinators
from . import errors
from .tokens import KeywordKind, PrimitiveKind

type Parser[T] = t.Callable[[], T]


@dataclass
class BaseParser:
    stream: stream.Stream[tokens.Token]

    def one_or_none[T](self, parser: Parser[T]) -> combinators.Combinator[T | None]:
        return combinators.OneOrNone(self.stream, parser)

    def parse_one_or_none[T](self, parser: Parser[T]) -> T | None:
        return self.one_or_none(parser)()

    def one_or_more[T](self, parser: Parser[T]) -> combinators.Combinator[list[T]]:
        return combinators.OneOrMore(self.stream, parser)

    def parse_one_or_more[T](self, parser: Parser[T]) -> list[T]:
        return self.one_or_more(parser)()

    def zero_or_more[T](self, parser: Parser[T]) -> combinators.Combinator[list[T]]:
        return combinators.ZeroOrMore(self.stream, parser)

    def parse_zero_or_more[T](self, parser: Parser[T]) -> list[T]:
        zero_or_more = combinators.ZeroOrMore(self.stream, parser)
        return zero_or_more()

    def between[Open, Close, Between](
        self, open: Parser[Open], close: Parser[Close], between: Parser[Between]
    ) -> combinators.Combinator[tuple[Open, Close, Between]]:
        parser = combinators.Between(open=open, close=close, between=between)
        return parser

    def parse_between[Open, Close, Between](
        self, open: Parser[Open], close: Parser[Close], between: Parser[Between]
    ) -> tuple[Open, Close, Between]:
        parser = combinators.Between(open=open, close=close, between=between)
        return parser()

    def either[A, B](self, parser_a: Parser[A], parser_b: Parser[B]) -> A | B:
        a_or_none = self.parse_one_or_none(parser_a)
        if a_or_none is not None:
            return a_or_none

        return parser_b()

    def choice[T](self, *choices: Parser[T]) -> T:
        for choice in choices:
            item = self.parse_one_or_none(choice)
            if item is not None:
                return item

        raise errors.UnexpectedToken()


@dataclass
class TokenParser(BaseParser):
    def __post_init__(self):
        self.primitive = {
            kind: combinators.Primitive(self.stream, kind) for kind in PrimitiveKind
        }

        self.keyword = {
            kind: combinators.Keyword(self.stream, kind) for kind in KeywordKind
        }

        self.identifier_ = combinators.Identifier(self.stream)

    def parse_identifier(self) -> tokens.Identifier:
        return self.identifier_.parse()

    def identifier(self) -> tokens.Identifier:
        self.zero_or_more(self.whitespace)

        peeked = self.stream.peek()
        if peeked is None:
            raise errors.UnexpectedEOF()
        if isinstance(peeked, tokens.Identifier):
            self.stream.next()
            return peeked
        raise errors.UnexpectedToken()

    def integer(self) -> tokens.IntegerLiteral:
        self.zero_or_more(self.whitespace)

        peeked = self.stream.peek()
        if peeked is None:
            raise errors.UnexpectedEOF()
        if isinstance(peeked, tokens.IntegerLiteral):
            self.stream.next()
            return peeked
        raise errors.UnexpectedToken()

    def whitespace(self) -> tokens.Whitespace:
        peeked = self.stream.peek()
        if peeked is None:
            raise errors.UnexpectedEOF()
        if isinstance(peeked, tokens.Whitespace):
            self.stream.next()
            return peeked
        raise errors.UnexpectedToken()

    def space_then[T](self, parser: Parser[T]) -> T:
        self.whitespace()
        return parser()


@dataclass
class OpalParser(TokenParser):
    def parse_variable_declaration(self) -> nodes.VariableDeclaration:
        # let [mut] name: type = initializer newline

        keyword = self.keyword[KeywordKind.Let].parse()

        self.whitespace()

        mut_or_none = self.space_then(self.one_or_none(self.keyword[KeywordKind.Mut]))
        if mut_or_none is not None:
            self.whitespace()

        identifier = (
            combinators.Identifier(self.stream)
            .then(self.primitive[PrimitiveKind.Colon])
            .parse()
        )

        type_ = (
            combinators.ParserWrapper(self.parse_type)
            .then(self.primitive[PrimitiveKind.Equal])
            .parse()
        )

        itor = self.parse_expression()
        newline = self.primitive[PrimitiveKind.NewLine].parse()

        return nodes.VariableDeclaration(
            span=lex.Span(
                start=keyword.span.start,
                stop=newline.span.stop,
            ),
            mut=mut_or_none,
            name=identifier.identifier,
            type=type_.name,
            initializer=itor,
        )

    def parse_enum_declaration(self) -> nodes.EnumDeclaration:
        keyword = self.keyword[KeywordKind.Enum].parse()
        identifier = self.space_then(self.identifier)

        _opening, closing, members = self.parse_between(
            open=self.primitive[PrimitiveKind.LeftBrace],
            close=self.primitive[PrimitiveKind.RightBrace].then(
                self.primitive[PrimitiveKind.NewLine]
            ),
            between=self.one_or_more(
                self.primitive[PrimitiveKind.Comma].then_(self.identifier)
            ),
        )

        return nodes.EnumDeclaration(
            span=keyword.span + closing.span,
            identifier=identifier,
            members=members,
        )

    def parse_struct(self) -> nodes.Struct:
        ...

    def parse_type(self) -> nodes.Type:
        token = self.choice(
            self.keyword[KeywordKind.U8],
            self.keyword[KeywordKind.Char],
        )

        return nodes.Type(span=token.span, name=token.kind.value)

    def parse_statement(self) -> nodes.Statement:
        ...

    def parse_paramspec(self) -> nodes.ParamSpec:
        # NOTE: that "mut type" is part of the type not the paramspec. So this
        # parser does not check for "mut". The type parser should do that.
        # Syntax:
        # anon name: type,
        anon = self.parse_one_or_none(self.keyword[KeywordKind.Anon])
        identifier = self.identifier()
        self.primitive[PrimitiveKind.Colon].parse()
        param_type = self.parse_type()
        comma = self.primitive[PrimitiveKind.Comma].parse()

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
                name=identifier.identifier,
                type=param_type,
            ),
        )

    def parse_generic_paramspec(self) -> nodes.GenericParamSpec:
        ...

    def parse_function_signature(self) -> nodes.FunctionSignature:
        # def foo(anon name: mut type, ...) -> type
        keyword = self.keyword[KeywordKind.Def].parse()
        identifier = self.identifier()

        _left, right, params = self.parse_between(
            open=self.primitive[PrimitiveKind.LeftParenthesis],
            close=self.primitive[PrimitiveKind.RightParenthesis],
            between=self.zero_or_more(self.parse_paramspec),
        )

        return_type = None
        return_arrow = self.parse_one_or_none(self.primitive[PrimitiveKind.RightArrow])

        # TODO: Type could be keyword or identifier
        if return_arrow is not None:
            return_type = self.identifier()

        if return_type is None:
            stop_span = right.span
        else:
            stop_span = return_type.span
            return_type = return_type.identifier

        return nodes.FunctionSignature(
            span=keyword.span + stop_span,
            name=identifier.identifier,
            params=params,
            return_type=return_type,
        )

    def parse_method_signature(self) -> nodes.MethodSignature:
        ...

    def parse_function(self) -> nodes.Function:
        signature = self.parse_function_signature()
        _opening, closing, body = self.parse_between(
            open=self.primitive[PrimitiveKind.LeftParenthesis],
            close=self.primitive[PrimitiveKind.RightParenthesis],
            between=self.zero_or_more(self.parse_statement),
        )

        return nodes.Function(
            span=signature.span + closing.span,
            signature=signature,
            body=body,
        )

    def parse_trait_declaration(self) -> nodes.TraitDeclaration:
        keyword = self.keyword[KeywordKind.Trait].parse()
        identifier = combinators.Whitespace(self.stream).then_(self.identifier).parse()

        generic_params = []
        if (
            self.parse_one_or_none(self.primitive[PrimitiveKind.LeftBracket])
            is not None
        ):
            generic_params = (
                self.zero_or_more(
                    combinators.ParserWrapper(self.parse_generic_paramspec).then(
                        self.primitive[PrimitiveKind.Comma]
                    )
                )
                .then(self.primitive[PrimitiveKind.RightBracket])
                .parse()
            )

        trait_bases = (
            self.one_or_none(self.primitive[PrimitiveKind.LeftParenthesis])
            .then_(
                self.zero_or_more(
                    self.identifier_.then(self.primitive[PrimitiveKind.Comma])
                )
            )
            .then(self.primitive[PrimitiveKind.RightParenthesis])
        ).parse()

        return nodes.TraitDeclaration(
            span=stream.Span(
                start=keyword.span.start, stop=stream.TextPosition.default()
            ),
            name=identifier.identifier,
            bases=trait_bases,
            generic_params=generic_params,
            methods=[],
            functions=[],
        )

    def parse_expression(self) -> nodes.Expression:
        ...


def parse(tokens: list[tokens.Token]):
    ...
