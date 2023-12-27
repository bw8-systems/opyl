import typing as t

from opyl.compile.error import LexError
from opyl.compile.token import (
    IntegerLiteralBase,
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
)
from opyl.support.stream import Stream

just = Just[str, LexError]
filt = Filter[str, LexError]
one_of = OneOf[str, LexError]


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
    return (
        padded(just("_"), digs)
        .repeated()
        .at_least(1)
        .require(LexError.MalformedIntegerLiteral)
    )


def integer_mapper(base: int) -> t.Callable[[list[str]], IntegerLiteral]:
    literal_base = {
        2: IntegerLiteralBase.Binary,
        10: IntegerLiteralBase.Decimal,
        16: IntegerLiteralBase.Hexadecimal,
    }[base]

    return lambda chars: IntegerLiteral(
        int("".join(chars), base=base), base=literal_base
    )


bin_integer = startswith("0b").ignore_then(integer_digits(bin)).map(integer_mapper(2))

dec_integer = (
    dec.and_check(lambda char: char != "0").chain(padded(just("_"), dec).repeated())
).map(integer_mapper(10))

hex_integer = (startswith("0x").ignore_then(integer_digits(hex))).map(
    integer_mapper(16)
)

integer = (
    bin_integer
    | dec_integer
    | hex_integer
    | just("0")
    .map(lambda char: int(char, base=10))
    .map(lambda zero: IntegerLiteral(zero))
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
        just("+").to(Basic.Plus),
        just("-").ignore_then(just(">").to(Basic.RightArrow).or_else(Basic.Hyphen)),
        just("*").to(Basic.Asterisk),
        just("/").to(Basic.ForwardSlash),
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

strip = (whitespace | comment).repeated().or_not()

# TODO: Update identifier / keyword parsers so that this isn't
# position dependent.
token = integer | keyword | identifier | basic | string | character

tokenizer = strip.ignore_then(token.spanned()).repeated()


def tokenize(
    source: str, file_handle: str | None = None
) -> ParseResult.Type[str, Stream[Token], LexError]:
    match tokenizer.parse(Stream.from_source(source, file_handle)):
        case PR.Match(toks, rem):
            return PR.Match(Stream(file_handle, toks), rem)
        case PR.NoMatch:
            return PR.NoMatch
        case PR.Error() as error:
            return error
