from compile import lex
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

var_decl = " "
parse.parse(lex.tokenize(var_decl))
