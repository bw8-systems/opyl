import argparse
from pprint import pprint

from opyl.compile import lex
from opyl.compile import parse
from opyl.compile.error import format_error
from opyl.support.combinator import PR


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument("source_file")
    args = argparser.parse_args()

    with open(args.source_file) as f:
        source = f.read()

    stream = lex.tokenize(source).unwrap()[0]

    match parse.parse(stream):
        case PR.Match(item):
            pprint(item)
        case PR.NoMatch:
            ...
        case PR.Error(err, span):
            fmt = format_error(err, span, source)
            print(fmt)


if __name__ == "__main__":
    main()
