import argparse
from pprint import pprint

from opyl.compile import lex
from opyl.compile import parse
from opyl.support.combinator import PR
from opyl.compile.error import format_error


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument("source_file")
    args = argparser.parse_args()

    with open(args.source_file) as f:
        text = f.read()

    stream = lex.tokenize(text, args.source_file).unwrap()[0]  # TODO: Don't unwrap

    match parse.parse(stream):
        case PR.Match(item):
            pprint(item)
        case PR.NoMatch:
            ...
        case PR.Error(err, pos):
            fmt = format_error(err, pos)
            print(fmt)


if __name__ == "__main__":
    main()
