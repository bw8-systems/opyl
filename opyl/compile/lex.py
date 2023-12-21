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
)
from opyl.support.stream import Stream


just = Just[str, LexError]
filt = Filter[str, LexError]
one_of = OneOf[str, LexError]

bin = one_of("01")
dec = one_of("0123456789")
hex = one_of("0123456789abcdefABCDEF")

bin_integer = (
    startswith("0b")
    .ignore_then(bin.repeated().at_least(1).require(LexError.MalformedIntegerLiteral))
    .map(lambda chars: "".join(chars))
    .map(lambda string: int(string, base=2))
).map(lambda integer: IntegerLiteral(integer, IntegerLiteralBase.Binary))

dec_integer = (
    dec.and_check(lambda char: char != "0")
    .chain(dec.repeated())
    .map(lambda chars: "".join(chars))
    .map(lambda string: int(string, base=10))
).map(lambda integer: IntegerLiteral(integer, IntegerLiteralBase.Decimal))

hex_integer = (
    startswith("0x")
    .ignore_then(hex.repeated().at_least(1).require(LexError.MalformedIntegerLiteral))
    .map(lambda chars: "".join(chars))
    .map(lambda string: int(string, base=16))
).map(lambda integer: IntegerLiteral(integer, IntegerLiteralBase.Hexadecimal))

integer = (
    bin_integer
    | dec_integer
    | hex_integer
    | Just("0")
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

# TODO: Update identifier / keyword parsers so that this isn't
# position dependent.
token = integer | keyword | identifier | basic | string | character

tokenizer = (whitespace | comment).repeated().or_not().ignore_then(token).repeated()


def tokenize(source: str) -> ParseResult.Type[str, Stream[Token], LexError]:
    match tokenizer.parse(Stream(list(source))):
        case PR.Match(toks, rem):
            return PR.Match(Stream(toks), rem)
        case PR.NoMatch:
            return PR.NoMatch
        case PR.Error(err):
            return PR.Error(err)
