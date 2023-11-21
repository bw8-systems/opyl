from pprint import pprint

from compile import parse


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

    return 0
}

"""
parser = parse.OpalParser(test_source)

parsed = parser.parse()
pprint(parsed)
# higher_order = parser.keyword(Keywords.Let) >> parser.whitespace() & parser.maybe(
#     parser.keyword(Keywords.Mut)
# )

# pprint(parser.parse())
# for item in higher_order.parse()
#     pprint(item)
