from opyl.compile import compile
from opyl.support.union import Result
from opyl.io import error

from opyl.driver.command_line import CommandLineArguments
from opyl.io.file import File


def main():
    args = CommandLineArguments.parse_args()

    match File.open(args.source_file).and_then(File.read):
        case Result.Err(err):
            error.fatal_io_error(err)
        case Result.Ok(text):
            compile.compile(args.source_file, text)


if __name__ == "__main__":
    main()
