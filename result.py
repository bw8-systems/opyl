from typing import TypeGuard, Self, Callable
import enum


class Result[Okay, Error]:
    def __init__(self):
        self._ok: Okay | None = None
        self._err: Error | None = None

    @classmethod
    def Ok(cls, ok: Okay) -> Self:
        self = cls()
        self._ok = ok

        assert self.invariant
        return self

    @classmethod
    def Err(cls, err: Error) -> Self:
        self = cls()
        self._err = err

        assert self.invariant
        return self

    @property
    def invariant(self) -> bool:
        return (self._ok is None and self._err is not None) or (
            self._err is None and self._ok is not None
        )

    def is_ok(self, ok: Okay | None) -> TypeGuard[Okay]:
        assert self.invariant
        return self._ok is not None

    def is_err(self, err: Error | None) -> TypeGuard[Error]:
        assert self.invariant
        return self._err is not None

    def unwrap(self) -> Okay:
        assert self.invariant
        if self.is_ok(self._ok):
            return self._ok
        raise ValueError

    def unwrap_err(self) -> Error:
        assert self.invariant
        if self.is_err(self._err):
            return self._err
        raise ValueError

    def and_[U](self, res: "Result[U, Error]") -> "Result[U, Error]":
        assert self.invariant
        if self.is_ok(self._ok):
            return res
        else:
            return Result[U, Error].Err(self.unwrap_err())

    def and_then[U](self, op: Callable[[], "Result[U, Error]"]) -> "Result[U, Error]":
        assert self.invariant
        if self.is_ok(self._ok):
            return op()
        return Result[U, Error].Err(self.unwrap_err())


class ParseError(enum.Enum):
    UnexpectedToken = enum.auto()
    UnexpectedEOF = enum.auto()


type ParseResult[T] = Result[T, ParseError]
