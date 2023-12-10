#!python3

import sys
import argparse
import pathlib
from pprint import pprint

from compile import lex
from compile import lexemes
from compile import parse
from compile.positioning import Span
from compile.combinators import TokenStream
from compile.lexemes import PrimitiveKind as PK
from compile.lexemes import KeywordKind as KK
from compile.combinators import just, ident, lines, block
from compile.parse import expr, stmt


def main(input_path: str):
    source = pathlib.Path(input_path).read_text()
    tokens = lex.tokenize(source)

    parse.parse(tokens)
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
