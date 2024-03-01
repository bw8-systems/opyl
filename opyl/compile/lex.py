import typing as t
from dataclasses import dataclass
import os

from opyl.compile.error import LexError
from opyl.compile.token import (
    Token,
    IntegerLiteral,
    Keyword,
    Basic,
    Identifier,
    StringLiteral,
    CharacterLiteral,
    Comment,
    Whitespace,
)
from opyl.support.combinator import (
    Filter,
    Just,
    ParseResult,
    PR,
    OneOf,
    choice,
    startswith,
    Parser,
    Nothing,
)
from opyl.support.stream import Stream
from opyl.support.span import Spanned


@dataclass
class LexResult[T]:
    stream: Stream[T]
    errors: list[ParseResult.Error[LexError]]


just = Just[str, LexError]
filt = Filter[str, LexError]
one_of = OneOf[str, LexError]
eof = Nothing[str, LexError]()

bin = one_of("01")
dec = one_of("0123456789")
hex = one_of("0123456789abcdefABCDEF")


def padded(
    padder: Parser[str, str, LexError], parser: Parser[str, str, LexError]
) -> Parser[str, str, LexError]:
    return padder.or_not().ignore_then(parser).then_ignore(padder.or_not())


def integer_digits(
    digs: Parser[str, str, LexError]
) -> Parser[str, list[str], LexError]:
    return padded(just("_"), digs).repeated().at_least(1)


def integer_mapper(
    base: t.Literal[2] | t.Literal[10] | t.Literal[16],
) -> t.Callable[[list[str]], IntegerLiteral]:
    return lambda chars: IntegerLiteral(int("".join(chars), base=base), base=base)


bin_integer = (
    startswith("0b")
    .ignore_then(integer_digits(bin).require(LexError.MalformedBinaryIntegerLiteral))
    .map(integer_mapper(2))
)

dec_integer = (
    dec.and_check(lambda char: char != "0").chain((padded(just("_"), dec).repeated()))
).map(integer_mapper(10))

hex_integer = (
    startswith("0x")
    .ignore_then(
        integer_digits(hex).require(LexError.MalformedHexadecimalIntegerLiteral)
    )
    .map(integer_mapper(16))
)

integer = (
    bin_integer
    | dec_integer
    | hex_integer
    | just("0").map(lambda char: IntegerLiteral(int(char, base=10)))
)

identifier = (
    filt(lambda char: char.isalpha() or char == "_")
    .chain(filt(lambda char: char.isalnum() or char == "_").repeated())
    .map(lambda chars: "".join(chars))
).map(Identifier)

keyword = identifier.and_check(lambda ident: ident.identifier in Keyword).map(
    lambda ident: Keyword(ident.identifier)
)

basic = choice(
    (
        just("+").ignore_then(just("=").to(Basic.PlusEqual).or_else(Basic.Plus)),
        just("-").ignore_then(
            (just(">").to(Basic.RightArrow) | just("=").to(Basic.HyphenEqual)).or_else(
                Basic.Hyphen
            )
        ),
        just("*").ignore_then(
            just("=").to(Basic.AsteriskEqual).or_else(Basic.Asterisk)
        ),
        just("/").ignore_then(
            just("=").to(Basic.ForwardSlashEqual).or_else(Basic.ForwardSlash)
        ),
        just("^").to(Basic.Caret),
        just("%").to(Basic.Percent),
        just("@").to(Basic.At),
        just("&").ignore_then(just("&").to(Basic.Ampersand2).or_else(Basic.Ampersand)),
        just("!").ignore_then(just("=").to(Basic.BangEqual).or_else(Basic.Bang)),
        just("~").to(Basic.Tilde),
        just(":").ignore_then(just(":").to(Basic.Colon2).or_else(Basic.Colon)),
        just("=").ignore_then(just("=").to(Basic.Equal2).or_else(Basic.Equal)),
        just("{").to(Basic.LeftBrace),
        just("}").to(Basic.RightBrace),
        just("(").to(Basic.LeftParenthesis),
        just(")").to(Basic.RightParenthesis),
        just("<").ignore_then(
            (
                just("<").to(Basic.LeftAngle2) | just("=").to(Basic.LeftAngleEqual)
            ).or_else(Basic.LeftAngle)
        ),
        just(">").ignore_then(
            (
                just(">").to(Basic.RightAngle2) | just("=").to(Basic.RightAngleEqual)
            ).or_else(Basic.RightAngle)
        ),
        just("[").to(Basic.LeftBracket),
        just("]").to(Basic.RightBracket),
        just(",").to(Basic.Comma),
        just(".").to(Basic.Period),
        just("|").ignore_then(just("|").to(Basic.Pipe2).or_else(Basic.Pipe)),
        just("\n").to(Basic.NewLine),
    )
)

string = (
    just('"')
    .ignore_then(filt(lambda char: char not in {"\n", '"'}).repeated())
    .then_ignore(just('"').require(LexError.UnterminatedStringLiteral))
    .map(lambda chars: "".join(chars))
).map(StringLiteral)

character = (
    just("'")
    .ignore_then(filt(lambda char: char != "'"))
    .then_ignore(just("'").require(LexError.UnterminatedCharacterLiteral))
).map(CharacterLiteral)

whitespace = just(" ").then(filt(str.isspace).repeated()).map(lambda _: Whitespace)

comment = (
    just("#")
    .ignore_then(filt(lambda char: char != "\n").repeated())
    .map(lambda chars: "".join(chars))
).map(Comment)

strip = whitespace.repeated().or_not()

# TODO: Update identifier / keyword parsers so that this isn't
# position dependent.
token = keyword | identifier | basic | string | character | integer

tokenizer = (
    strip.ignore_then((token | comment).spanned())
    .repeated()
    .then_ignore(eof)
    .require(LexError.UnexpectedCharacter)
)


def tokenize_with_comments(
    source: str,
    file_handle: os.PathLike[str] | None = None,
) -> LexResult[Token | Comment]:
    tokens = list[Spanned[Token | Comment]]()
    errors = list[ParseResult.Error[LexError]]()
    span_base = 0

    for line in source.splitlines():
        match tokenizer.parse(Stream.from_source(f"{line}\n", file_handle, span_base)):
            case PR.Match(toks, rem):
                tokens.extend(toks)
                # TODO: Don't assert.
                assert rem.position == (
                    len(line) + 1
                ), "Top level `require` should prevent stream from being incompletely consumed."
            case PR.NoMatch:
                # TODO: Don't assert.
                assert (
                    False
                ), "Top level `require` should prevent this from being reachable."
            case PR.Error() as error:
                errors.append(error)

        span_base += len(line) + 1

    return LexResult(
        stream=Stream(file_handle=file_handle, spans=tokens),
        errors=errors,
    )


def tokenize(
    source: str, file_handle: os.PathLike[str] | None = None
) -> LexResult[Token]:
    with_comments = tokenize_with_comments(source, file_handle)
    return LexResult(
        stream=filter_comments(with_comments.stream), errors=with_comments.errors
    )


def filter_comments(with_comments: Stream[Token | Comment]) -> Stream[Token]:
    def is_token(
        spanned: Spanned[Token | Comment],
    ) -> t.TypeGuard[Spanned[Token]]:
        return not isinstance(spanned.item, Comment)

    return Stream(
        file_handle=with_comments.file_handle,
        spans=list(filter(is_token, with_comments.spans)),
        position=with_comments.position,
    )
