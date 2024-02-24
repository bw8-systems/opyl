import sys
from dataclasses import dataclass
import typing as t
import argparse
import pathlib


# TODO: If argparse.ArgumentParser.parse_args fails, it will print to stdout/sterr and then exit immediately.
# I would like to:
#   1. Control where the output is print to. This would simplify unit testing.
#   2. Maybe instead return file.IOError or a new error type, which is to be handled by the caller. This is more "functional".
#       - Will also help testing.
@dataclass
class CommandLineArguments:
    source_file: pathlib.Path

    @classmethod
    def parse_args(cls, args: list[str] | None = None) -> t.Self:
        if args is None:
            args = sys.argv[1:]

        argparser = argparse.ArgumentParser()
        argparser.add_argument("source_file")
        parsed_args = argparser.parse_args(args)

        return cls(source_file=pathlib.Path(parsed_args.source_file))
