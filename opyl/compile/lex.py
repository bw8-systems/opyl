from compile.error import LexError
from compile.token import (
    IntegerLiteral,
    Keyword,
    Basic,
    Identifier,
    StringLiteral,
    CharacterLiteral,
    Comment,
    Whitespace,
)
from support.combinator import Filter, Just, filter, one_of


just = Just[str, LexError]
filt = Filter[str, LexError]

integer = (
    (
        filt(lambda char: str.isdigit(char) and char != "0")
        .chain(filter(str.isdigit).repeated())
        .map(lambda chars: int("".join(chars)))
    )
    | Just("0").map(int)
).map(IntegerLiteral)


identifier = (
    filt(lambda char: char.isalpha() or char == "_")
    .chain(filt(lambda char: char.isalnum() or char == "_").repeated())
    .map(lambda chars: "".join(chars))
).map(Identifier)

keyword = identifier.and_check(lambda ident: ident in Keyword).map(
    lambda char: Keyword(char)
)

basic = one_of("+-*/{}").map(lambda char: Basic(char))

string = (
    just('"')
    .ignore_then(filt(lambda char: char not in {"\n", '"'}).repeated())
    .then_ignore(just('"').require(LexError.UnterminatedStringLiteral))
    .map(lambda chars: "".join(chars))
).map(StringLiteral)

character = (
    just("'")
    .ignore_then(filt(lambda char: char != "'"))
    .then_ignore(just("'").require(LexError.UnexpectedCharacter))
).map(CharacterLiteral)

whitespace = just(" ").then(filter(str.isspace).repeated()).map(lambda _: Whitespace)

comment = (
    just("#")
    .ignore_then(filt(lambda char: char != "\n").repeated())
    .map(lambda chars: "".join(chars))
).map(Comment)

token = (
    integer | identifier | keyword | basic | string | character | comment | whitespace
)

tokenizer = token.repeated()
