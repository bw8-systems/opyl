import enum
import os
import typing as t
from collections.abc import Iterator

if t.TYPE_CHECKING:
    from _typeshed import OpenTextMode

from opyl.support.union import Result


class IOError(enum.Enum):
    FileNotFound = enum.auto()


type IOResult[T] = Result.Type[T, IOError]


class IOMode(enum.Enum):
    Read = enum.auto()
    Write = enum.auto()
    Append = enum.auto()
    ReadWrite = enum.auto()

    def to_mode(
        self,
    ) -> "OpenTextMode":
        match self:
            case IOMode.Read:
                return "r"
            case IOMode.Write:
                return "w"
            case IOMode.Append:
                return "w+"
            case IOMode.ReadWrite:
                return "r+"


type ReadFile = File[t.Literal[IOMode.Read]]
type WriteFile = File[t.Literal[IOMode.Write]]
type AppendFile = File[t.Literal[IOMode.Append]]
type ReadWriteFile = File[t.Literal[IOMode.ReadWrite]]

type WriteableFile = WriteFile | AppendFile | ReadWriteFile


class File[Mode: IOMode]:
    def __init__(self, path: os.PathLike[str], mode: IOMode):
        self.fd = open(path, mode.to_mode())

    def __del__(self):
        if hasattr(self, "fd"):
            self.fd.close()

    @staticmethod
    def open(path: os.PathLike[str]) -> "IOResult[ReadFile]":
        try:
            return Result.Ok(File(path, IOMode.Read))
        except FileNotFoundError:
            return Result.Err(IOError.FileNotFound)

    @staticmethod
    def create(path: os.PathLike[str]) -> "IOResult[WriteFile]":
        return Result.Ok(File(path, IOMode.Write))

    def read(self: ReadFile) -> "IOResult[str]":
        return Result.Ok(self.fd.read())

    def write(self: WriteableFile, data: str) -> "IOResult[None]":
        self.fd.write(data)
        return Result.Ok(None)

    def lines(self: ReadFile) -> Iterator[str]:
        for line in self.fd:
            yield line