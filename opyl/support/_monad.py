from typing import Callable, Any
from dataclasses import dataclass
from abc import ABC, abstractmethod

type Predicate[T] = Callable[[T], bool]


class _Option[T](ABC):
    def and_[U](self, optb: "Option[U]") -> "Option[U]":
        if self.is_nil():
            return Nil
        return optb

    def and_then[U](self, func: Callable[[T], "Option[U]"]) -> "Option[U]":
        if self.is_nil():
            return Nil
        return func(self.unwrap())

    def expect(self, msg: str) -> T:
        try:
            return self.unwrap()
        except ValueError as e:
            e.add_note(msg)
            raise

    @abstractmethod
    def filter(self, pred: Predicate[T]) -> "Option[T]":
        ...

    def is_nil(self) -> bool:
        return self is Nil

    def is_some(self) -> bool:
        return not self.is_nil()

    def is_some_and(self, func: Predicate[T]) -> bool:
        return self.is_some() and func(self.unwrap())

    def map[U](self, func: Callable[[T], U]) -> "Option[U]":
        if self.is_nil():
            return Nil
        return Some(func(self.unwrap()))

    def map_or[U](self, default: U, func: Callable[[T], U]) -> U:
        if self.is_nil():
            return default
        return func(self.unwrap())

    def map_or_else[U](self, default: Callable[[], U], func: Callable[[T], U]) -> U:
        if self.is_nil():
            return default()
        return func(self.unwrap())

    def ok_or[E](self, err: E) -> "Result[T, E]":
        if self.is_nil():
            return Err(err)
        return Ok(self.unwrap())

    def ok_or_else[E](self, err: Callable[[], E]) -> "Result[T, E]":
        if self.is_some():
            return Ok(self.unwrap())
        return Err(err())

    @abstractmethod
    def or_(self, optb: "Option[T]") -> "Option[T]":
        ...

    @abstractmethod
    def or_else(self, func: Callable[[], "Option[T]"]) -> "Option[T]":
        ...

    @abstractmethod
    def unwrap(self) -> T:
        ...

    def unwrap_or(self, default: T) -> T:
        if self.is_nil():
            return default
        return self.unwrap()

    def unwrap_or_else(self, f: Callable[[], T]) -> T:
        if self.is_nil():
            return f()
        return self.unwrap()

    @abstractmethod
    def xor(self, optb: "Option[T]") -> "Option[T]":
        ...

    def zip[U](self, other: "Option[U]") -> "Option[tuple[T, U]]":
        if self.is_some() and other.is_some():
            return Some((self.unwrap(), other.unwrap()))
        return Nil

    def zip_with[
        U, R
    ](self, other: "Option[U]", func: Callable[[T, U], R]) -> "Option[R]":
        if self.is_some() and other.is_some():
            return Some(func(self.unwrap(), other.unwrap()))
        return Nil


@dataclass
class Some[T](_Option[T]):
    some: T

    def unwrap(self) -> T:
        return self.some

    def filter(self, pred: Predicate[T]) -> "Option[T]":
        return self

    def or_(self, optb: "Option[T]") -> "Option[T]":
        return self

    def or_else(self, func: Callable[[], "Option[T]"]) -> "Option[T]":
        return self

    def xor(self, optb: "Option[T]") -> "Option[T]":
        if optb.is_some():
            return Nil
        return self


class _Nil(_Option[Any]):
    def unwrap(self) -> Any:
        raise ValueError

    def filter[T](self, pred: Predicate[T]) -> "Option[T]":
        if self.is_nil():
            return Nil
        if pred(self.unwrap()):
            return self
        return Nil

    def or_[T](self, optb: "Option[T]") -> "Option[T]":
        return optb

    def or_else[T](self, func: Callable[[], "Option[T]"]) -> "Option[T]":
        return func()

    def xor[T](self, optb: "Option[T]") -> "Option[T]":
        if optb.is_nil():
            return optb
        return self


Nil = _Nil()

type Option[T] = Some[T] | _Nil


class _ResultContainer[TorE]:
    def is_ok(self) -> bool:
        return isinstance(self, Ok)

    def is_err(self) -> bool:
        return not self.is_ok()

    @abstractmethod
    def and_[U](self, res: "Result[U, E]") -> "Result[U, E]":
        ...

    def and_then[U](self, op: Callable[[], "Result[U, E]"]) -> "Result[U, E]":
        if self.is_ok():
            return op()
        return Err(self.unwrap_err())

    @abstractmethod
    def err(self) -> Option[E]:
        ...

    def expect(self, msg: str) -> T:
        try:
            return self.unwrap()
        except ValueError as e:
            e.add_note(msg)
            raise

    def expect_err(self, msg: str) -> E:
        try:
            return self.unwrap_err()
        except ValueError as e:
            e.add_note(msg)
            raise

    def is_err_and(self, pred: Predicate[E]) -> bool:
        return self.is_err() and pred(self.unwrap_err())

    def is_ok_and(self, pred: Predicate[T]) -> bool:
        return self.is_ok() and pred(self.unwrap())

    def map[U](self, op: Callable[[T], U]) -> "Result[U, E]":
        if self.is_err():
            return Err(self.unwrap_err())
        return Ok(op(self.unwrap()))

    def map_err[F](self, op: Callable[[E], F]) -> "Result[T, F]":
        if self.is_ok():
            return Ok(self.unwrap())
        return Err(op(self.unwrap_err()))

    def map_or[U](self, default: U, op: Callable[[T], U]) -> U:
        if self.is_err():
            return default
        return op(self.unwrap())

    def map_or_else[U](self, default: Callable[[E], U], op: Callable[[T], U]) -> U:
        if self.is_ok():
            return op(self.unwrap())
        return default(self.unwrap_err())

    @abstractmethod
    def ok(self) -> Option[T]:
        ...

    def or_[F](self, res: "Result[T, F]") -> "Result[T, F]":
        if self.is_err():
            return res
        return Ok(self.unwrap())

    def or_else[F](self, op: Callable[[E], "Result[T, F]"]) -> "Result[T, F]":
        if self.is_err():
            return op(self.unwrap_err())
        return Ok(self.unwrap())

    def unwrap(self) -> T:
        if self.is_ok():
            return self.ok().unwrap()
        raise ValueError

    def unwrap_err(self) -> E:
        if self.is_err():
            return self.err().unwrap()
        raise ValueError

    def unwrap_or(self, default: T) -> T:
        if self.is_ok():
            return self.unwrap()
        return default

    def unwrap_or_else(self, op: Callable[[E], T]) -> T:
        if self.is_ok():
            return self.unwrap()
        return op(self.unwrap_err())


@dataclass
class Ok[T](_ResultContainer[T]):
    _ok: T

    @abstractmethod
    def and_[U, E](self, res: "Result[U, E]") -> "Result[U, E]":
        return res


@dataclass
class Err[E](_ResultContainer[E]):
    _err: E

    @abstractmethod
    def and_[U](self, res: "Result[U, E]") -> "Result[U, E]":
        return Err(self.unwrap_err())


type Result[T, E] = Ok[T] | Err[E]
