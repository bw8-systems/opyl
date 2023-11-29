from pprint import pprint

from compile import parse

parser = parse.OpalParser(
    """for val in iter {}
    """
)

decl = parser.for_statement().parse()

pprint(decl)


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
