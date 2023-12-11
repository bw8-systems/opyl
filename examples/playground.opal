let mut foo: Type = 5
const NAME: u8 = 2

struct Span {
    foo: Foo
    bar: Bar
}

enum TokenKind {
    Basic,
    Keyword,
    Identifier,
    IntegerLiteral
}

union Token = u16 | str


def function(
    foo: Foo,
    bar: Bar,
) -> ReturnType {
    foo
}

trait Iterator {}

