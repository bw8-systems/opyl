import typing as t

from opyl.io import file
from opyl.console.color import colors


def die(op: t.Callable[[], t.Any], exit_code: int = -1) -> t.NoReturn:
    op()
    exit(exit_code)


def fatal(
    message: str, file: t.TextIO = file.stderr, exit_code: int = -1
) -> t.NoReturn:
    die(lambda: print(message, file=file), exit_code=exit_code)


def fatal_io_error(
    error: file.IOError, file: t.TextIO = file.stderr, exit_code: int = -1
) -> t.NoReturn:
    fatal(message=format_io_error(error), file=file, exit_code=exit_code)


def format_io_error(error: file.IOError) -> str:
    match error.value:
        case file.IOError.Kind.FileNotFound:
            return f"{colors.bold}{colors.red}io error:{colors.reset} input file {colors.bold}{colors.black}'{error.path}'{colors.reset} not found."
