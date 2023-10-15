union Result<Okay, Error> {
    ok: Okay
    err: Error

    def is_ok(&self) -> bool {
        when self {
            is Okay { return True }
            is Error { return False }
        }
    }

    def is_err(&self) -> bool {
        return !self.is_ok()
    }
}

protocol Display {
    def repr() -> String
}

struct Span(Display, Copy) {
    absolute: u32
    line: u32
    column: u32
}

enum PrimitiveKind { LeftBrace, RightBrace, Colon, Comma, }
enum KeywordKind { Union, Enum, Struct, Type }

enum IntegerBase { Bin, Dec, Hex, }
struct IntegerLiteral {
    value: u32
    base: IntegerBase
}

type TokenKind = PrimitiveKind | KeywordKind

struct Token {
    span: Span
    kind: TokenKind
}
