import argparse
from pprint import pprint

from opyl.compile import lex
from opyl.compile import parse
from opyl.compile.error import format_error, report_lex_errors
from opyl.support.combinator import PR
from opyl.support.stream import Source
from opyl.io.file import File


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument("source_file")
    args = argparser.parse_args()

    text = (
        File.open(args.source_file).and_then(File.read).expect("File error occurred.")
    )

    source = Source(text, args.source_file)
    lex_result = lex.tokenize(text, args.source_file)
    report_lex_errors(lex_result.errors, source)
    tokens = lex_result.stream

    match parse.parse(tokens):
        case PR.Match(item):
            pprint(item)
        case PR.NoMatch:
            ...
        case PR.Error(err, span):
            fmt = format_error(err, span, source)
            print(fmt)


if __name__ == "__main__":
    main()
