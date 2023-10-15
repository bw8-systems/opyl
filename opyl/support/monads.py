from typing import TypeGuard, Self, Callable

type Predicate[T] = Callable[[T], bool]


class Option[Some]:
    def __init__(self):
        self._some: Some | None = None

    @classmethod
    def Just(cls, some: Some) -> Self:
        self = cls()
        self._some = some
        return self

    @classmethod
    def Nil(cls) -> Self:
        return cls()

    def and_[U](self, optb: "Option[U]") -> "Option[U]":
        if self.is_nil():
            return Option[U].Nil()
        return optb

    def and_then[U](self, f: Callable[[Some], "Option[U]"]) -> "Option[U]":
        if self.is_nil():
            return Option[U].Nil()
        return f(self.unwrap())

    def expect(self, msg: str) -> Some:
        try:
            return self.unwrap()
        except ValueError as e:
            e.add_note(msg)
            raise

    def filter(self, pred: Predicate[Some]) -> "Option[Some]":
        if self.is_nil():
            return Option[Some].Nil()
        if pred(self.unwrap()):
            return self
        return Option[Some].Nil()

    def is_nil(self) -> bool:
        return self._some is None

    def is_some(self) -> bool:
        return not self.is_nil()

    def is_some_and(self, f: Predicate[Some]) -> bool:
        return self.is_some() and f(self.unwrap())

    def map[U](self, f: Callable[[Some], U]) -> "Option[U]":
        if self._some is None:
            return Option[U].Nil()
        return Option[U].Just(f(self.unwrap()))

    def map_or[U](self, default: U, f: Callable[[Some], U]) -> U:
        if self._some is None:
            return default
        return f(self.unwrap())

    def map_or_else[U](self, default: Callable[[], U], f: Callable[[Some], U]) -> U:
        if self._some is None:
            return default()
        return f(self.unwrap())

    def ok_or[Error](self, err: Error) -> "Result[Some, Error]":
        if self._some is None:
            return Result[Some, Error].Err(err)
        return Result[Some, Error].Ok(self.unwrap())

    def ok_or_else[Error](self, err: Callable[[], Error]) -> "Result[Some, Error]":
        if self._some is not None:
            return Result[Some, Error].Ok(self.unwrap())
        return Result[Some, Error].Err(err())

    def or_(self, optb: "Option[Some]") -> "Option[Some]":
        if self._some is None:
            return optb
        return self

    def or_else(self, f: Callable[[], "Option[Some]"]) -> "Option[Some]":
        if self._some is None:
            return f()
        return self

    def unwrap(self) -> Some:
        if self._some is not None:
            return self._some
        raise ValueError

    def unwrap_or(self, default: Some) -> Some:
        if self._some is None:
            return default
        return self.unwrap()

    def unwrap_or_else(self, f: Callable[[], Some]) -> Some:
        if self._some is None:
            return f()
        return self.unwrap()

    def unzip[U](self: "Option[tuple[Some, U]]") -> tuple["Option[Some]", "Option[U]"]:
        if self.is_some():
            left, right = self.unwrap()
            return (Option[Some].Just(left), Option[U].Just(right))
        return (Option[Some].Nil(), Option[U].Nil())

    def xor(self, optb: "Option[Some]") -> "Option[Some]":
        if self.is_some() and optb.is_some():
            return Option[Some].Nil()
        if self.is_nil() and optb.is_nil():
            return Option[Some].Nil()
        return self

    def zip[U](self, other: "Option[U]") -> "Option[tuple[Some, U]]":
        if self.is_some() and other.is_some():
            return Option[tuple[Some, U]].Just((self.unwrap(), other.unwrap()))
        return Option[tuple[Some, U]].Nil()

    def zip_with[
        U, R
    ](self, other: "Option[U]", f: Callable[[Some, U], R]) -> "Option[R]":
        if self.is_some() and other.is_some():
            return Option[R].Just(f(self.unwrap(), other.unwrap()))
        return Option[R].Nil()


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

    def _is_ok(self, ok: Okay | None) -> TypeGuard[Okay]:
        assert self.invariant
        return self._ok is not None

    def _is_err(self, err: Error | None) -> TypeGuard[Error]:
        assert self.invariant
        return self._err is not None

    def and_[U](self, res: "Result[U, Error]") -> "Result[U, Error]":
        assert self.invariant
        if self._is_ok(self._ok):
            return res
        else:
            return Result[U, Error].Err(self.unwrap_err())

    def and_then[U](self, op: Callable[[], "Result[U, Error]"]) -> "Result[U, Error]":
        assert self.invariant
        if self._is_ok(self._ok):
            return op()
        return Result[U, Error].Err(self.unwrap_err())

    def err(self) -> Option[Error]:
        assert self.invariant
        if self._is_err(self._err):
            return Option[Error].Just(self._err)
        return Option[Error].Nil()

    def expect(self, msg: str) -> Okay:
        assert self.invariant
        try:
            return self.unwrap()
        except ValueError as e:
            e.add_note(msg)
            raise

    def expect_err(self, msg: str) -> Error:
        assert self.invariant
        try:
            return self.unwrap_err()
        except ValueError as e:
            e.add_note(msg)
            raise

    def flatten(self: "Result[Result[Okay, Error], Error]") -> "Result[Okay, Error]":
        assert self.invariant
        if self._is_ok(self._ok):
            return self._ok
        return Result[Okay, Error].Err(self.unwrap_err())

    def is_err(self) -> bool:
        assert self.invariant
        return self._is_err(self._err)

    def is_err_and(self, pred: Predicate[Error]) -> bool:
        assert self.invariant
        return self.is_err() and pred(self.unwrap_err())

    def is_ok(self) -> bool:
        assert self.invariant
        return self._is_ok(self._ok)

    def is_ok_and(self, pred: Predicate[Okay]) -> bool:
        assert self.invariant
        return self.is_ok() and pred(self.unwrap())

    def map[U](self, op: Callable[[Okay], U]) -> "Result[U, Error]":
        assert self.invariant
        if self.is_err():
            return Result[U, Error].Err(self.unwrap_err())
        return Result[U, Error].Ok(op(self.unwrap()))

    def map_err[F](self, op: Callable[[Error], F]) -> "Result[Okay, F]":
        assert self.invariant
        if self.is_ok():
            return Result[Okay, F].Ok(self.unwrap())
        return Result[Okay, F].Err(op(self.unwrap_err()))

    def map_or[U](self, default: U, op: Callable[[Okay], U]) -> U:
        assert self.invariant
        if self.is_err():
            return default
        return op(self.unwrap())

    def map_or_else[
        U
    ](self, default: Callable[[Error], U], op: Callable[[Okay], U]) -> U:
        assert self.invariant
        if self.is_ok():
            return op(self.unwrap())
        return default(self.unwrap_err())

    def ok(self) -> Option[Okay]:
        assert self.invariant
        if self.is_ok():
            return Option[Okay].Just(self.unwrap())
        return Option[Okay].Nil()

    def or_[F](self, res: "Result[Okay, F]") -> "Result[Okay, F]":
        if self.is_err():
            return res
        return Result[Okay, F].Ok(self.unwrap())

    def or_else[F](self, op: Callable[[Error], "Result[Okay, F]"]) -> "Result[Okay, F]":
        if self.is_err():
            return op(self.unwrap_err())
        return Result[Okay, F].Ok(self.unwrap())

    def unwrap(self) -> Okay:
        assert self.invariant
        if self._is_ok(self._ok):
            return self._ok
        raise ValueError

    def unwrap_err(self) -> Error:
        assert self.invariant
        if self._is_err(self._err):
            return self._err
        raise ValueError

    def unwrap_or(self, default: Okay) -> Okay:
        if self.is_ok():
            return self.unwrap()
        return default

    def unwrap_or_else(self, op: Callable[[Error], Okay]) -> Okay:
        if self.is_ok():
            return self.unwrap()
        return op(self.unwrap_err())
