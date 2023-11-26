from pprint import pprint

from compile import parse
from compile import combinators as comb
from compile import lex
from compile import lexemes
from compile.positioning import Stream

opal_fibonacci = """
union Option[T] = T | None

trait Iterator[T] {
    mem next() -> Option[T]
}

class Range(Iterator[u32]) {
    start: u32
    stop: u32
    current: u32

    pub def new(start: u32, stop: u32) -> Range {
        return Range(
            start=start,
            stop=stop,
            current=start,
        )
    }

    pub mem next() -> Option[T] {
        if (self.current < self.stop) {
            self.current += 1
            return self.current - 1
        }

        return None
    }
}

def fibonacci(n: u32) -> u32 {
    if (n == 0) {
        return 1
    }

    if (n == 1) {
        return 1
    }

    return fibonacci(n - 1) + fibonacci(n - 2)
}

fn main() {
    for val in Range::new(start=0, stop=10) {
        let fib: u32 = fibonacci(val)
        print(fib)
    }
}
"""

test_source = """
let mut foo: Foo = bar
const FOO: Foo = baz

struct Range {
    start: u8
    stop: u8
}

enum Color {
    Red, Green, Blue
}

enum Monty {
    Foo,
    Bar,
    Baz,
}

union Enums = Color | Monty

def empty() {}

trait Iterable {
    def next()
}

union WithMethods = Range | u8 {
    def hella() {}
}

def main(foo: Foo, bar: mut Bar, anon baz: Baz) {
    let local: u32 = a

    if expr {
        other
    } else {
        another
    }

    for idx in range {
        stmt

        continue
    }

    while expr {
        lmao
        break
    }

    when union_value {
        is ThisType {
            some_expr_stmt
        }
        is ThatType {}
    }

    when union_value {
        is ThisType {
            some_expr_stmt
        }
        is ThatType {}
    }

    when arbitrary_value as av {
        is ThisType {}
        is ThatType {}
        else { bitchin }
    }


    return 0
}
"""
# parser = parse.OpalParser(test_source)

# parsed = parser.parse()
# pprint(parsed)
# assert len(parsed) == 10
# higher_order = parser.keyword(Keywords.Let) >> parser.whitespace() & parser.maybe(
#     parser.keyword(Keywords.Mut)
# )

# pprint(parser.parse())
# for item in higher_order.parse()
#     pprint(item)

# stream = Stream(
#     list(
#         filter(
#             lambda token: not isinstance(token, lexemes.Whitespace),
#             lex.tokenize("mut"),
#         )
#     )
# )

# parser = parse.OpalParser("def")
# print(parser.maybe(parser.keyword(lexemes.KeywordKind.Mut)).parse())

tokens = Stream(
    list(
        filter(
            lambda token: not isinstance(token, lexemes.Whitespace),
            lex.tokenize("def foo 1 +"),
        )
    )
)

value = (
    # ~comb.KeywordTerminal(tokens, lexemes.KeywordKind.Def)
    comb.IdentifierTerminal(tokens) & ~comb.IntegerLiteralTerminal(tokens)
).parse()


# pprint(parse.OpalParser("let foo: Foo = 5\n").parse())
# nodes = (
#     comb.KeywordTerminal(stream, lexemes.KeywordKind.Def)
#     & comb.IdentifierTerminal(stream)
#     & comb.PrimitiveTerminal(stream, terminal=lexemes.PrimitiveKind.LeftParenthesis)
#     & comb.PrimitiveTerminal(stream, terminal=lexemes.PrimitiveKind.RightParenthesis)
#     & comb.PrimitiveTerminal(stream, terminal=lexemes.PrimitiveKind.LeftBrace)
#     & comb.PrimitiveTerminal(stream, terminal=lexemes.PrimitiveKind.RightBrace)
# ).parse()

# for node in nodes:
#     pprint(node)

# print(comb.IdentifierTerminal(Stream(lex.tokenize("foo"))).parse())
# print(comb.IntegerLiteralTerminal(Stream(lex.tokenize("4"))).parse())
# print(
#     comb.PrimitiveTerminal(
#         Stream(lex.tokenize("+")), lexemes.PrimitiveKind.Plus
#     ).parse()
# )
