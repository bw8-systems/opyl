from opyl.compile import lex
from opyl.compile import parse

source = """
let foo: Foo = 5

union Token = Primitive | Keyword {
    def foo() {}
    def bar() {}
    def baz() {}
}

struct TextPosition {
    absolute: u32
    line: u32
    column: u32
}

struct Span {
    start: TextPosition
    stop: TextPosition
}
"""

tokens = lex.tokenize(source)
decls = parser.parse(tokens)

print(f"Tokens: {len(tokens)}")
print(f"Decls: {len(decls)}")
