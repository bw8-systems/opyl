import typing as t

from opyl.compile import ast
from opyl.compile.token import Token, Keyword, Basic, Identifier
from opyl.compile.error import ParseError
from opyl.compile.pratt import expr
from opyl.support.stream import Stream
from opyl.support.combinator import Parser, ParseResult, Nothing, OneOf, choice
from opyl.support.union import Maybe
from opyl.support.atoms import just, ident, newlines


class Statement(Parser[Token, ast.Statement, ParseError]):
    @t.override
    def parse(
        self, input: Stream[Token]
    ) -> ParseResult.Type[Token, ast.Statement, ParseError]:
        return (
            assign_stmt
            | return_stmt
            | if_stmt
            | for_loop
            | while_loop
            | when_stmt
            | let_decl
            | const_decl
            | expr
        ).parse(input)


def block[
    T
](these: Parser[Token, T, ParseError], label: str = "block") -> Parser[
    Token, list[T], ParseError
]:
    return newlines.ignore_then(
        lines(these).delimited_by(
            just(Basic.LeftBrace),
            just(Basic.RightBrace).require(ParseError(expected="}", following=label)),
        )
    )


def block_pair[
    T, U
](
    these: Parser[Token, T, ParseError],
    those: Parser[Token, U, ParseError],
    label: str = "block",
) -> Parser[Token, tuple[list[T], list[U]], ParseError]:
    return newlines.ignore_then(
        these.separated_by(newlines.at_least(1))
        .allow_leading()
        .allow_trailing()
        .then(those.separated_by(newlines.at_least(1)).allow_leading().allow_trailing())
    ).delimited_by(
        just(Basic.LeftBrace).require(
            ParseError(expected="{", following="start of block")
        ),  # TODO: Hacky hardcoded "following" text...
        just(Basic.RightBrace).require(ParseError(expected="'}'", following=label)),
    )


def lines[
    T
](parser: Parser[Token, T, ParseError]) -> Parser[Token, list[T], ParseError]:
    return newlines.ignore_then(
        parser.separated_by(newlines.at_least(1)).allow_leading().allow_trailing()
    )


def named_decl(keyword: Keyword) -> Parser[Token, Identifier, ParseError]:
    return just(keyword).ignore_then(
        ident.require(
            ParseError(expected="identifier", following=f"'{keyword.value}' keyword")
        )
    )


def kw_expr(keyword: Keyword) -> Parser[Token, ast.Expression, ParseError]:
    return just(keyword).ignore_then(
        expr.require(
            ParseError(expected="expression", following=f"'{keyword.value}' keyword")
        )
    )


one_of = OneOf[Token, ParseError]


builtin_type = choice(
    (
        just(Keyword.Bool).to(ast.BuiltInType.Bool),
        just(Keyword.Char).to(ast.BuiltInType.Char),
        just(Keyword.Str).to(ast.BuiltInType.Str),
        just(Keyword.U8).to(ast.BuiltInType.U8),
        just(Keyword.I8).to(ast.BuiltInType.I8),
        just(Keyword.U16).to(ast.BuiltInType.U16),
        just(Keyword.I16).to(ast.BuiltInType.I16),
        just(Keyword.U32).to(ast.BuiltInType.U32),
        just(Keyword.I32).to(ast.BuiltInType.I32),
    )
)

type = ident | builtin_type


field = ident.then(
    just(Basic.Colon).ignore_then(
        type.require(ParseError(expected="type", following="':'"))
    )
).map(lambda items: ast.Field(*items))

initializer = (
    just(Basic.Equal)
    .require(ParseError("=", "variable declaration"))
    .ignore_then(expr.require(ParseError(expected="expression", following="'='")))
)

const_decl = (
    just(Keyword.Const)
    .ignore_then(
        field.then(initializer).require(
            ParseError(expected="const declaration", following="'const' keyword")
        )
    )
    .map(
        lambda items: ast.ConstDeclaration(
            name=items[0].name,
            type=items[0].type,
            initializer=items[1],
        )
    )
)

