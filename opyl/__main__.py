import argparse

from opyl.compile import compile
from opyl.io import error
from opyl.io.file import File


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument("source_file")
    args = argparser.parse_args()

    read_result = File.open(args.source_file).and_then(File.read)

    if read_result.is_err():
        error.fatal(
            f"Failed to open source file '{args.source_file}'.",
        )

    text = read_result.unwrap()

    compile.compile(args.source_file, text)


if __name__ == "__main__":
    main()
