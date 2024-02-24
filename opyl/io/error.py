import typing as t

from opyl.io import file


def die(op: t.Callable[[], t.Any], exit_code: int = -1) -> t.NoReturn:
    op()
    exit(-1)


def fatal(
    message: str, file: t.TextIO = file.stderr, exit_code: int = -1
) -> t.NoReturn:
    die(lambda: print(message, file=file), exit_code=exit_code)