let_decl = (
    just(Keyword.Let)
    .ignore_then(just(Keyword.Mut).boolean())
    .then(
        field.then(initializer).require(
            ParseError(expected="variable declaration", following="'let' keyword")
        )
    )
    .map(
        lambda items: ast.VarDeclaration(
            is_mut=items[0],
            name=items[1][0].name,
            type=Maybe.Just(items[1][0].type),
            initializer=items[1][1],
        )
    )
)

# TODO: Error handling: Identifier should not be required if `anon` wasn't
# present because in that case the identifier is the first token of the node.
param_spec = (
    just(Keyword.Anon)
    .boolean()
    .then(ident)
    .then_ignore(just(Basic.Colon))
    .then(just(Keyword.Mut).boolean())
    .then(type)
    .map(
        lambda items: ast.ParamSpec(
            is_anon=items[0][0][0],
            ident=items[0][0][1],
            is_mut=items[0][1],
            type=items[1],
        )
    )
)

param_list = (
    newlines.ignore_then(param_spec)
    .separated_by(just(Basic.Comma))
    .allow_trailing()
    .then_ignore(newlines)
    .delimited_by(just(Basic.LeftParenthesis), just(Basic.RightParenthesis))
)

func_sig = (
    named_decl(Keyword.Def)
    .then(
        param_list.require(
            ParseError("parameter specification list", "'def' keyword with identifier")
        )
    )
    .then(
        just(Basic.RightArrow)
        .ignore_then(ident.require(ParseError(expected="identifier", following="'->'")))
        .or_not()
    )
    .map(
        lambda items: ast.FunctionSignature(
            name=items[0][0],
            params=items[0][1],
            return_type=items[1],
        )
    )
)

stmt = Statement()

assign_operator = choice(
    (
        just(Basic.Equal).to(ast.AssignmentOperator.Equal),
        just(Basic.PlusEqual).to(ast.AssignmentOperator.Add),
        just(Basic.HyphenEqual).to(ast.AssignmentOperator.Subtract),
        just(Basic.AsteriskEqual).to(ast.AssignmentOperator.Multiply),
        just(Basic.ForwardSlashEqual).to(ast.AssignmentOperator.Divide),
    )
)

assign_stmt = expr.then(
    assign_operator.then(
        expr.require(ParseError(expected="expression", following="assignment operator"))
    )
).map(
    lambda items: ast.AssignStatement(
        target=items[0], operator=items[1][0], value=items[1][1]
    )
)

break_stmt = just(Keyword.Break).to(ast.BreakStatement())
continue_stmt = just(Keyword.Continue).to(ast.ContinueStatement())
return_stmt = (
    just(Keyword.Return)
    .ignore_then(expr.or_not())
    .map(lambda item: ast.ReturnStatement(expression=item))
)

func_decl = func_sig.then(block(stmt, "function definition")).map(
    lambda items: ast.FunctionDeclaration(
        name=items[0].name,
        signature=items[0],
        body=items[1],
    )
)

struct_decl = (
    named_decl(Keyword.Struct)
    .then(block_pair(field, func_decl, "struct definition"))
    .map(
        lambda items: ast.StructDeclaration(
            name=items[0],
            fields=items[1][0],
            functions=items[1][1],
        )
    )
)

enum_decl = (
    named_decl(Keyword.Enum)
    .then_ignore(just(Basic.NewLine).or_not())
    .then(
        newlines.ignore_then(ident)
        .separated_by(just(Basic.Comma).then(newlines))
        .allow_trailing()
        .delimited_by(
            start=just(Basic.LeftBrace),
            end=newlines.ignore_then(just(Basic.RightBrace)),
        )
    )
    .map(lambda items: ast.EnumDeclaration(name=items[0], members=items[1]))
)

type_def = (
    named_decl(Keyword.Type).then(
        just(Basic.Equal)
        .require(ParseError(expected="=", following="'type' with identifier"))
        .ignore_then(type.separated_by(just(Basic.Pipe)).at_least(1))
        .require(ParseError(expected="type alias", following="'type' keyword"))
    )
).map(lambda items: ast.TypeDefinition(*items))

trait_decl = (
    named_decl(Keyword.Trait)
    .then(block(func_sig, "trait definition"))
    .map(lambda items: ast.TraitDeclaration(*items))
)


