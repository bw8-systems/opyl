import argparse
from pprint import pprint

from opyl.compile import lex
from opyl.compile import parse


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument("source_file")
    args = argparser.parse_args()

    with open(args.source_file) as f:
        source = f.read()

    stream = lex.tokenize(source).unwrap()[0]
    result = parse.parse(stream)
    pprint(result.unwrap()[0])


if __name__ == "__main__":
    main()
