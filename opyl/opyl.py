#!python3

import sys
import argparse
import pathlib

from compile import lex
from compile import parse


def main(input_path: str):
    source = pathlib.Path(input_path).read_text()
    parse.parse(source)
    # pprint(tree)


def _parse_args(argv: list[str]) -> str:
    argparser = argparse.ArgumentParser(
        prog="opyl",
        description="Compiler for the Opal programming language.",
    )

    argparser.add_argument("input_file")
    args = argparser.parse_args(argv)
    return args.input_file


if __name__ == "__main__":
    args = _parse_args(sys.argv[1:])
    main(args)