else_block = just(Keyword.Else).ignore_then(block(stmt, "else block"))

if_stmt = (
    just(Keyword.If)
    .ignore_then(
        expr.require(ParseError(expected="expression", following="'if' keyword"))
    )
    .then(block(stmt).require(ParseError(expected="'{'", following="expression")))
    .then(else_block.or_else([]))
    .map(
        lambda items: ast.IfStatement(
            if_condition=items[0][0],
            if_statements=items[0][1],
            else_statements=items[1],
        )
    )
)

loop_stmt = stmt | break_stmt | continue_stmt

while_loop = (
    just(Keyword.While)
    .ignore_then(
        expr.require(ParseError(expected="expression", following="'while' keyword"))
    )
    .then(block(loop_stmt))
    .map(lambda items: ast.WhileLoop(*items))
)

for_loop = (
    named_decl(Keyword.For)
    .then_ignore(
        just(Keyword.In).require(ParseError(expected="'in'", following="identifier"))
    )
    .then(expr.require(ParseError(expected="expression", following="'in' keyword")))
    .then(block(loop_stmt))
    .map(
        lambda items: ast.ForLoop(
            target=items[0][0], iterator=items[0][1], statements=items[1]
        )
    )
)

is_arm = (
    just(Keyword.Is)
    .ignore_then(type.require(ParseError(expected="type", following="'is' keyword")))
    .then(block(stmt, "is arm"))
    .map(lambda items: ast.IsClause(*items))
)

# TODO: Parse `else` blocks in when statements.
when_stmt = (
    kw_expr(Keyword.When).then(
        just(Keyword.As)
        .ignore_then(
            ident.require(ParseError(expected="identifier", following="'as' keyword"))
        )
        .or_not()
        .then(block(is_arm))
    )
).map(lambda item: ast.WhenStatement(item[0], item[1][0], item[1][1], []))

eof = Nothing[Token, ParseError]()

decl = (
    enum_decl | struct_decl | const_decl | let_decl | func_decl | type_def | trait_decl
)

decls = (
    lines(decl)
    .then_ignore(eof)
    .require(ParseError(expected="end of input", following="declaration"))
)


def parse(
    stream: Stream[Token],
) -> ParseResult.Type[Token, list[ast.Declaration], ParseError]:
    """
    TODO: Actually do this vvvvvvvvvv
    In order to simplify error recovery while also maintaining error reporting ergononomics, the general approach to error
    recovery being taken here is, "don't," where the twist is that rather than parsing the entire token stream in one go,
    it'll instead be parsed incrementally so as to localize the spoil effect that syntax errors have on the entire output.

    In order to split the stream, the hueristic is to parse at top-level opening curly braces. With a single split like this,
    it means that one error may be reported per top-level declaration. This isn't an ideal solution since something such as a
    trait or struct declaration could have a quite large body, but it's an initial stab at a proof of concept.
    """

    # pairs = list[tuple[int, int]]()
    # current_start = 0
    # depth = 0
    # prev_depth = 0
    # for idx, spanned in enumerate(stream):
    #     if not isinstance(spanned.item, Basic):
    #         continue

    #     match spanned.item:
    #         case Basic.LeftBrace:
    #             depth += 1
    #         case Basic.RightBrace:
    #             depth -= 1
    #         case _:
    #             pass

    #     if (prev_depth != depth) and (depth == 0):
    #         pairs.append((current_start, idx))
    #         current_start = idx

    #     prev_depth = depth

    # for pair in pairs:
    #     if pair[1] == 106:
    #         spans = stream.spans[pair[0] :]
    #     else:
    #         spans = stream.spans[pair[0] : pair[1] + 1]
    #     substream = Stream(
    #         file_handle=stream.file_handle,
    #         spans=spans,
    #         position=stream.position,
    #     )
    #     parsed = decls.parse(substream)
    #     match parsed:
    #         case PR.Match(item, _):
    #             pprint(item)
    #         case PR.Error(err, span):
    #             report_parse_error(err, span, Foo)
    #         case PR.NoMatch:
    #             print("NO MATCH")
    # # p`print(stream)
    # # pprint(len(stre`am.spans))
    # print(pairs)
    # exit()
    return decls.parse(stream)
