type ParseResult = Match | NoMatch | Error

struct Match {
    
}

struct NoMatch {}

struct Error {}

struct Arguments {
    count: u8

    def len() -> u8 {}
}

def main(args: Arguments) -> ExitCode {
    let mut foo: Foo = 5

    if args.len() == 0 {
        return ExitCode::Failure
    }

    when value {
        is Match {}
        is NoMatch {}
        is Error {}
        else {4+2}
    }

    print("Hello, World!")
}
