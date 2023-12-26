type ParseResult = Match | NoMatch | Error

struct Arguments {
    count: u8

    def len() -> u8 {}
}

def main(args: Arguments) -> ExitCode {
    let mut foo: Foo =

    if args.len() == 0 {
        return ExitCode::Failure
    }

    when value {
        is Match {}
        is NoMatch {}
        is Type {}
    }
}
