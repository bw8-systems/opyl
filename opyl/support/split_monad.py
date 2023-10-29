from typing import Callable, NoReturn, Any
from abc import ABC, abstractmethod
from dataclasses import dataclass

type Predicate[T] = Callable[[T], bool]
type Result[Ok, Err: Exception] = Okay[Ok, Err] | Error[Ok, Err]
type Option[T] = Some[T] | Nil[T]


class _Option(ABC):
    def is_nil(self) -> bool:
        return isinstance(self, Nil)

    def is_some(self) -> bool:
        return not self.is_nil()


class Nil[T](_Option):
    def unwrap(self) -> T:
        raise ValueError

    def __and__[U](self, optb: Option[U]) -> Option[U]:
        return Nil()

    def and_then[U](self, fn: Callable[[T], Option[U]]) -> Option[U]:
        return Nil()

    def filter(self, pred: Predicate[T]) -> Option[T]:
        return Nil()

    def is_some_and(self, fn: Predicate[T]) -> bool:
        return False

    def map[U](self, fn: Callable[[T], U]) -> Option[U]:
        return Nil()

    def map_or[U](self, default: U, fn: Callable[[T], U]) -> U:
        return default

    def map_or_else[U](self, default: Callable[[], U], fn: Callable[[T], U]) -> U:
        return default()

    def ok_or[E: Exception](self, err: E) -> Result[T, E]:
        return Error(err)

    def zip[U](self, other: Option[U]) -> Option[tuple[T, U]]:
        return Nil()


@dataclass(frozen=True, unsafe_hash=True)
class Some[T](_Option):
    some: T

    def unwrap(self) -> T:
        return self.some

    def __and__[U](self, optb: Option[U]) -> Option[U]:
        return optb

    def and_then[U](self, fn: Callable[[T], Option[U]]) -> Option[U]:
        return fn(self.unwrap())

    def is_some_and(self, fn: Predicate[T]) -> bool:
        return self.is_some() and fn(self.unwrap())

    def map[U](self, fn: Callable[[T], U]) -> Option[U]:
        return Some(fn(self.unwrap()))

    def map_or[U](self, default: U, fn: Callable[[T], U]) -> U:
        return fn(self.unwrap())

    def map_or_else[U](self, default: Callable[[], U], fn: Callable[[T], U]) -> U:
        return fn(self.unwrap())

    def ok_or[E: Exception](self, err: E) -> Result[T, E]:
        return Okay(self.unwrap())

    def zip[U](self, other: Option[U]) -> Option[tuple[T, U]]:
        if other.is_some():
            return Some((self.unwrap(), other.unwrap()))
        return Nil()


class _Result[Ok, Err: Exception](ABC):
    @abstractmethod
    def is_ok(self) -> bool:
        ...

    def is_err(self) -> bool:
        return not self.is_ok()

    def is_ok_and(self, pred: Predicate[Ok]) -> bool:
        return self.is_ok() and pred(self.unwrap())

    def is_err_and(self, pred: Predicate[Err]) -> bool:
        return self.is_err() and pred(self.unwrap_err())

    @abstractmethod
    def unwrap(self) -> Ok:
        ...

    @abstractmethod
    def unwrap_err(self) -> Err:
        ...


@dataclass(frozen=True, unsafe_hash=True)
class Okay[Ok, Err: Exception](_Result[Ok, Err]):
    _ok: Ok

    def ok(self) -> Option[Ok]:
        return Some(self.unwrap())

    def is_ok(self) -> bool:
        return True

    def unwrap(self) -> Ok:
        return self._ok

    def unwrap_err(self) -> Err:
        raise ValueError

    def __or__[F: Exception](self, obj: Result[Ok, F]) -> Result[Ok, F]:
        return Okay(self._ok)

    def or_else(self, fn: Callable[[], Result[Ok, Err]]) -> Ok:
        return self._ok

    def or_raise(self, exc: Exception | None = None) -> Ok:
        return self._ok

    def map[U](self, fn: Callable[[Ok], U]) -> Result[U, Err]:
        return Okay(fn(self.unwrap()))

    def map_or[U](self, default: U, fn: Callable[[Ok], U]) -> U:
        return fn(self.unwrap())

    def map_or_else[U](self, default: Callable[[Err], U], fn: Callable[[Ok], U]) -> U:
        return fn(self.unwrap())

    def __and__[U](self, res: Result[U, Err]) -> Result[U, Err]:
        return res

    def and_then[U](self, func: Callable[[Ok], Result[U, Err]]) -> Result[U, Err]:
        return func(self._ok)

    def exit(self, ok: Callable[[], Any], err: Callable[[], Any]) -> Result[Ok, Err]:
        ok()
        return self


@dataclass(frozen=True, unsafe_hash=True)
class Error[Ok, Err: Exception](_Result[Ok, Err]):
    _err: Err

    def ok(self) -> Option[Ok]:
        return Nil()

    def is_ok(self) -> bool:
        return False

    def unwrap(self) -> Ok:
        raise self._err

    def unwrap_err(self) -> Err:
        return self._err

    def __or__[F](self, obj: Result[Ok, F]) -> Result[Ok, F]:
        return obj

    def or_else[U](self, fn: Callable[[], U]) -> U:
        return fn()

    def or_raise(self, exc: Exception | None = None) -> NoReturn:
        if exc is not None:
            raise exc from self._err
        raise self._err

    def map[U: Exception](self, fn: Callable[[Ok], U]) -> Result[U, Err]:
        return Error(self._err)

    def map_or[U](self, default: U, fn: Callable[[Ok], U]) -> U:
        return default

    def map_or_else[U](self, default: Callable[[Err], U], fn: Callable[[Ok], U]) -> U:
        return default(self._err)

    def __and__[U](self, res: Result[U, Err]) -> Result[U, Err]:
        return Error(self._err)

    def and_then[U](self, func: Callable[[Ok], Result[U, Err]]) -> Result[U, Err]:
        return Error(self._err)

    def exit(self, ok: Callable[[], Any], err: Callable[[], Any]) -> Result[Ok, Err]:
        err()
        return self
