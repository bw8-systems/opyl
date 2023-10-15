struct TextPosition {
    absolute: u32
    line: u32
    column: u32
}

struct Span {
    start: TextPosition
    end: TextPosition
}

enum PrimitiveKind {
    LeftBrace, RightBrace, EOF
}

enum KeywordKind {
    Struct, Enum, Union
}

struct DecLiteral {
    value: u32
}

struct BinLiteral {
    value: u32
}

struct HexLiteral {
    value: u32
}

union IntegerLiteral = DecLiteral | BinLiteral | HexLiteral

union TokenKind = PrimitiveKind | KeywordKind | IntegerLiteral

struct AnyToken {
    kind: TokenKind
    span: Span
}

struct ParametricToken<value TokenKind> {
    span: Span
}

union Token = AnyToken | ParametricToken

union Result<type Ok, type Error> = Ok | Error
enum ParseError { UnexpectedToken, UnexpectedEOF }
union ParseResult<T> = T | ParseError

def peek(&self) -> Option<TokenKind> {
    if self.index > self.tokens.len() {
        return None
    }

    when foo() {
        is None { return 5 }
        is Foo { return 4 }
    }

    return self.tokens[self.index]
}

def next() -> Token { ... }

def parse_token<const kind: TokenKind>() -> ParseResult<ParametricToken<TokenKind>> {
    let peeked: TokenKind = peek()
    if peeked != kind {
        return UnexpectedToken
    }

    return 
}
